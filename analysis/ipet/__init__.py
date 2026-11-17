"""
IPET (Implicit Path Enumeration Technique) WCET Analysis Package
for ARM Cortex-M microcontrollers.
"""

from .cfg_builder import (
    EdgeType,
    Instruction,
    CFGEdge,
    BasicBlock,
    FunctionCFG,
    build_cfg,
    extract_instructions_from_elf,
)
from .loop_bound_extractor import (
    LoopBoundResult,
    OptInfoLoopRecord,
    extract_loop_bounds,
    detect_constant_loop_bound,
    extract_dwarf_loop_bounds,
    normalize_user_loop_bounds,
    parse_gcc_opt_info,
    correlate_opt_info_to_cfg,
)
from .microarch import (
    InsnClass,
    PipelineState,
    compute_instruction_cycles,
    simulate_block,
    annotate_edges,
)
from .ilp_formulator import (
    IPETSolveResult,
    formulate_and_solve_ipet,
)
from .wcet_ipet import (
    FunctionIPETResult,
    compute_function_ipet_wcet,
)
from .visualizer import visualize_cfg

__all__ = [
    "EdgeType",
    "Instruction",
    "CFGEdge",
    "BasicBlock",
    "FunctionCFG",
    "build_cfg",
    "extract_instructions_from_elf",
    "LoopBoundResult",
    "OptInfoLoopRecord",
    "extract_loop_bounds",
    "detect_constant_loop_bound",
    "extract_dwarf_loop_bounds",
    "normalize_user_loop_bounds",
    "parse_gcc_opt_info",
    "correlate_opt_info_to_cfg",
    "InsnClass",
    "PipelineState",
    "compute_instruction_cycles",
    "simulate_block",
    "annotate_edges",
    "IPETSolveResult",
    "formulate_and_solve_ipet",
    "FunctionIPETResult",
    "compute_function_ipet_wcet",
    "visualize_cfg",
]
