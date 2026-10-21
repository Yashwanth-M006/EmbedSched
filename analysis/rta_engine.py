"""
analysis/rta_engine.py

Response Time Analysis (RTA) for fixed-priority preemptive scheduling (RM/DM)
and utilization bound tests for dynamic priority (EDF).

Includes Priority Ceiling Protocol (PCP/SRP) blocking time calculations and
inter-core communication latency bounds.
"""

import math
import sys
from typing import List, Dict, Tuple
from models.autosar_task import AutosarTask, CoreConfig, Resource, InterCoreChannel


MAX_ITERATIONS = 1000   # safety cap to prevent infinite loops on pathological inputs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _get_bus_latency(region_name: str, chip_regions: dict) -> float:
    if not chip_regions or region_name not in chip_regions:
        return 1.0 # default 1us
    region = chip_regions[region_name]
    ws = region.get('wait_states', 0)
    return (1 + ws) * 0.01

def run_rta(tasks: List[AutosarTask], cores: Dict[int, CoreConfig] = None, resources: List[Resource] = None, channels: List[InterCoreChannel] = None, chip_regions: dict = None, chip_profile: dict = None) -> None:
    if cores is None: cores = {}
    if resources is None: resources = []
    if channels is None: channels = []
    
    # Calculate inter-core latencies
    task_by_name = {t.name: t for t in tasks}
    core_freqs = {}
    if chip_profile:
        global_freq = chip_profile.get('clock_max_mhz', 100.0)
        for c in chip_profile.get('core_types', []):
            core_freqs[c.get('id')] = c.get('clock_max_mhz', global_freq)
        # fallback for single-core
        if not core_freqs:
            core_freqs[0] = global_freq

    channel_latency = {}
    for ch in channels:
        lat = 0.0
        spin_lat = 0.0
        found = False
        if chip_profile and 'inter_core_shared_regions' in chip_profile:
            for r in chip_profile['inter_core_shared_regions']:
                if r.get('name') == ch.shared_region:
                    overhead = r.get('spinlock_overhead_cycles', 0)
                    to_task = task_by_name.get(ch.to_task)
                    if to_task:
                        freq = core_freqs.get(to_task.core_id, 100.0)
                        spin_lat = overhead / freq
                    lat += r.get('data_write_latency_us', 0.0)
                    found = True
                    break
        if not found and not spin_lat:
            spin_lat = _get_bus_latency(ch.shared_region, chip_regions)

        # 2. Channel-specified write latency or data-dependency from sender WCET
        if getattr(ch, 'write_latency_us', 0.0) > 0:
            lat = ch.write_latency_us
        elif ch.from_task in task_by_name and lat == 0.0:
            from_t = task_by_name[ch.from_task]
            if from_t.wcet_us > 0:
                lat = 0.05 * from_t.wcet_us

        total_lat = lat + spin_lat
        ch.latency_us = total_lat
        channel_latency[ch.to_task] = channel_latency.get(ch.to_task, 0) + total_lat

    # Compute PCP ceilings (lower integer = higher priority)
    res_map = {r.name: r for r in resources}
    # Initialize ceilings to infinity
    for r in resources:
        r.ceiling = float('inf')
        
    for t in tasks:
        for r_name in t.resources:
            if r_name in res_map:
                res_map[r_name].ceiling = min(res_map[r_name].ceiling, t.priority)

    core_tasks = _group_by_core(tasks)
    
    for core_id, c_tasks in core_tasks.items():
        config = cores.get(core_id, CoreConfig(id=core_id, algorithm="RM"))
        ordered = sorted(c_tasks, key=lambda t: t.priority)
        
        if config.algorithm in ("RM", "DM", "FPP"):
            _run_fixed_priority_rta(ordered, res_map, channel_latency)
        elif config.algorithm == "EDF":
            _run_edf_analysis(ordered, channel_latency)


