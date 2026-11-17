"""
analysis/ipet/microarch/edge_annotator.py — CFG Edge Timing Annotation

Implements Phase 4c of the IPET microarchitectural timing analysis:
  Assigns exact worst-case cycle costs to each directed edge in the CFG:
    cost(edge) = branch_flush_penalty + fetch_penalty + simulate_block(dst, entry_pipeline_state)
  This models path-dependent pipeline effects (load-use stalls crossing blocks,
  taken branch flushes, and Flash prefetch buffer misses).
"""

from typing import Dict, Optional, Tuple

from ..cfg_builder import BasicBlock, CFGEdge, EdgeType, FunctionCFG, Instruction, is_call_instruction
from .memory_model import PrefetchBufferState, fetch_cost_m0, fetch_cost_m3m4
from .pipeline_model import (
    InsnClass,
    PipelineState,
    compute_instruction_cycles,
    simulate_block,
)


def _branch_flush_cycles(
    arch: str,
    edge_type: EdgeType,
    branch_insn: Optional[Instruction] = None,
) -> int:
    """
    Returns pipeline flush penalty cycles when entering a basic block via a branch.
    Sources:
      - Cortex-M0 TRM DDI0432C §3.3.3: 2 cycles
      - Cortex-M3 TRM DDI0337H (r2p1) §3.3.4:
          1 cycle for direct branch (16-bit encoding, target known at decode)
          3 cycles for 32-bit branch or target not resolved at decode
          3 cycles for indirect branch (BX reg, BLX reg)
      - Cortex-M4 TRM DDI0439D §3.3.4: 1 cycle for direct branch, 3 for indirect (BX reg)
    """
    norm_arch = arch.lower().replace("-", "").replace("_", "")
    if "m0" in norm_arch:
        return 2

    if "m3" in norm_arch:
        if edge_type in (EdgeType.BRANCH_TAKEN, EdgeType.BRANCH_UNCONDITIONAL):
            if branch_insn and branch_insn.size == 2 and not branch_insn.mnemonic.lower().startswith("bx"):
                # 16-bit direct branch encoding (known at decode)
                return 1
            # 32-bit branch or indirect branch
            return 3
        return 3

    if "m4" in norm_arch:
        if edge_type == EdgeType.BRANCH_UNCONDITIONAL:
            if branch_insn and branch_insn.mnemonic.lower().startswith("bx"):
                return 3  # Indirect branch (BX reg)
            return 1      # Direct unconditional branch (B, B.W)
        return 1          # Direct branch taken

    return 3              # Conservative default


def _compute_exit_state(bb: BasicBlock, arch: str, wait_states: int) -> PipelineState:
    """
    Simulates execution through a basic block to determine the pipeline state at its exit.
    Used for fall-through edges where the predecessor block state flows directly into successor.
    """
    curr_state = PipelineState(last_insn_class=InsnClass.ALU, loaded_reg=None, pending_stalls=0)
    for insn in bb.instructions:
        _, curr_state = compute_instruction_cycles(
            insn=insn,
            prev_state=curr_state,
            arch=arch,
            wait_states=wait_states,
            is_first_in_block=False,
            entry_via_branch=False,
        )
    return curr_state


