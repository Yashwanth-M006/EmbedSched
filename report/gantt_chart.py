"""
report/gantt_chart.py

ASCII Gantt chart for the AUTOSAR scheduler simulation results.

Renders one timeline per core over the simulated hyperperiod.
Each task gets a unique single-character symbol. Preemption events
are shown as '>' at the interruption point.

Example output (80-char terminal, HP=4000µs):

  CORE 0  |  Hyperperiod: 4000 µs  (scale: 50 µs/char)
  ─────────────────────────────────────────────────────────────────────────────────
  Task_SensorRead  [S] ████░░░░████░░░░████░░░░████░░░░████░░░░████░░░░████░░░░
  Task_MotorCtrl   [M] ░░░░████░░░░████░░░░████░░░░████░░░░████░░░░████░░░░████
  Task_Logger      [L] ░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░
  Timeline (µs)        0    500   1000  1500  2000  2500  3000  3500  4000

Legend: █ = executing   ░ = idle   > = preempted
"""

import math
from typing import List, Dict, Optional
from collections import defaultdict
from analysis.scheduler_sim import SimulationResult, GanttInterval

# Terminal width for the chart body (not including the left label column)
CHART_WIDTH   = 64
LABEL_WIDTH   = 20
EXEC_CHAR     = '█'
IDLE_CHAR     = '░'
PREEMPT_CHAR  = '>'

# Palette of single-char symbols for tasks (up to 20 tasks)
TASK_SYMBOLS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'


def render_gantt_chart(sim: SimulationResult) -> str:
    """
    Render an ASCII Gantt chart and return it as a multi-line string.
    """
    if not sim.gantt:
        return "  [Gantt chart: no simulation data]\n"

    lines: List[str] = []
    hp = sim.hyperperiod_us
    if hp <= 0:
        return "  [Gantt chart: hyperperiod is zero]\n"

    is_representative = sim.capped or hp > 1_000_000.0
    display_len_us = 30000.0 if is_representative else hp
    scale_us_per_char = display_len_us / CHART_WIDTH   # µs per character cell

    # Collect tasks per core
    tasks_by_core: Dict[int, List[str]] = defaultdict(list)
    for interval in sim.gantt:
        if interval.task_name not in tasks_by_core[interval.core_id]:
            tasks_by_core[interval.core_id].append(interval.task_name)

    # Assign symbols to tasks (global)
    all_tasks: List[str] = []
    for core_tasks in tasks_by_core.values():
        for t in core_tasks:
            if t not in all_tasks:
                all_tasks.append(t)
    sym_map: Dict[str, str] = {
        t: TASK_SYMBOLS[i % len(TASK_SYMBOLS)]
        for i, t in enumerate(all_tasks)
    }

    for core_id in sorted(tasks_by_core.keys()):
        lines.append("")
        if is_representative:
            lines.append(
                f"  CORE {core_id}  |  Representative Window (First {int(display_len_us//1000)}ms)  "
                f"(scale: {scale_us_per_char:.1f} µs/char)"
            )
            lines.append(
                f"  NOTE: Full simulation disabled due to hyperperiod explosion ({int(hp//1000):,}ms). "
                f"Showing representative {int(display_len_us//1000)}ms window only."
            )
        else:
            lines.append(
                f"  CORE {core_id}  |  Hyperperiod: {hp:.0f} µs  "
                f"(scale: {scale_us_per_char:.1f} µs/char)"
            )
        lines.append("  " + "─" * (LABEL_WIDTH + CHART_WIDTH + 4))

        core_task_names = tasks_by_core[core_id]

        # Build interval lookup: {task_name: [GanttInterval]}
        intervals_by_task: Dict[str, List[GanttInterval]] = defaultdict(list)
        for iv in sim.gantt:
            if iv.core_id == core_id:
                intervals_by_task[iv.task_name].append(iv)

        for task_name in core_task_names:
            sym   = sym_map.get(task_name, '?')
            label = f"{task_name[:LABEL_WIDTH-4]:<{LABEL_WIDTH-4}} [{sym}]"
            
            # Find missed absolute deadlines for this task
            misses = [dm.deadline_us for dm in sim.deadline_misses if dm.task_name == task_name]
            
            row   = _build_row(
                task_name,
                intervals_by_task[task_name],
                display_len_us,
                CHART_WIDTH,
                scale_us_per_char,
                sym,
                misses
            )
            lines.append(f"  {label} {row}")

        # Timeline ruler
        lines.append(_build_ruler(display_len_us, CHART_WIDTH, scale_us_per_char, LABEL_WIDTH))

    # Legend
    lines.append("")
    lines.append(f"  Legend:  {EXEC_CHAR} = executing   {IDLE_CHAR} = idle   {PREEMPT_CHAR} = preemption point")

    # Symbols legend
    lines.append("")
    lines.append("  Task symbols:")
    for task_name, sym in sym_map.items():
        lines.append(f"    [{sym}]  {task_name}")

    # Deadline misses
    if sim.deadline_misses:
        lines.append("")
        lines.append(f"  DEADLINE MISSES ({len(sim.deadline_misses)} events):")
        for dm in sim.deadline_misses[:10]:   # show first 10
            lines.append(
                f"    [MISS]  {dm.task_name:<20} "
                f"released @ {dm.activation_time_us:.0f} µs,  "
                f"deadline @ {dm.deadline_us:.0f} µs,  "
                f"finished @ {dm.actual_finish_us:.2f} µs  "
                f"(+{dm.miss_by_us:.2f} µs late)"
            )
        if len(sim.deadline_misses) > 10:
            lines.append(f"    ... and {len(sim.deadline_misses) - 10} more.")

    return "\n".join(lines) + "\n"


