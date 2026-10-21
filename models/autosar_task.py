from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class Resource:
    name: str
    type: str  # e.g., "mutex", "spinlock"
    accessed_by: List[str] = field(default_factory=list)
    ceiling: float = float('inf')  # Computed priority ceiling (highest priority / lowest integer of any task accessing it)
    critical_section_us: float = 5.0  # Assumed default critical section length (could be derived from call graph)
    task_critical_sections_us: Dict[str, float] = field(default_factory=dict)
    # acquisition_order: {task_name: int} — the sequence order in which a task acquires this lock.
    # e.g. {"Task_A": 1, "Task_B": 2} means Task_A grabs it first, Task_B second.
    # Used to detect global lock-ordering inversions (deadlock risk) across tasks.
    acquisition_order: Dict[str, int] = field(default_factory=dict)

@dataclass
class InterCoreChannel:
    from_task: str
    to_task: str
    shared_region: str
    sync_mechanism: str
    latency_us: float = 0.0  # Computed from chip profile
    write_latency_us: float = 0.0  # Optional explicit write/data latency

@dataclass
class CoreConfig:
    id: int
    algorithm: str = "RM"  # RM, DM, EDF

@dataclass
class AutosarTask:
    """
    Represents a single AUTOSAR OS task with all parameters needed
    for schedulability analysis.

    period_us  : Task period in microseconds (release every T us)
    deadline_us: Relative deadline in microseconds. For constrained-deadline
                 systems deadline_us <= period_us.
    priority   : Fixed priority (lower integer = higher priority in this engine:
                 1 = highest priority, consistent with RM/DM scheduling literature
                 and PCP ceiling calculations; 255 = lowest/idle).
    core_id    : Core assignment for multi-core analysis (0-based).
    function   : Name of the firmware function that is the task body entry point.
                 Used to look up WCET from timing model / call graph.
    """
    name: str
    period_us: float
    deadline_us: float
    priority: int
    core_id: int
    function: str  # maps to a symbol name in the ELF
    resources: List[str] = field(default_factory=list)
    stack_bytes: int = 0

    # Filled in by wcet_extractor after analysis
    wcet_us: float = 0.0
    wcet_tag: str = "[CALCULATED]"   # [CALCULATED] or [SIMULATED]
    wcet_cycles: int = 0
    wcet_call_chain: List[str] = field(default_factory=list)

    # Filled in by rta_engine
    wcrt_us: float = 0.0             # Worst-case response time
    blocking_us: float = 0.0         # Priority inversion blocking time
    blocking_source_task: Optional[str] = None
    blocking_source_res: Optional[str] = None
    schedulable: Optional[bool] = None  # None = not yet analysed
    margin_us: float = 0.0           # deadline_us - wcrt_us

    # ISR pseudo-tasks get this set True
    is_isr: bool = False

