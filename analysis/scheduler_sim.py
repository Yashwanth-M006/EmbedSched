"""
analysis/scheduler_sim.py

Discrete-event scheduler simulation over one hyperperiod.

Purpose:
    Validate RTA results by running an actual preemptive fixed-priority
    scheduler simulation. Produces:
      - Per-task Gantt intervals (start, end) for the Gantt chart
      - Per-task actual start times across all activations (for jitter analysis)
      - Deadline miss events

Algorithm:
    Event-driven simulation:
    1. Compute hyperperiod H = LCM of all task periods.
    2. Pre-generate all task release events in [0, H).
    3. Use a priority queue (max-heap by priority) as the ready queue.
    4. Simulate time-step by time-step, advancing to the next event.
    5. At each event: insert newly released tasks, select highest-priority
       ready task, run it to completion or next preemption event.

Simulation resolution:
    Time is tracked as rational microseconds (float). Resolution is bounded
    by the smallest WCET in the task set — typically sub-microsecond precision
    is not needed since we work with datasheet-derived WCETs.

Hyperperiod cap:
    If the computed hyperperiod exceeds MAX_HYPERPERIOD_US, we cap it and
    warn — otherwise simulation of e.g. tasks with periods 1ms and 997ms
    would run for 997ms simulated time which could be slow.
"""

import math
import heapq
import bisect
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from models.autosar_task import AutosarTask, CoreConfig

MAX_HYPERPERIOD_US = 2_000_000         # 2,000 ms (2 seconds) — upper bound on simulated hyperperiod
MAX_SIMULATION_ACTIVATIONS = 10_000    # Cap simulation if total activations exceed 10,000


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class GanttInterval:
    """A single execution slot on the Gantt chart."""
    __slots__ = ['task_name', 'core_id', 'start_us', 'end_us', 'preempted']

    def __init__(self, task_name: str, core_id: int,
                 start_us: float, end_us: float, preempted: bool = False):
        self.task_name = task_name
        self.core_id   = core_id
        self.start_us  = start_us
        self.end_us    = end_us
        self.preempted = preempted   # True = this slot ended due to preemption


class DeadlineMiss:
    """Records a deadline miss event."""
    __slots__ = ['task_name', 'activation_time_us', 'deadline_us',
                 'actual_finish_us', 'miss_by_us']

    def __init__(self, task_name: str, activation_time_us: float,
                 deadline_us: float, actual_finish_us: float):
        self.task_name          = task_name
        self.activation_time_us = activation_time_us
        self.deadline_us        = deadline_us
        self.actual_finish_us   = actual_finish_us
        self.miss_by_us         = actual_finish_us - deadline_us


class SimulationResult:
    def __init__(self):
        self.gantt:           List[GanttInterval]     = []
        self.deadline_misses: List[DeadlineMiss]      = []
        # {task_name: [actual_start_us per activation]}
        self.start_times:     Dict[str, List[float]]  = defaultdict(list)
        self.hyperperiod_us:  float                   = 0.0
        self.capped:          bool                    = False   # True if HP was capped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate_schedule(
    tasks: List[AutosarTask],
    stochastic: bool = False,
    cores: Dict[int, CoreConfig] = None
) -> SimulationResult:
    """
    Simulate the task set over one hyperperiod.

    Only tasks with period_us > 0 and wcet_us > 0 are simulated.
    Returns a SimulationResult with Gantt intervals, deadline misses, and
    per-task start-time lists (for jitter analysis).
    """
    result = SimulationResult()

    valid_tasks = [t for t in tasks if t.period_us > 0 and t.wcet_us > 0]
    if not valid_tasks:
        return result

    # Group by core
    core_tasks_map: Dict[int, List[AutosarTask]] = {}
    for t in valid_tasks:
        core_tasks_map.setdefault(t.core_id, []).append(t)

    # Compute global system hyperperiod and simulation length across all tasks
    true_hp, global_sim_len, capped = _hyperperiod(valid_tasks)
    result.hyperperiod_us = true_hp
    result.capped = capped

    # Simulate every core for the SAME global simulation length
    for core_id, core_tasks in sorted(core_tasks_map.items()):
        _simulate_core(core_id, core_tasks, global_sim_len, result, stochastic, cores)

    return result


# ---------------------------------------------------------------------------
# Per-core simulation
# ---------------------------------------------------------------------------