def render_jitter_table(sim: SimulationResult, tasks) -> str:
    """
    Render per-task jitter table showing start-time variation.

    Jitter = max(start_times) - min(start_times) relative to ideal periodic start.
    Ideal start for activation k of task with period T = k * T.
    """
    if not sim.start_times:
        return "  [Jitter: no simulation data]\n"

    lines: List[str] = []
    lines.append("")
    lines.append("  JITTER ANALYSIS  (start-time variation from ideal periodic release)")
    sep = "  " + "─" * 76
    lines.append(sep)

    # Build period lookup
    period_map = {t.name: t.period_us for t in tasks}

    header = (
        f"  {'Task':<22} {'Activations':>12} "
        f"{'Max Jitter µs':>14} {'Mean Jitter µs':>15} {'Assessment'}"
    )
    lines.append(header)
    lines.append(sep)

    for task_name, starts in sorted(sim.start_times.items()):
        if not starts:
            continue
        period = period_map.get(task_name, 0)
        if period <= 0:
            continue

        # Compute jitter: difference between actual start and ideal start
        # Ideal start for activation k = k * period
        jitters = []
        for k, actual_start in enumerate(sorted(starts)):
            ideal = k * period
            jitters.append(min(abs(actual_start - ideal), period))

        max_j  = max(jitters)
        mean_j = sum(jitters) / len(jitters)

        # Assessment
        if max_j < period * 0.01:
            assess = "EXCELLENT  (<1% of period)"
        elif max_j < period * 0.05:
            assess = "GOOD       (<5% of period)"
        elif max_j < period * 0.20:
            assess = "MODERATE   (<20% of period)"
        else:
            t_obj = next((t for t in tasks if t.name == task_name), None)
            core_tasks = [t for t in tasks if t_obj and getattr(t, 'core_id', 0) == getattr(t_obj, 'core_id', 0) and t.period_us > 0]
            core_u = sum(t.wcet_us / t.period_us for t in core_tasks) if core_tasks else 0.0
            all_sched = all(getattr(t, 'schedulable', True) is not False for t in core_tasks)
            if core_u >= 0.75 and all_sched:
                assess = "HIGH       (>20% of period — expected at high utilization; reduce utilization if jitter affects control stability)"
            else:
                assess = "HIGH       (>20% of period — review priority assignment)"

        lines.append(
            f"  {task_name:<22} {len(starts):>12}  "
            f"{max_j:>13.2f}  {mean_j:>14.2f}  {assess}"
        )

    lines.append(sep)
    lines.append(
        "  NOTE: Jitter is measured against the ideal periodic release time.\n"
        "  Non-zero jitter is caused by higher-priority task preemption.\n"
        "  For sensor/control loops, high jitter degrades control stability.\n"
        "  Jitter on single-task cores reflects simulation granularity/drift, not real-world preemption delay."
    )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_row(
    task_name: str,
    intervals: List[GanttInterval],
    hp: float,
    width: int,
    scale: float,
    sym: str,
    misses: List[float] = None
) -> str:
    """Build a single Gantt row string of length `width`."""
    if misses is None:
        misses = []
        
    row = [IDLE_CHAR] * width

    # Mark deadlines
    for dl in misses:
        col = int(dl / scale)
        if 0 <= col < width:
            row[col] = '\033[91m|\033[0m'

    for iv in intervals:
        start_col = int(iv.start_us / scale)
        end_col   = int(math.ceil(iv.end_us / scale))
        start_col = max(0, min(start_col, width - 1))
        end_col   = max(0, min(end_col,   width))

        for col in range(start_col, end_col):
            # If past any missed deadline, color it red
            is_past_dl = any(dl <= (col * scale) for dl in misses)
            
            if row[col] == '\033[91m|\033[0m':
                pass # keep the line
            else:
                if is_past_dl:
                    row[col] = f'\033[91m{EXEC_CHAR}\033[0m'
                else:
                    row[col] = EXEC_CHAR

        if iv.preempted and end_col < width:
            # Don't overwrite deadline marker with preemption
            if row[min(end_col, width - 1)] != '\033[91m|\033[0m':
                is_past_dl = any(dl <= (min(end_col, width - 1) * scale) for dl in misses)
                if is_past_dl:
                    row[min(end_col, width - 1)] = f'\033[91m{PREEMPT_CHAR}\033[0m'
                else:
                    row[min(end_col, width - 1)] = PREEMPT_CHAR

    # We return a string. Since we use ANSI codes which are multiple chars, 
    # we just join. The actual visual length is preserved because ANSI codes are zero-width in terminal.
    return ''.join(row)


def _build_ruler(hp: float, width: int, scale: float, label_width: int) -> str:
    """Build the time-axis ruler below the Gantt rows."""
    ruler_chars = list(" " * width)
    tick_interval_us  = _nice_tick(hp, width)
    t = 0.0
    while t <= hp + 1e-6:
        col = int(t / scale)
        if col < width:
            label = str(int(t))
            for i, ch in enumerate(label):
                if col + i < width:
                    ruler_chars[col + i] = ch
        t += tick_interval_us

    pad = " " * (label_width + 3)
    return f"  {pad}{''.join(ruler_chars)}"


def _nice_tick(hp: float, width: int) -> float:
    """Choose a 'nice' tick interval so the ruler has 4–10 ticks."""
    approx = hp / 8.0
    for base in [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]:
        if approx <= base:
            return float(base)
    return approx
