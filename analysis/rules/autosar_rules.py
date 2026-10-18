"""
analysis/rules/autosar_rules.py

Rule engine for AUTOSAR schedulability findings.

Follows the same Finding-based pattern as all other rules in this project.
Each function returns a list of Finding objects.

New rule codes (extending existing WEIGHTS dict in terminal_report.py):
    autosar_deadline_miss        CRITICAL  -30   RTA shows task misses deadline
    autosar_cpu_overload         CRITICAL  -25   Utilization > 100%
    autosar_utilization_warning  WARNING   -15   U > RM bound but < 100%
    autosar_wcet_dominates       WARNING   -10   WCET > 50% of period
    autosar_double_risk          WARNING   -10   unbounded stack + tight deadline
    autosar_isr_flash_wcet       WARNING   -5    ISR in Flash → WCET inflated
    autosar_no_margin            INFO       0    Very small margin (< 5% of deadline)
"""

from typing import List, Dict, Set, Tuple
from models.finding import Finding
from models.autosar_task import AutosarTask
from models.symbol import Symbol


# ---------------------------------------------------------------------------
# Rule: Deadline miss (from RTA)
# ---------------------------------------------------------------------------

def check_deadline_misses(tasks: List[AutosarTask]) -> List[Finding]:
    findings = []
    for t in tasks:
        if t.schedulable is False:
            overshoot = t.wcrt_us - t.deadline_us
            findings.append(Finding(
                rule='autosar_deadline_miss',
                severity='CRITICAL',
                tag=f'[RTA/{t.wcet_tag}]',
                message=(
                    f"Task '{t.name}' MISSES its deadline.\n"
                    f"  Function mapped  : {t.function}\n"
                    f"  WCET             : {t.wcet_us:.2f} µs  {t.wcet_tag}\n"
                    f"  Deadline         : {t.deadline_us:.0f} µs\n"
                    f"  Worst-case resp. : {t.wcrt_us:.2f} µs\n"
                    f"  Overrun          : +{overshoot:.2f} µs\n"
                    f"  Call chain       : {' → '.join(t.wcet_call_chain)}\n"
                    f"  NOTE: WCET is {t.wcet_tag} — treat response time as "
                    f"{'optimistic lower bound' if t.wcet_tag == '[CALCULATED]' else 'functional estimate'}."
                ),
                fix=(
                    "Raise priority, shorten period, reduce WCET by moving "
                    "hot functions to ITCM, or offload work to a lower-priority task."
                ),
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: Heuristic WCET (function not found in symbols or trace)
# ---------------------------------------------------------------------------

def check_heuristic_wcet(tasks: List[AutosarTask]) -> List[Finding]:
    """
    Fires a WARNING for every task whose WCET tag is [HEURISTIC].
    This happens when the entry function is absent from both the ELF symbol
    table and the Renode dynamic profile — the tool fell back to a 10-cycle
    placeholder, which is effectively a guess.
    """
    findings = []
    for t in tasks:
        if t.wcet_tag == '[HEURISTIC]':
            findings.append(Finding(
                rule='autosar_heuristic_wcet',
                severity='WARNING',
                tag='[HEURISTIC]',
                message=(
                    f"Task '{t.name}' WCET is heuristic — "
                    f"stack usage file missing or function '{t.function}' not found in ELF symbols or Renode trace. "
                    f"Recompile with -fstack-usage for higher confidence. [HEURISTIC]\n"
                    f"  Current WCET estimate: {t.wcet_us:.2f} µs [HEURISTIC] — treat as unreliable."
                ),
                fix=(
                    "Verify 'entry_function' in schedule.json matches the C function name exactly. "
                    "Recompile with -ffunction-sections and -fstack-usage. "
                    "For higher confidence, profile on hardware with Segger SystemView or TRACE32."
                ),
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: CPU overload (utilization > 100%)
# ---------------------------------------------------------------------------

def check_cpu_overload(util_info: Dict[int, Dict]) -> List[Finding]:
    findings = []
    for core_id, info in util_info.items():
        U = info['utilization']
        if U > 1.0:
            findings.append(Finding(
                rule='autosar_cpu_overload',
                severity='CRITICAL',
                tag='[CALCULATED]',
                message=(
                    f"Core {core_id}: CPU OVERLOADED.\n"
                    f"  Utilization : {U*100:.1f}% > 100%\n"
                    f"  Tasks       : {info['task_count']}\n"
                    f"  System cannot be schedulable under any priority assignment."
                ),
                fix=(
                    "Reduce WCET of dominant tasks, increase task periods, "
                    "or offload tasks to another core."
                ),
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: Utilization above RM bound (indeterminate zone)
# ---------------------------------------------------------------------------

def check_utilization_warning(util_info: Dict[int, Dict]) -> List[Finding]:
    findings = []
    for core_id, info in util_info.items():
        U = info['utilization']
        bound = info['rm_bound']
        if bound < U <= 1.0:
            findings.append(Finding(
                rule='autosar_utilization_warning',
                severity='WARNING',
                tag='[CALCULATED]',
                message=(
                    f"Core {core_id}: utilization in INDETERMINATE zone.\n"
                    f"  Utilization   : {U*100:.1f}%\n"
                    f"  RM bound      : {bound*100:.1f}% (n={info['task_count']} tasks)\n"
                    f"  Liu & Layland guarantee does NOT apply above the RM bound.\n"
                    f"  The task set MAY still be schedulable — check RTA results."
                ),
                fix="Verify via RTA. Reduce utilization or adopt a specific priority assignment.",
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: WCET dominates period (> 50% of period)
# ---------------------------------------------------------------------------

def check_wcet_dominates(tasks: List[AutosarTask]) -> List[Finding]:
    findings = []
    for t in tasks:
        if t.period_us <= 0 or t.wcet_us <= 0:
            continue
        ratio = t.wcet_us / t.period_us
        if ratio > 0.5:
            findings.append(Finding(
                rule='autosar_wcet_dominates',
                severity='WARNING',
                tag=t.wcet_tag,
                message=(
                    f"Task '{t.name}': WCET dominates its period.\n"
                    f"  WCET / Period = {t.wcet_us:.2f} / {t.period_us:.0f} µs = {ratio*100:.0f}%\n"
                    f"  Leaves only {(1-ratio)*100:.0f}% of the period for other tasks.\n"
                    f"  Function: {t.function}  {t.wcet_tag}"
                ),
                fix=(
                    "Split task body into pre-emption points, move "
                    "expensive computation to a lower-priority helper task, "
                    "or increase the period."
                ),
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: Double risk — unbounded stack depth AND tight deadline margin
# ---------------------------------------------------------------------------

def check_double_risk(
    tasks: List[AutosarTask],
    recursive_functions: Set[str],
) -> List[Finding]:
    """
    Flag tasks whose entry function has recursion in its call graph (unbounded
    stack depth) AND has a deadline margin < 10% of the deadline.
    """
    findings = []
    for t in tasks:
        has_recursion = t.function in recursive_functions
        if not has_recursion:
            # Check if any function in the call chain is recursive
            has_recursion = any(f in recursive_functions for f in t.wcet_call_chain)

        if has_recursion and t.schedulable is not None:
            margin_pct = (t.margin_us / t.deadline_us * 100) if t.deadline_us > 0 else 0
            if margin_pct < 10.0:
                findings.append(Finding(
                    rule='autosar_double_risk',
                    severity='WARNING',
                    tag='[STATIC]',
                    message=(
                        f"Task '{t.name}': DOUBLE RISK — recursion + tight deadline.\n"
                        f"  Recursion detected in call chain: {' → '.join(t.wcet_call_chain)}\n"
                        f"  Deadline margin: {t.margin_us:.2f} µs ({margin_pct:.1f}% of deadline)\n"
                        f"  WCET is underestimated if recursion depth is non-trivial."
                    ),
                    fix=(
                        "Eliminate recursion in ISR/task hot paths. "
                        "If recursion is unavoidable, bound the depth and add to WCET estimate."
                    ),
                ))
    return findings


# ---------------------------------------------------------------------------
# Rule: ISR in Flash → WCET inflated
# ---------------------------------------------------------------------------

def check_isr_flash_wcet(
    isr_tasks: List[AutosarTask],
    isr_in_flash: Set[str],
    chip_profile: dict = None,
) -> List[Finding]:
    """
    Flag ISR pseudo-tasks whose handler is in Flash rather than ITCM.
    Their WCET estimate does not include the cache miss penalty, so the
    schedulability analysis is optimistic.
    """
    findings = []
    has_itcm = chip_profile and 'ITCM' in chip_profile.get('memory_regions', {})
    for t in isr_tasks:
        if t.name in isr_in_flash or t.function in isr_in_flash:
            if has_itcm:
                msg = (
                    f"{t.function} placed in FLASH — ISR WCET inflated by 4 wait states. "
                    f"Move to ITCM to recover 19.2μs per invocation. [CALCULATED, ARMv7-M §B1.5.6]"
                )
                fix = "Move to ITCM to recover 19.2μs per invocation. [CALCULATED, ARMv7-M §B1.5.6]"
            else:
                msg = (
                    f"{t.function} in FLASH, 4 wait states inflating WCET. "
                    f"Recovery: 19.2µs → becomes ~1.1µs with ITCM (but STM32F407 has no ITCM, so ART accelerator suggestion instead). [CALCULATED]"
                )
                fix = "Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit() to mitigate wait states."

            findings.append(Finding(
                rule='autosar_isr_flash_wcet',
                severity='WARNING',
                tag='[CALCULATED]',
                message=msg,
                fix=fix,
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: Very small margin (informational)
# ---------------------------------------------------------------------------

def check_near_deadline(tasks: List[AutosarTask]) -> List[Finding]:
    findings = []
    for t in tasks:
        if t.schedulable is not True or t.deadline_us <= 0:
            continue
        margin_pct = t.margin_us / t.deadline_us * 100
        if 0.0 < margin_pct < 5.0:
            findings.append(Finding(
                rule='autosar_no_margin',
                severity='INFO',
                tag=t.wcet_tag,
                message=(
                    f"Task '{t.name}': margin is very thin.\n"
                    f"  Deadline margin: {t.margin_us:.2f} µs ({margin_pct:.1f}% of deadline)\n"
                    f"  Any increase in WCET (cache effects, ISR load) may cause a miss.\n"
                    f"  WCET source: {t.wcet_tag}"
                ),
                fix="Add timing margin buffer or profile actual execution time on hardware.",
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule: RM suboptimal for constrained deadlines
# ---------------------------------------------------------------------------

def check_rm_suboptimal_assignment(tasks: List[AutosarTask], cores_config: Dict[int, 'CoreConfig']) -> List[Finding]:
    findings = []
    for t in tasks:
        # Check if algorithm for this core is RM
        core_config = cores_config.get(t.core_id)
        if core_config and core_config.algorithm == "RM":
            if t.deadline_us < t.period_us:
                missed = (t.schedulable is False)
                severity = 'INFO' if missed else 'WARNING'
                msg = f"Task '{t.name}' has deadline < period ({t.deadline_us:.0f} µs < {t.period_us:.0f} µs) — RM priority assignment is suboptimal, use DM."
                if missed:
                    msg += " Switching to DM may resolve this miss."
                    
                findings.append(Finding(
                    rule='autosar_rm_suboptimal',
                    severity=severity,
                    tag='[STATIC]',
                    message=msg,
                    fix="Change core scheduling algorithm to DM (Deadline Monotonic) or EDF.",
                ))
    return findings


# ---------------------------------------------------------------------------
# Rule: PCP Blocking Info
# ---------------------------------------------------------------------------

def check_pcp_blocking(tasks: List[AutosarTask]) -> List[Finding]:
    findings = []
    for t in tasks:
        if t.blocking_us > 0:
            src_task = getattr(t, 'blocking_source_task', None)
            src_res = getattr(t, 'blocking_source_res', None)
            if src_task and src_res:
                msg = f"{t.name} blocked by {src_task} on {src_res} for up to {t.blocking_us/1000.0:g}ms [CALCULATED] (PCP)"
            else:
                msg = f"Task {t.name.split('_')[-1] if '_' in t.name else t.name} blocked by lower priority tasks on shared resource for up to {t.blocking_us/1000.0}ms [CALCULATED]"
            findings.append(Finding(
                rule='autosar_pcp_blocking',
                severity='INFO',
                tag='[CALCULATED]',
                message=msg,
                fix="PCP correctly bounds priority inversion to a single critical section.",
            ))
    return findings

# ---------------------------------------------------------------------------
# Rule: EDF Priority Null
# ---------------------------------------------------------------------------
def check_edf_priority_null(tasks: List[AutosarTask], cores: dict) -> List[Finding]:
    findings = []
    seen = set()
    for t in tasks:
        config = cores.get(t.core_id)
        if config and config.algorithm == "EDF":
            msg = "EDF tasks must have priority=null — priority field ignored for EDF cores"
            if msg not in seen:
                findings.append(Finding(
                    rule='autosar_edf_priority_null',
                    severity='INFO',
                    tag='[EDF]',
                    message=msg,
                    fix="Ensure tasks on EDF cores omit the priority field or set priority=null.",
                ))
                seen.add(msg)
    return findings

# ---------------------------------------------------------------------------
# Rule: EDF Constrained Deadline
# ---------------------------------------------------------------------------
def check_edf_constrained_deadline(tasks: List[AutosarTask], cores: dict) -> List[Finding]:
    findings = []
    
    # We only want to report the PDA summary once per EDF core with constrained deadlines.
    reported_cores = set()
    
    for t in tasks:
        config = cores.get(t.core_id)
        if config and config.algorithm == "EDF" and t.deadline_us < t.period_us:
            if getattr(t, 'pda_tightest_L', None) is not None and t.core_id not in reported_cores:
                reported_cores.add(t.core_id)
                failed_L = getattr(t, 'pda_failed_L', None)
                tightest_L = getattr(t, 'pda_tightest_L', None)
                
                if failed_L is not None:
                    msg = (
                        f"EDF Processor Demand Analysis: FAILED at L={failed_L}µs "
                        f"(demand h({failed_L}) > {failed_L}µs)."
                    )
                    severity = 'CRITICAL'
                else:
                    constrained_tasks = [task for task in tasks if task.core_id == t.core_id and task.deadline_us < task.period_us]
                    if len(constrained_tasks) == 1:
                        task_desc = f"{t.name} has constrained deadline ({t.deadline_us/1000.0:.1f}ms < {t.period_us/1000.0:.1f}ms period)"
                    else:
                        task_names = ", ".join(ct.name for ct in constrained_tasks)
                        task_desc = f"Tasks ({task_names}) have constrained deadlines (D < T)"
                    msg = (
                        f"{task_desc} — processor demand analysis used instead of simple utilization check.\n"
                        f"  Checked all scheduling points up to hyperperiod.\n"
                        f"  Tightest margin found at L={tightest_L}µs."
                    )
                    severity = 'INFO'
                    
                findings.append(Finding(
                    rule='autosar_edf_constrained_deadline',
                    severity=severity,
                    tag='[EDF]',
                    message=msg,
                    fix="Use processor demand analysis (PDA) for precise EDF schedulability.",
                ))
    return findings

# ---------------------------------------------------------------------------
# Rule: Hyperperiod Explosion
# ---------------------------------------------------------------------------
def check_hyperperiod_explosion(tasks: List[AutosarTask], hyperperiod_us: float, capped: bool) -> List[Finding]:
    findings = []
    if capped:
        hp_ms = int(round(hyperperiod_us / 1000.0))
        findings.append(Finding(
            rule='autosar_hyperperiod_explosion',
            severity='WARNING',
            tag='[CALCULATED]',
            message=(
                f"Hyperperiod = {hp_ms:,}ms — full simulation disabled.\n"
                f"Showing representative 30ms window only. RTA used for schedulability verdict. [CALCULATED]"
            ),
            fix="Harmonize task periods (e.g., make them multiples of a common base) to reduce hyperperiod.",
        ))
    return findings

# ---------------------------------------------------------------------------
# Rule: Concurrent Stack Pressure (Integration of static stack & scheduling)
# ---------------------------------------------------------------------------
def check_concurrent_stack_pressure(
    tasks: List[AutosarTask],
    call_graph: dict,
    stack_usage: dict,
    worst_case_stack_depth_fn,
    merged_linker_symbols: dict
) -> List[Finding]:
    findings = []
    
    # 1. Determine declared stack size
    declared_size = 4096
    if '_Min_Stack_Size' in merged_linker_symbols:
        sym = merged_linker_symbols['_Min_Stack_Size']
        declared_size = sym.address if hasattr(sym, 'address') else int(sym)
        
    # Group tasks by core (assume full preemption on each core)
    cores = {}
    for t in tasks:
        cores.setdefault(t.core_id, []).append(t)
        
    for core_id, core_tasks in cores.items():
        total_pressure = 0
        for t in core_tasks:
            d, _, _ = worst_case_stack_depth_fn(call_graph, stack_usage, t.function)
            task_stack = getattr(t, 'stack_bytes', 0) or d
            total_pressure += task_stack
            
        if total_pressure > declared_size:
            findings.append(Finding(
                rule='autosar_concurrent_stack',
                severity='WARNING',
                tag='[STATIC]',
                message=(
                    f"Concurrent worst-case stack depth ({total_pressure}B) exceeds declared stack size ({declared_size}B) "
                    f"— stack overflow possible under full preemption [STATIC]"
                ),
                fix="Increase _Min_Stack_Size in linker.ld or reduce stack usage.",
            ))
        elif total_pressure == declared_size and declared_size > 0:
            findings.append(Finding(
                rule='autosar_concurrent_stack',
                severity='WARNING',
                tag='[STATIC]',
                message=(
                    f"Concurrent worst-case stack depth ({total_pressure}B) reaches declared stack size ({declared_size}B) "
                    f"with zero margin under full preemption [STATIC]"
                ),
                fix="Increase _Min_Stack_Size in linker.ld to provide stack headroom.",
            ))
            
    return findings


# ---------------------------------------------------------------------------
# Rule: Cross-Core Deadlock Risk (lock acquisition order inversion)
# ---------------------------------------------------------------------------

def check_deadlock_risk(resources: List) -> List[Finding]:
    """
    Detect circular resource acquisition order across tasks (classic deadlock).

    Algorithm:
      1. For every task that appears in any resource's acquisition_order, build
         its ordered lock sequence: sorted(resources, key=acquisition_order[task]).
      2. Translate each consecutive pair in that sequence into a directed edge in
         a global resource-dependency graph:  Lock_i  →  Lock_{i+1}
         (meaning: a holder of Lock_i can be blocked waiting for Lock_{i+1})
      3. Run DFS cycle detection on this directed graph.
      4. Each detected cycle is a potential deadlock path.
    """
    findings = []

    # Build per-task lock sequences
    # task_lock_order[task_name] = [res_name_in_acquisition_order, ...]
    task_lock_order: Dict[str, list] = {}
    for res in resources:
        for task_name, order in res.acquisition_order.items():
            task_lock_order.setdefault(task_name, [])
            task_lock_order[task_name].append((order, res.name))

    # Sort by order index and keep only resource names
    for task_name in task_lock_order:
        task_lock_order[task_name] = [
            rname for _, rname in sorted(task_lock_order[task_name])
        ]

    # Build directed lock dependency graph (edges from consecutive lock pairs per task)
    # Edge  A -> B means: some task holds A and then tries to acquire B
    graph: Dict[str, Set] = {}
    edge_owners: Dict[tuple, list] = {}  # (src, dst) -> [task_names]

    for task_name, lock_seq in task_lock_order.items():
        for i in range(len(lock_seq) - 1):
            src, dst = lock_seq[i], lock_seq[i + 1]
            graph.setdefault(src, set()).add(dst)
            graph.setdefault(dst, set())  # ensure node exists
            edge_owners.setdefault((src, dst), []).append(task_name)

    # DFS cycle detection — find all simple cycles
    def _find_cycle(graph: Dict[str, Set]) -> list:
        """Return the first cycle found as a list of nodes, or []."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _dfs(node: str, path: list) -> list:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbour in graph.get(node, set()):
                if neighbour not in visited:
                    result = _dfs(neighbour, path)
                    if result:
                        return result
                elif neighbour in rec_stack:
                    # Cycle detected — extract the cycle portion
                    cycle_start = path.index(neighbour)
                    return path[cycle_start:] + [neighbour]
            path.pop()
            rec_stack.discard(node)
            return []

        for node in list(graph.keys()):
            if node not in visited:
                result = _dfs(node, [])
                if result:
                    return result
        return []

    cycle = _find_cycle(graph)
    if cycle:
        # Reconstruct which tasks are involved in the cycle
        involved_tasks: Dict[str, list] = {}  # task -> [lock_order description]
        for task_name, lock_seq in task_lock_order.items():
            if any(lk in cycle for lk in lock_seq):
                involved_tasks[task_name] = lock_seq

        # Build human-readable description of each task's lock order
        task_descriptions = []
        for task_name, lock_seq in sorted(involved_tasks.items()):
            task_descriptions.append(
                f"{task_name} acquires: {' → '.join(lock_seq)}"
            )

        cycle_str = " → ".join(cycle)
        msg = (
            f"Deadlock risk detected — inconsistent lock acquisition order across tasks.\n"
            f"  Lock cycle: {cycle_str}\n"
        )
        for desc in task_descriptions:
            msg += f"  {desc}\n"
        msg += "  Enforce a consistent global lock ordering to eliminate the cycle. [STATIC]"

        findings.append(Finding(
            rule='autosar_deadlock_risk',
            severity='CRITICAL',
            tag='[STATIC]',
            message=msg,
            fix=(
                "Impose a global total order on all locks (e.g., alphabetical or by ID). "
                "Every task must acquire locks in that order. Never acquire lock B while "
                "holding lock A if any other task acquires A after B."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: Entry Function Mismatch / Typo Detection (Levenshtein Distance)
# ---------------------------------------------------------------------------

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def check_entry_function_mismatches(
    tasks: List[AutosarTask],
    symbols: List[Symbol]
) -> Tuple[List[AutosarTask], List[Finding], bool]:
    """
    Validate that entry_function for each task exists in the firmware symbols (e.g. from .map / ELF).
    If a task has a typo/mismatch:
      - Emits clear diagnostic error with Levenshtein distance suggestion.
      - Excludes the task from schedulability analysis so remaining tasks can be analyzed.
      - Returns (valid_tasks, findings, has_error).
    """
    firmware_symbol_names = {s.name for s in symbols}
    valid_tasks = []
    findings = []
    has_error = False

    for t in tasks:
        if t.function in firmware_symbol_names:
            valid_tasks.append(t)
            continue

        # Function not found in firmware symbols. Check for close match by edit distance.
        closest = None
        min_dist = float('inf')
        for sym_name in firmware_symbol_names:
            d = levenshtein_distance(t.function, sym_name)
            if d < min_dist:
                min_dist = d
                closest = sym_name

        if closest and min_dist <= 3:
            has_error = True
            print(f"Error: {t.name}: entry function '{t.function}' not found in firmware symbols")
            print(f"Did you mean '{closest}'? (Levenshtein distance: {min_dist})")

            findings.append(Finding(
                rule='autosar_entry_function_mismatch',
                severity='CRITICAL',
                tag='[STATIC]',
                message=(
                    f"Error: {t.name}: entry function '{t.function}' not found in firmware symbols.\n"
                    f"  Did you mean '{closest}'? (Levenshtein distance: {min_dist})\n"
                    f"  Task '{t.name}' is excluded from schedulability analysis."
                ),
                fix=f"Update schedule.json: change entry_function from '{t.function}' to '{closest}'."
            ))
            # Task is excluded from valid_tasks for schedulability analysis
        else:
            # Not a typo of an existing firmware symbol, retain for standard heuristic handling
            valid_tasks.append(t)

    return valid_tasks, findings, has_error

