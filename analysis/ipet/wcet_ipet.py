"""
analysis/ipet/wcet_ipet.py — IPET WCET Analysis Orchestrator

Implements Phase 6 of the IPET pipeline:
  Orchestrates Phases 1 through 5 to compute the worst-case execution time (WCET)
  of an embedded function from first principles:

    ELF Disassembly (Phase 1)
           │
           ▼
    CFG Construction (Phase 2)
           │
           ▼
    Multi-Tier Loop Bound Extraction (Phase 3)
           │
           ▼
    Microarchitectural Pipeline & Memory Edge Annotation (Phase 4)
           │
           ▼
    ILP Formulation & Solution via SciPy/HiGHS (Phase 5)
           │
           ▼
    WCET Cycles & Critical Path (Phase 6)
"""

from dataclasses import dataclass, field
import os
from typing import Dict, List, Optional, Tuple, Union

from .cfg_builder import (
    FunctionCFG,
    Instruction,
    build_cfg,
    extract_instructions_from_elf,
)
from .loop_bound_extractor import (
    LoopBoundResult,
    extract_loop_bounds,
)
from .microarch.edge_annotator import annotate_edges
from .ilp_formulator import (
    IPETSolveResult,
    formulate_and_solve_ipet,
)


@dataclass
class FunctionIPETResult:
    """Complete results of IPET WCET analysis for a single function."""
    function_name: str
    wcet_cycles: int
    wcet_tag: str
    cfg: Optional[FunctionCFG] = None
    loop_bounds: Optional[LoopBoundResult] = None
    edge_costs: Optional[Dict[Tuple[str, str], int]] = None
    solve_result: Optional[IPETSolveResult] = None
    success: bool = True
    error_message: Optional[str] = None


def compute_function_ipet_wcet(
    func_name: str,
    elf_path: Optional[str] = None,
    instructions: Optional[List[Instruction]] = None,
    arch: str = "cortex-m4",
    wait_states: int = 0,
    user_loop_bounds: Optional[Dict] = None,
    opt_info_path: Optional[str] = None,
    max_loop_bound: int = 1000,
    strict_bounds: bool = False,
) -> FunctionIPETResult:
    """
    Computes true microarchitectural WCET for a single function using IPET.

    Args:
        func_name: Name of the target function (symbol name).
        elf_path: Path to firmware ELF file.
        instructions: Optional pre-disassembled instruction list.
        arch: Target architecture ('cortex-m0', 'cortex-m3', 'cortex-m4').
        wait_states: Flash wait states (0-5).
        user_loop_bounds: Explicit loop bound annotations dictionary.
        opt_info_path: Path to GCC -fopt-info log file (auto-detected if None).
        max_loop_bound: Fallback bound when loop cannot be bounded (default 1000).
        strict_bounds: If True, do not apply conservative fallback.

    Returns:
        FunctionIPETResult containing WCET cycles, confidence tag, CFG, and ILP solution.
    """
    # ── 1. Fetch Disassembly ─────────────────────────────────────────────────
    if instructions is None:
        if not elf_path or not os.path.exists(elf_path):
            return FunctionIPETResult(
                function_name=func_name,
                wcet_cycles=0,
                wcet_tag="[HEURISTIC]",
                success=False,
                error_message="ELF file not provided or not found",
            )
        try:
            insn_dict = extract_instructions_from_elf(elf_path, target_function=func_name)
            instructions = insn_dict.get(func_name)
        except Exception as exc:
            return FunctionIPETResult(
                function_name=func_name,
                wcet_cycles=0,
                wcet_tag="[HEURISTIC]",
                success=False,
                error_message=f"Disassembly extraction failed: {exc}",
            )

    if not instructions:
        return FunctionIPETResult(
            function_name=func_name,
            wcet_cycles=0,
            wcet_tag="[HEURISTIC]",
            success=False,
            error_message=f"Function '{func_name}' not found or contains no instructions",
        )

    # ── 2. Build Control Flow Graph (Phase 2) ────────────────────────────────
    cfg = build_cfg(func_name, instructions)

    # ── 3. Extract Loop Bounds (Phase 3) ─────────────────────────────────────
    loop_bounds = extract_loop_bounds(
        cfg=cfg,
        elf_path=elf_path,
        user_loop_bounds=user_loop_bounds,
        opt_info_path=opt_info_path,
        max_loop_bound=max_loop_bound,
        strict_bounds=strict_bounds,
    )

    # If unbounded loops exist in strict mode, fail safely
    if loop_bounds.unbounded_loops and strict_bounds:
        return FunctionIPETResult(
            function_name=func_name,
            wcet_cycles=0,
            wcet_tag="[UNBOUNDED]",
            cfg=cfg,
            loop_bounds=loop_bounds,
            success=False,
            error_message=f"Unbounded loops detected in strict mode: {loop_bounds.unbounded_loops}",
        )

    # ── 4. Microarchitectural Edge Annotation (Phase 4) ──────────────────────
    edge_costs = annotate_edges(cfg, arch=arch, wait_states=wait_states)

    # ── 5. Formulate and Solve ILP (Phase 5) ─────────────────────────────────
    solve_res = formulate_and_solve_ipet(cfg, edge_costs, loop_bounds)

    if not solve_res.success:
        return FunctionIPETResult(
            function_name=func_name,
            wcet_cycles=0,
            wcet_tag="[HEURISTIC]",
            cfg=cfg,
            loop_bounds=loop_bounds,
            edge_costs=edge_costs,
            solve_result=solve_res,
            success=False,
            error_message=solve_res.error_message or "ILP solver failed",
        )

    # Tag resolution:
    #   - If user annotations were used -> [IPET-ANNOTATED]
    #   - If conservative fallback was used -> [IPET-CONSERVATIVE]
    #   - If compiler/DWARF/pattern or loop-free -> [IPET]
    wcet_tag = loop_bounds.wcet_tag

    return FunctionIPETResult(
        function_name=func_name,
        wcet_cycles=solve_res.wcet_cycles,
        wcet_tag=wcet_tag,
        cfg=cfg,
        loop_bounds=loop_bounds,
        edge_costs=edge_costs,
        solve_result=solve_res,
        success=True,
    )