def _simulate_core(
    core_id: int,
    tasks: List[AutosarTask],
    hyperperiod: float,
    result: SimulationResult,
    stochastic: bool = False,
    cores: Dict[int, CoreConfig] = None,
) -> None:
    """
    Simulate one core using a greedy preemptive fixed-priority or EDF scheduler.
    Note: Cross-core channel latencies are modeled as bounded blocking in RTA;
    local core simulation timelines execute without simulating active cross-core IPC stalls.

    Ready queue: max-heap keyed by (-priority, release_time) so that
    equal-priority tasks are FIFO by release order.
    """
    import random

    if cores and core_id in cores:
        is_edf = (cores[core_id].algorithm == "EDF")
    else:
        # Fallback only when core config is omitted: true EDF tasks lack fixed priorities
        is_edf = any(t.priority is None for t in tasks)

    # Generate all release events in [0, hyperperiod)
    # Each event: (release_time, deadline_abs, remaining_wcet, task)
    all_releases: List[Tuple[float, float, float, AutosarTask]] = []
    for t in tasks:
        k = 0
        while True:
            rel = float(t.period_us * k)
            if rel >= hyperperiod:
                break
                
            deadline_abs = rel + t.deadline_us
            
            # Stochastic execution time: 85% to 100% of WCET
            actual_wcet = t.wcet_us
            if stochastic:
                actual_wcet = actual_wcet * random.uniform(0.85, 1.0)
                
            all_releases.append((rel, deadline_abs, actual_wcet, t))
            k += 1

    # Sort releases by time
    all_releases.sort(key=lambda x: x[0])

    # Ready queue: items are (prio_key, release_time, remaining, deadline_abs, task)
    ready_queue: List[Tuple] = []
    release_idx = 0
    now = 0.0
    started_activations = set()

    while now < hyperperiod:
        # Drain all releases that have arrived by `now`
        while release_idx < len(all_releases) and all_releases[release_idx][0] <= now + 1e-9:
            rel, dl, wcet, t = all_releases[release_idx]
            prio_key = dl if is_edf else (t.priority if t.priority is not None else 255)
            heapq.heappush(ready_queue, (prio_key, rel, wcet, dl, t))
            release_idx += 1

        if not ready_queue:
            # No tasks ready — jump to the next release
            if release_idx < len(all_releases):
                now = all_releases[release_idx][0]
            else:
                break
            continue

        # Pick highest-priority ready task (lowest integer value / earliest deadline)
        prio_key, rel_t, remaining, dl_abs, task = heapq.heappop(ready_queue)

        # Record this activation's start time (first slice only)
        activation_key = (task.name, rel_t)
        if activation_key not in started_activations:
            started_activations.add(activation_key)
            result.start_times[task.name].append(now)

        # Determine how far we can run before the next higher-priority release
        next_hp_release = _next_release_before(
            all_releases, release_idx, prio_key, now, hyperperiod, is_edf
        )

        available = next_hp_release - now if next_hp_release is not None else (hyperperiod - now)
        run_time  = min(remaining, available)

        if run_time <= 0:
            # Cannot run at all — re-queue and advance to next event
            heapq.heappush(ready_queue, (prio_key, rel_t, remaining, dl_abs, task))
            if release_idx < len(all_releases):
                now = all_releases[release_idx][0]
            else:
                break
            continue

        # Execute for run_time µs
        slot_start = now
        slot_end   = now + run_time
        new_remaining = remaining - run_time

        preempted = new_remaining > 1e-9   # still has work left → was preempted
        result.gantt.append(GanttInterval(
            task_name=task.name,
            core_id=core_id,
            start_us=slot_start,
            end_us=slot_end,
            preempted=preempted,
        ))

        now = slot_end

        if preempted:
            # Put task back into ready queue with reduced remaining time
            heapq.heappush(ready_queue, (prio_key, rel_t, new_remaining, dl_abs, task))
        else:
            # Task completed — check deadline
            if slot_end > dl_abs + 1e-9:
                result.deadline_misses.append(DeadlineMiss(
                    task_name=task.name,
                    activation_time_us=rel_t,
                    deadline_us=dl_abs,
                    actual_finish_us=slot_end,
                ))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hyperperiod(tasks: List[AutosarTask]) -> Tuple[float, float, bool]:
    """Compute LCM of all task periods. Returns (hp_us, sim_len_us, was_capped)."""
    periods_us = [int(round(t.period_us)) for t in tasks if t.period_us > 0]
    if not periods_us:
        return 1000.0, 1000.0, False

    hp = periods_us[0]
    for p in periods_us[1:]:
        hp = hp * p // math.gcd(hp, p)

    # Check total task activations across the computed hyperperiod
    total_activations = sum(hp // p for p in periods_us) if hp > 0 else 0

    if hp > MAX_HYPERPERIOD_US or total_activations > MAX_SIMULATION_ACTIVATIONS:
        # Cap simulation to representative 30 ms window
        sim_len = 30_000.0
        return float(hp), sim_len, True

    return float(hp), float(hp), False


def _next_release_before(
    releases: List[Tuple],
    from_idx: int,
    current_prio_key: float,
    now: float,
    hyperperiod: float,
    is_edf: bool = False,
) -> Optional[float]:
    """
    Find the earliest release time > now of a task with higher priority (or earlier deadline).
    Uses binary search to skip past releases, then scans forward.
    Returns None if no such release exists before hyperperiod.
    """
    start_idx = max(from_idx, bisect.bisect_right(releases, now + 1e-9, key=lambda x: x[0]))
    for i in range(start_idx, len(releases)):
        rel_t, dl, _, task = releases[i]
        key = dl if is_edf else (task.priority if task.priority is not None else 255)
        if key < current_prio_key:
            return rel_t
    return None