def annotate_edges(
    cfg: FunctionCFG,
    arch: str = "cortex-m4",
    wait_states: int = 0,
) -> Dict[Tuple[str, str], int]:
    """
    Annotates each directed edge (src -> dst) in the CFG with its worst-case cycle cost:
      cost(edge) = branch_flush_penalty + fetch_penalty + simulate_block(dst, entry_state)

    Also models:
      - Call-site BL overheads (Issue 7).
      - Cortex-M3 16-bit vs 32-bit branch penalties (Issue 1).
      - Sequential Flash 16-byte boundary crossing in prefetch buffer (Issue 5).
      - Multi-register POP {..., PC} branch redirect penalties (Issue 3).
      - Intra-block and inter-block load-use hazard interlocks (Issue 2).

    Returns:
        edge_cost_table: Mapping: (src_id, dst_id) -> int cycles
    """
    norm_arch = arch.lower().replace("-", "").replace("_", "")
    is_m0 = "m0" in norm_arch
    edge_cost_table: Dict[Tuple[str, str], int] = {}

    for edge in cfg.edges:
        if edge.src_id not in cfg.blocks or edge.dst_id not in cfg.blocks:
            continue

        src_bb = cfg.blocks[edge.src_id]
        dst_bb = cfg.blocks[edge.dst_id]
        term_insn = src_bb.instructions[-1] if src_bb.instructions else None

        # ── 1. Pipeline entry state and branch flush penalty ──────────────────
        is_call_edge = term_insn is not None and is_call_instruction(term_insn.mnemonic)

        if edge.edge_type == EdgeType.FALL_THROUGH and not is_call_edge:
            # Normal fall-through: pipeline continues smoothly from predecessor exit
            entry_state = _compute_exit_state(src_bb, arch, wait_states)
            entry_via_branch = False
            branch_flush_penalty = 0

            # Prefetch buffer state continues from predecessor end address (Issue 5)
            buf_base = (src_bb.end_address - 1) & ~0xF if src_bb.instructions else 0
            buf_state = PrefetchBufferState(buffer_base_addr=buf_base, valid=True)

        elif is_call_edge:
            # Issue 7: Call site BL/BLX branch call.
            # Even though control returns to dst_bb, the BL instruction flushed
            # the pipeline, executed the subroutine, and returned with a cold prefetch buffer.
            entry_state = PipelineState(last_insn_class=InsnClass.BRANCH, loaded_reg=None, pending_stalls=0)
            entry_via_branch = True
            branch_flush_penalty = _branch_flush_cycles(arch, EdgeType.BRANCH_UNCONDITIONAL, term_insn)
            buf_state = PrefetchBufferState(buffer_base_addr=0, valid=False)

        elif edge.edge_type in (EdgeType.BRANCH_TAKEN, EdgeType.BRANCH_UNCONDITIONAL):
            # Taken branch: pipeline was flushed by the branch instruction
            entry_state = PipelineState(last_insn_class=InsnClass.BRANCH, loaded_reg=None, pending_stalls=0)
            entry_via_branch = True
            branch_flush_penalty = _branch_flush_cycles(arch, edge.edge_type, term_insn)
            buf_state = PrefetchBufferState(buffer_base_addr=0, valid=False)

        else:
            # Return edge or unknown: cold pipeline
            entry_state = PipelineState(last_insn_class=InsnClass.ALU, loaded_reg=None, pending_stalls=0)
            entry_via_branch = True
            branch_flush_penalty = _branch_flush_cycles(arch, EdgeType.BRANCH_UNCONDITIONAL, term_insn)
            buf_state = PrefetchBufferState(buffer_base_addr=0, valid=False)

        # ── 2. Instruction fetch penalty for first instruction of dst block ───
        fetch_penalty = 0
        if dst_bb.instructions:
            first_insn = dst_bb.instructions[0]
            if is_m0:
                fetch_penalty = fetch_cost_m0(first_insn, wait_states)
            else:
                fp, buf_state = fetch_cost_m3m4(first_insn.address, entry_via_branch, buf_state, wait_states)
                fetch_penalty = fp

        # ── 3. Simulate block execution under entry state & buffer state ──────
        block_cycles, _, _ = simulate_block(
            bb=dst_bb,
            entry_state=entry_state,
            arch=arch,
            wait_states=wait_states,
            entry_via_branch=entry_via_branch,
            initial_buf_state=buf_state,
        )

        total_edge_cost = branch_flush_penalty + fetch_penalty + block_cycles
        edge.cost_cycles = total_edge_cost
        edge_cost_table[(edge.src_id, edge.dst_id)] = total_edge_cost

    # ── 4. Virtual Entry Edge ("__entry__", cfg.entry_bb) ────────────────────
    if cfg.entry_bb in cfg.blocks:
        entry_bb = cfg.blocks[cfg.entry_bb]
        cold_state = PipelineState(last_insn_class=InsnClass.ALU, loaded_reg=None, pending_stalls=0)

        entry_flush_penalty = _branch_flush_cycles(arch, EdgeType.BRANCH_UNCONDITIONAL, None)
        entry_fetch = 0
        init_buf = PrefetchBufferState(0, False)
        if entry_bb.instructions:
            first_insn = entry_bb.instructions[0]
            if is_m0:
                entry_fetch = fetch_cost_m0(first_insn, wait_states)
            else:
                entry_fetch, init_buf = fetch_cost_m3m4(
                    first_insn.address,
                    is_branch_target=True,
                    buf_state=init_buf,
                    wait_states=wait_states,
                )

        entry_bb_cycles, _, _ = simulate_block(
            bb=entry_bb,
            entry_state=cold_state,
            arch=arch,
            wait_states=wait_states,
            entry_via_branch=True,
            initial_buf_state=init_buf,
        )
        edge_cost_table[("__entry__", cfg.entry_bb)] = (
            entry_flush_penalty + entry_fetch + entry_bb_cycles
        )

    return edge_cost_table
