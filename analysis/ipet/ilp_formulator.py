"""
analysis/ipet/ilp_formulator.py — Integer Linear Programming Formulator for IPET

Implements Phase 5 of the IPET microarchitectural timing analysis:
  Translates the annotated CFG (from Phase 4) and loop bounds (from Phase 3)
  into an Integer Linear Program (ILP):

    Maximize:
      WCET = sum_{e in E} cost(e) * x_e

    Subject to:
      1. Flow conservation at every basic block v:
           sum_{u: (u, v) in E} x_(u, v) - sum_{w: (v, w) in E} x_(v, w) = 0
      2. Entry and exit normalization:
           x_("__entry__", entry_bb) = 1
           sum_{x in exit_bbs} x_(x, "__exit__") = 1
      3. Loop back-edge capacity bounds for each natural loop header h:
           sum_{(u, h) in BackEdges(h)} x_(u, h) <= N_h * sum_{(p, h) not in BackEdges(h)} x_(p, h)
      4. Integrality and non-negativity:
           x_e in Z_{>= 0} for all e in E

Uses scipy.optimize.milp (HiGHS solver bundled in SciPy) — no external binaries required.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np
from scipy.optimize import LinearConstraint, Bounds, milp

from .cfg_builder import FunctionCFG
from .loop_bound_extractor import LoopBoundResult


@dataclass
class IPETSolveResult:
    """Result of solving the IPET ILP for a function."""
    wcet_cycles: int
    edge_counts: Dict[Tuple[str, str], int] = field(default_factory=dict)
    block_counts: Dict[str, int] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    critical_edges: List[Tuple[str, str]] = field(default_factory=list)
    solver_status: str = "optimal"
    success: bool = True
    error_message: Optional[str] = None


def formulate_and_solve_ipet(
    cfg: FunctionCFG,
    edge_costs: Dict[Tuple[str, str], int],
    loop_bounds: LoopBoundResult,
    timeout_sec: float = 30.0,
) -> IPETSolveResult:
    """
    Formulates and solves the IPET ILP over the annotated CFG edges.

    Args:
        cfg: Function CFG with basic blocks, edges, entry/exit blocks, and back-edges.
        edge_costs: Mapping of (src_id, dst_id) -> worst-case cycle cost (from edge_annotator).
        loop_bounds: LoopBoundResult containing loop bounds per loop header.
        timeout_sec: Solver time limit in seconds.

    Returns:
        IPETSolveResult containing total WCET cycles, edge/block counts, and critical path.
    """
    if not cfg.blocks:
        return IPETSolveResult(
            wcet_cycles=0,
            solver_status="empty_cfg",
            success=True,
        )

    # ── 1. Index All Directed Edges (Decision Variables x_e) ─────────────────
    # Variable indices:
    #   - Normal edges from cfg.edges
    #   - Virtual entry edge: ("__entry__", cfg.entry_bb)
    #   - Virtual exit edges: (exit_bb, "__exit__") for all exit_bb in cfg.exit_bbs
    all_edges: List[Tuple[str, str]] = []
    seen_edges: Set[Tuple[str, str]] = set()

    # Virtual entry edge
    v_entry = ("__entry__", cfg.entry_bb)
    all_edges.append(v_entry)
    seen_edges.add(v_entry)

    # Normal CFG edges
    for edge in cfg.edges:
        e = (edge.src_id, edge.dst_id)
        if e not in seen_edges:
            all_edges.append(e)
            seen_edges.add(e)

    # Virtual exit edges (one for each exit basic block)
    exit_bbs = cfg.exit_bbs if cfg.exit_bbs else [list(cfg.blocks.keys())[-1]]
    v_exits: List[Tuple[str, str]] = []
    for x_bb in exit_bbs:
        e = (x_bb, "__exit__")
        if e not in seen_edges:
            all_edges.append(e)
            seen_edges.add(e)
            v_exits.append(e)

    num_vars = len(all_edges)
    edge_to_idx: Dict[Tuple[str, str], int] = {e: i for i, e in enumerate(all_edges)}

    # ── 2. Construct Objective Vector c (scipy.optimize.milp minimizes c^T x) ─
    # To maximize sum(cost * x), minimize -sum(cost * x).
    c = np.zeros(num_vars, dtype=np.float64)
    for i, e in enumerate(all_edges):
        cost = edge_costs.get(e, 0)
        c[i] = -float(cost)

    # ── 3. Flow Conservation Constraints (A_eq * x = b_eq) ───────────────────
    # For each basic block v in cfg.blocks:
    #   sum_{u: (u, v) in E} x_(u, v) - sum_{w: (v, w) in E} x_(v, w) = 0
    in_edges_by_node: Dict[str, List[int]] = {b: [] for b in cfg.blocks}
    out_edges_by_node: Dict[str, List[int]] = {b: [] for b in cfg.blocks}

    for i, (u, v) in enumerate(all_edges):
        if v in in_edges_by_node:
            in_edges_by_node[v].append(i)
        if u in out_edges_by_node:
            out_edges_by_node[u].append(i)

    eq_rows: List[np.ndarray] = []
    eq_b: List[float] = []

    # Node flow conservation
    for b in cfg.blocks:
        row = np.zeros(num_vars, dtype=np.float64)
        for in_idx in in_edges_by_node[b]:
            row[in_idx] += 1.0
        for out_idx in out_edges_by_node[b]:
            row[out_idx] -= 1.0
        eq_rows.append(row)
        eq_b.append(0.0)

    # Entry edge must equal 1: x_("__entry__", entry_bb) = 1
    entry_row = np.zeros(num_vars, dtype=np.float64)
    entry_row[edge_to_idx[v_entry]] = 1.0
    eq_rows.append(entry_row)
    eq_b.append(1.0)

    # Total exit flow must equal 1: sum_{x} x_(x, "__exit__") = 1
    if v_exits:
        exit_row = np.zeros(num_vars, dtype=np.float64)
        for vex in v_exits:
            exit_row[edge_to_idx[vex]] = 1.0
        eq_rows.append(exit_row)
        eq_b.append(1.0)

    # ── 4. Loop Capacity Constraints (A_ub * x <= b_ub) ──────────────────────
    # For each natural loop header h with back-edges B_h = {(u, h)}:
    #   sum_{(u, h) in B_h} x_(u, h) <= N_h * sum_{(p, h) not in B_h} x_(p, h)
    # Rearranged:
    #   sum_{(u, h) in B_h} x_(u, h) - N_h * sum_{(p, h) not in B_h} x_(p, h) <= 0
    ub_rows: List[np.ndarray] = []
    ub_b: List[float] = []

    # Group back-edges by loop header
    header_to_backedges: Dict[str, List[Tuple[str, str]]] = {}
    for src_id, dst_id in cfg.back_edges:
        header_to_backedges.setdefault(dst_id, []).append((src_id, dst_id))

    for header_id, b_edges in header_to_backedges.items():
        if header_id not in cfg.blocks:
            continue
        # Get bound for this loop header
        n_h = loop_bounds.bounds.get(header_id, 1000)

        # Inflow edges into header
        header_in_indices = in_edges_by_node.get(header_id, [])
        back_edge_indices = set()
        for be in b_edges:
            if be in edge_to_idx:
                back_edge_indices.add(edge_to_idx[be])

        row = np.zeros(num_vars, dtype=np.float64)
        for in_idx in header_in_indices:
            if in_idx in back_edge_indices:
                row[in_idx] += 1.0
            else:
                row[in_idx] -= float(n_h)

        ub_rows.append(row)
        ub_b.append(0.0)

    # ── 5. Build SciPy LinearConstraint and Bounds ───────────────────────────
    # Combine constraints into LinearConstraint(A, lb, ub)
    constraints = []
    
    if eq_rows:
        A_eq = np.array(eq_rows, dtype=np.float64)
        b_eq = np.array(eq_b, dtype=np.float64)
        constraints.append(LinearConstraint(A_eq, lb=b_eq, ub=b_eq))

    if ub_rows:
        A_ub = np.array(ub_rows, dtype=np.float64)
        b_ub = np.array(ub_b, dtype=np.float64)
        # ub_rows * x <= b_ub  =>  -inf <= ub_rows * x <= b_ub
        constraints.append(LinearConstraint(A_ub, lb=-np.inf, ub=b_ub))

    # All edge counts are non-negative integers: x_e >= 0
    integrality = np.ones(num_vars, dtype=np.int32)
    bounds = Bounds(lb=0.0, ub=np.inf)

    # ── 6. Solve via HiGHS ───────────────────────────────────────────────────
    try:
        options = {"time_limit": timeout_sec}
        res = milp(
            c=c,
            integrality=integrality,
            bounds=bounds,
            constraints=constraints,
            options=options,
        )
    except Exception as exc:
        return IPETSolveResult(
            wcet_cycles=0,
            solver_status="solver_exception",
            success=False,
            error_message=str(exc),
        )

    if not res.success or res.x is None:
        return IPETSolveResult(
            wcet_cycles=0,
            solver_status=res.status_message if hasattr(res, 'status_message') else "infeasible",
            success=False,
            error_message=f"MILP solver failed: status {res.status}",
        )

    # ── 7. Extract Results and Reconstruct Critical Path ─────────────────────
    x_sol = np.round(res.x).astype(int)
    wcet_cycles = int(round(-res.fun))

    edge_counts: Dict[Tuple[str, str], int] = {}
    critical_edges: List[Tuple[str, str]] = []
    for i, e in enumerate(all_edges):
        cnt = int(x_sol[i])
        edge_counts[e] = cnt
        if cnt > 0 and e[0] != "__entry__" and e[1] != "__exit__":
            critical_edges.append(e)

    # Compute block execution counts
    block_counts: Dict[str, int] = {b: 0 for b in cfg.blocks}
    for (u, v), cnt in edge_counts.items():
        if v in block_counts:
            block_counts[v] += cnt

    # Reconstruct critical path: ordered blocks traversed with non-zero count
    critical_path = _extract_critical_path(cfg, edge_counts)

    return IPETSolveResult(
        wcet_cycles=wcet_cycles,
        edge_counts=edge_counts,
        block_counts=block_counts,
        critical_path=critical_path,
        critical_edges=critical_edges,
        solver_status="optimal",
        success=True,
    )


def _extract_critical_path(
    cfg: FunctionCFG,
    edge_counts: Dict[Tuple[str, str], int],
) -> List[str]:
    """
    Extracts a representative critical path (list of basic block IDs)
    starting from entry_bb and following non-zero flow edges to exit.
    """
    if not cfg.entry_bb or cfg.entry_bb not in cfg.blocks:
        return []

    visited: Set[str] = set()
    path: List[str] = []
    curr = cfg.entry_bb

    while curr and curr not in visited:
        visited.add(curr)
        path.append(curr)
        # Find successor edge with highest execution count
        best_succ = None
        best_count = 0
        for succ in cfg.blocks[curr].successors:
            cnt = edge_counts.get((curr, succ), 0)
            if cnt > best_count:
                best_count = cnt
                best_succ = succ
        curr = best_succ

    return path