def compute_utilization(tasks: List[AutosarTask], cores: Dict[int, CoreConfig] = None) -> Dict[int, Dict]:
    if cores is None: cores = {}
    cores_map = _group_by_core(tasks)
    result = {}
    for core_id, core_tasks in cores_map.items():
        periodic = [t for t in core_tasks if t.period_us > 0]
        n = len(periodic)
        config = cores.get(core_id, CoreConfig(id=core_id, algorithm="RM"))
        is_edf = config.algorithm == "EDF"
        
        bound = 1.0 if is_edf else (n * (2 ** (1.0 / n) - 1.0)) if n > 0 else 1.0

        if n == 0:
            result[core_id] = {
                'utilization': 0.0,
                'task_count':  0,
                'bound':       bound,
                'rm_bound':    bound,
                'schedulable_by_utilization': True,
                'algorithm': config.algorithm,
                'is_edf': is_edf,
                'has_constrained_deadline': False,
                'pda_passed': None,
            }
            continue

        U = sum(t.wcet_us / t.period_us for t in periodic)
        constrained = any(t.deadline_us < t.period_us for t in periodic)

        pda_passed = None
        tightest_L = None
        tightest_margin = None
        if is_edf and constrained:
            pda_passed = all(t.schedulable is True for t in periodic)
            tightest_L = min((t.pda_tightest_L for t in periodic if getattr(t, 'pda_tightest_L', None) is not None), default=None)
            tightest_margin = min((t.pda_tightest_margin for t in periodic if getattr(t, 'pda_tightest_margin', None) is not None), default=None)

        result[core_id] = {
            'utilization': U,
            'task_count':  n,
            'bound':       bound,
            'rm_bound':    bound,
            'schedulable_by_utilization': U <= bound,
            'algorithm': config.algorithm,
            'is_edf': is_edf,
            'has_constrained_deadline': constrained,
            'pda_passed': pda_passed,
            'pda_tightest_L': tightest_L,
            'pda_tightest_margin': tightest_margin,
        }
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _group_by_core(tasks: List[AutosarTask]) -> Dict[int, List[AutosarTask]]:
    cores: Dict[int, List[AutosarTask]] = {}
    for t in tasks:
        cores.setdefault(t.core_id, []).append(t)
    return cores


def _run_fixed_priority_rta(ordered: List[AutosarTask], res_map: Dict[str, Resource], channel_latency: Dict[str, float]) -> None:
    for i, task in enumerate(ordered):
        if task.deadline_us <= 0:
            task.wcrt_us    = 0.0
            task.schedulable = None
            task.margin_us  = float('inf')
            continue

        if task.wcet_us <= 0:
            task.wcrt_us    = 0.0
            task.schedulable = None
            task.margin_us  = float('inf')
            continue

        # Calculate Blocking Time B_i (PCP)
        B_i = 0.0
        blocking_source_task = None
        blocking_source_res = None
        lower_priority_tasks = ordered[i+1:]
        for lp_task in lower_priority_tasks:
            for r_name in lp_task.resources:
                if r_name in res_map and res_map[r_name].ceiling <= task.priority:
                    res_obj = res_map[r_name]
                    cs_duration = res_obj.critical_section_us
                    if getattr(res_obj, 'task_critical_sections_us', None) and lp_task.name in res_obj.task_critical_sections_us:
                        cs_duration = res_obj.task_critical_sections_us[lp_task.name]
                    if cs_duration > B_i:
                        B_i = cs_duration
                        blocking_source_task = lp_task.name
                        blocking_source_res = r_name
        
        # Add inter-core communication blocking
        B_i += channel_latency.get(task.name, 0.0)
        task.blocking_us = B_i
        task.blocking_source_task = blocking_source_task
        task.blocking_source_res = blocking_source_res

        hp_tasks = [t for t in ordered[:i] if t.period_us > 0 and t.wcet_us > 0]
        R = task.wcet_us + B_i
        
        converged = False
        for _ in range(MAX_ITERATIONS):
            interference = sum(math.ceil(round(R, 6) / hp.period_us) * hp.wcet_us for hp in hp_tasks)
            R_new = task.wcet_us + B_i + interference

            if R_new > task.deadline_us:
                R = R_new
                converged = True  # Deadline miss proven
                break
            if abs(R_new - R) < 1e-9:
                R = R_new
                converged = True
                break
            R = R_new

        task.wcrt_us = R
        if not converged:
            print(f"[RTA] Warning: task '{task.name}' did not converge in {MAX_ITERATIONS} iterations.", file=sys.stderr)
            task.schedulable = None
            task.margin_us = task.deadline_us - R
        else:
            task.schedulable = R <= task.deadline_us
            task.margin_us  = task.deadline_us - R

def _run_edf_analysis(tasks: List[AutosarTask], channel_latency: Dict[str, float]) -> None:
    import math

    # Basic setup
    periodic = [t for t in tasks if t.period_us > 0]
    for task in tasks:
        task.blocking_us = channel_latency.get(task.name, 0.0)
        task.pda_tightest_L = None
        task.pda_tightest_margin = float('inf')
        task.pda_failed_L = None

    if not periodic:
        for task in tasks:
            task.wcrt_us = task.wcet_us + task.blocking_us
            task.schedulable = True
            task.margin_us = task.deadline_us - task.wcrt_us
        return

    # 1. Exact Response Time Analysis under Preemptive EDF
    for i, task in enumerate(tasks):
        if task.period_us <= 0 or task.wcet_us <= 0:
            task.wcrt_us = task.wcet_us + task.blocking_us
            task.schedulable = True
            task.margin_us = task.deadline_us - task.wcrt_us
            continue

        max_R = task.wcet_us + task.blocking_us
        # Evaluate activations across the first busy period.
        # max_p is bounded to 5 activations as a tractable approximation for WCRT;
        # Processor Demand Analysis (PDA) below provides the full exact feasibility test.
        max_p = 5
        for p in range(max_p):
            d_ip = p * task.period_us + task.deadline_us
            t = (p + 1) * (task.wcet_us + task.blocking_us)
            for _ in range(100):
                w = (p + 1) * (task.wcet_us + task.blocking_us)
                for j, other in enumerate(tasks):
                    if i == j or other.period_us <= 0 or other.wcet_us <= 0:
                        continue
                    n_jobs = max(0, math.floor((d_ip - other.deadline_us) / other.period_us) + 1)
                    active_jobs = min(n_jobs, math.ceil(round(t, 6) / other.period_us))
                    w += active_jobs * (other.wcet_us + other.blocking_us)
                if abs(w - t) < 1e-6:
                    t = w
                    break
                t = w
                if t - p * task.period_us > task.deadline_us:
                    break
            R_p = t - p * task.period_us
            if R_p > max_R:
                max_R = R_p

        task.wcrt_us = max_R
        task.margin_us = task.deadline_us - max_R
        task.schedulable = max_R <= task.deadline_us

    # Check if constrained deadlines
    constrained = any(t.deadline_us < t.period_us for t in periodic)
    U = sum((t.wcet_us + t.blocking_us) / t.period_us for t in periodic)

    if not constrained:
        if U > 1.0:
            for task in tasks:
                task.schedulable = False
        return

    # Processor Demand Analysis
    # Calculate hyperperiod for bounds
    def gcd(a, b):
        return a if b == 0 else gcd(b, a % b)
    def lcm(a, b):
        return a * b // gcd(a, b)
    
    periods_int = [int(round(t.period_us)) for t in periodic]
    if any(abs(round(t.period_us) - t.period_us) > 0.001 for t in periodic):
        print("[RTA] Warning: fractional periods rounded to integer for PDA hyperperiod.", file=sys.stderr)

    H = periods_int[0]
    for p_int in periods_int[1:]:
        H = lcm(H, p_int)
    H = min(H, 10000000) # cap at 10s for safety

    # Collect all scheduling points (all absolute deadlines <= H)
    scheduling_points = set()
    for t in periodic:
        k = 0
        while True:
            d = k * t.period_us + t.deadline_us
            if d > H:
                break
            scheduling_points.add(d)
            k += 1
            
    scheduling_points = sorted(list(scheduling_points))
    
    tightest_L = None
    tightest_margin = float('inf')
    failed_L = None
    
    for L in scheduling_points:
        h_L = 0.0
        for t in periodic:
            if L >= t.deadline_us:
                h_L += math.floor((L + t.period_us - t.deadline_us) / t.period_us) * (t.wcet_us + t.blocking_us)
                
        margin = L - h_L
        if margin < tightest_margin:
            tightest_margin = margin
            tightest_L = L
            
        if h_L > L:
            failed_L = L
            break
            
    # Attach to a task (or all) for rules to pick up
    for task in tasks:
        task.pda_tightest_L = tightest_L
        task.pda_tightest_margin = tightest_margin
        task.pda_failed_L = failed_L
        if failed_L is not None:
            task.schedulable = False

