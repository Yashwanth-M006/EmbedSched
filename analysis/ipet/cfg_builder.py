"""
analysis/ipet/cfg_builder.py — Control Flow Graph (CFG) Construction
for ARM Cortex-M Thumb/Thumb-2 disassembly.

Implements Phase 1 (instruction stream extraction) & Phase 2 (CFG builder):
  - Function instruction extraction from ELF via pyelftools + Capstone
  - Leader identification (entry, branch targets, post-branch instructions)
  - Basic block construction and edge classification
  - Back-edge detection via DFS cycle detection to identify loop headers
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import os
import re
from typing import Dict, List, Optional, Set, Tuple

import capstone
from capstone import arm
from elftools.elf.elffile import ELFFile


class EdgeType(Enum):
    FALL_THROUGH = auto()
    BRANCH_TAKEN = auto()
    BRANCH_UNCONDITIONAL = auto()
    RETURN = auto()


@dataclass
class Instruction:
    address: int
    mnemonic: str       # lowercase, e.g. "ldr", "udiv", "beq"
    op_str: str         # operand string
    size: int           # instruction size in bytes (2 or 4)
    raw_bytes: bytes    # raw machine code bytes

    def __str__(self) -> str:
        return f"0x{self.address:08x}: {self.mnemonic} {self.op_str}".strip()


@dataclass
class CFGEdge:
    src_id: str
    dst_id: str
    edge_type: EdgeType
    cost_cycles: int = 0   # populated in Phase 4c


@dataclass
class BasicBlock:
    id: str                            # canonical: f"BB_{address:08x}"
    address: int
    instructions: List[Instruction] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    is_loop_header: bool = False
    loop_bound: Optional[int] = None
    loop_id: Optional[str] = None      # e.g. "LOOP_0x08004214"

    @property
    def end_address(self) -> int:
        if not self.instructions:
            return self.address
        last = self.instructions[-1]
        return last.address + last.size

    @property
    def size_bytes(self) -> int:
        return sum(insn.size for insn in self.instructions)


@dataclass
class FunctionCFG:
    name: str
    entry_bb: str
    exit_bbs: List[str]
    blocks: Dict[str, BasicBlock]
    edges: List[CFGEdge]
    back_edges: Set[Tuple[str, str]]
    is_reducible: bool = True
    irreducible_loops: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# ARM Thumb/Thumb-2 Instruction Classification
# ─────────────────────────────────────────────────────────────────────────────

CONDITIONAL_BRANCH_PREFIXES = (
    'beq', 'bne', 'blt', 'bgt', 'ble', 'bge',
    'blo', 'bhi', 'bls', 'bhs', 'bmi', 'bpl',
    'bvs', 'bvc', 'bcc', 'bcs',
)

CONDITIONAL_BRANCHES = set(CONDITIONAL_BRANCH_PREFIXES) | {
    p + '.w' for p in CONDITIONAL_BRANCH_PREFIXES
} | {'cbz', 'cbnz'}

UNCONDITIONAL_BRANCHES = {'b', 'b.w'}
CALL_BRANCHES = {'bl', 'bl.w', 'blx', 'blx.w'}
TABLE_BRANCHES = {'tbb', 'tbh'}


def is_conditional_branch(mnemonic: str) -> bool:
    m = mnemonic.lower()
    return m in CONDITIONAL_BRANCHES


def is_unconditional_branch(mnemonic: str) -> bool:
    m = mnemonic.lower()
    return m in UNCONDITIONAL_BRANCHES


def is_call_instruction(mnemonic: str) -> bool:
    m = mnemonic.lower()
    return m in CALL_BRANCHES


def is_return_instruction(insn: Instruction) -> bool:
    """
    Checks if an instruction returns from the current subroutine:
      - bx lr
      - pop {..., pc}
      - ldm/ldmia/ldmfd ..., {..., pc}
      - mov pc, lr
    """
    m = insn.mnemonic.lower()
    ops = insn.op_str.lower().replace(" ", "")

    if m == 'bx' and 'lr' in ops:
        return True
    if m in ('pop', 'ldm', 'ldmia', 'ldmfd', 'ldmea', 'ldmdb') and 'pc' in ops:
        return True
    if m == 'mov' and ops.startswith('pc,lr'):
        return True
    return False


def extract_branch_target(insn: Instruction, cs_insn: Optional[capstone.CsInsn] = None) -> Optional[int]:
    """
    Extracts numerical branch target address from an instruction.
    Uses Capstone operand detail if available, falls back to parsing op_str.
    """
    if cs_insn is not None and len(cs_insn.operands) > 0:
        for op in cs_insn.operands:
            if op.type == arm.ARM_OP_IMM:
                return op.imm & ~1

    # Fallback regex search on op_str
    # Matches patterns like "#0x800032a", "0x800032a", "#134218538"
    match = re.search(r'#(?:0x)?([0-9a-fA-F]+)|(?:0x)([0-9a-fA-F]+)', insn.op_str)
    if match:
        val_str = match.group(1) or match.group(2)
        try:
            val = int(val_str, 16 if ('0x' in insn.op_str or any(c in 'abcdefABCDEF' for c in val_str)) else 10)
            return val & ~1
        except ValueError:
            pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Disassembly Parser
# ─────────────────────────────────────────────────────────────────────────────

def extract_instructions_from_elf(
    elf_path: str,
    target_function: Optional[str] = None
) -> Dict[str, List[Instruction]]:
    """
    Parses ELF binary using pyelftools and disassembles functions with Capstone.
    Returns mapping: function_name -> List[Instruction].
    """
    if not os.path.exists(elf_path):
        raise FileNotFoundError(f"ELF file not found: {elf_path}")

    results: Dict[str, List[Instruction]] = {}

    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab')
        if not symtab:
            # Fall back to dynamic symbol table if stripped
            symtab = elf.get_section_by_name('.dynsym')
        if not symtab:
            raise ValueError(f"No symbol table found in ELF: {elf_path}")

        # Collect symbols: function name -> (addr, size)
        symbols: Dict[str, Tuple[int, int]] = {}
        addr_list: List[Tuple[int, int, str]] = []

        for sym in symtab.iter_symbols():
            st_type = sym['st_info']['type']
            name = sym.name
            if not name or name.startswith('$'):  # skip ARM mapping symbols ($a, $t, $d)
                continue
            if st_type in ('STT_FUNC', 'STT_NOTYPE') and sym['st_value'] != 0:
                raw_addr = sym['st_value']
                addr = raw_addr & ~1  # clear Thumb bit
                size = sym['st_size']
                symbols[name] = (addr, size)
                addr_list.append((addr, size, name))

        addr_list.sort(key=lambda x: x[0])

        # Initialize Capstone disassembler (ARM Thumb mode)
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        md.detail = True

        # Map executable sections
        exec_sections = [s for s in elf.iter_sections() if s['sh_flags'] & 0x4]

        # Determine functions to process
        funcs_to_process = [target_function] if target_function else list(symbols.keys())

        for fname in funcs_to_process:
            if fname not in symbols:
                continue
            faddr, fsize = symbols[fname]

            # Find matching section
            sec = None
            for s in exec_sections:
                if s['sh_addr'] <= faddr < s['sh_addr'] + s['sh_size']:
                    sec = s
                    break
            if not sec:
                continue

            # If size is 0, estimate size using distance to next symbol
            if fsize == 0:
                cur_idx = [i for i, item in enumerate(addr_list) if item[0] == faddr and item[2] == fname]
                if cur_idx and cur_idx[0] + 1 < len(addr_list):
                    next_addr = addr_list[cur_idx[0] + 1][0]
                    fsize = min(next_addr - faddr, (sec['sh_addr'] + sec['sh_size']) - faddr)
                else:
                    fsize = (sec['sh_addr'] + sec['sh_size']) - faddr

            sec_data = sec.data()
            offset = faddr - sec['sh_addr']
            func_bytes = sec_data[offset : offset + fsize]

            insns: List[Instruction] = []
            for cs_insn in md.disasm(func_bytes, faddr):
                insn = Instruction(
                    address=cs_insn.address,
                    mnemonic=cs_insn.mnemonic.lower(),
                    op_str=cs_insn.op_str,
                    size=cs_insn.size,
                    raw_bytes=bytes(cs_insn.bytes),
                )
                insns.append(insn)

            if insns:
                results[fname] = insns

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: CFG Builder
# ─────────────────────────────────────────────────────────────────────────────

def build_cfg(function_name: str, instructions: List[Instruction]) -> FunctionCFG:
    """
    Builds the Control Flow Graph (CFG) of basic blocks for a single function.
    Identifies basic block leaders, constructs blocks, resolves edges,
    and detects loop back-edges via DFS.
    """
    if not instructions:
        return FunctionCFG(
            name=function_name,
            entry_bb="",
            exit_bbs=[],
            blocks={},
            edges=[],
            back_edges=set(),
        )

    addr_to_insn: Dict[int, Instruction] = {i.address: i for i in instructions}
    insn_indices: Dict[int, int] = {i.address: idx for idx, i in enumerate(instructions)}

    func_start = instructions[0].address
    last_insn = instructions[-1]
    func_end = last_insn.address + last_insn.size

    # ── Step 1: Identify Leaders ──────────────────────────────────────────────
    # A leader is the first instruction of a basic block:
    #   1. First instruction in the function.
    #   2. Target of any branch instruction.
    #   3. Instruction immediately following any branch or return.
    leaders: Set[int] = {func_start}

    for idx, insn in enumerate(instructions):
        m = insn.mnemonic.lower()
        is_cond = is_conditional_branch(m)
        is_uncond = is_unconditional_branch(m)
        is_call = is_call_instruction(m)
        is_ret = is_return_instruction(insn)
        is_table = m in TABLE_BRANCHES

        if is_cond or is_uncond:
            target = extract_branch_target(insn)
            if target is not None and func_start <= target < func_end:
                if target in addr_to_insn:
                    leaders.add(target)
            # Instruction immediately following branch is a leader
            if idx + 1 < len(instructions):
                leaders.add(instructions[idx + 1].address)

        elif is_call or is_ret or is_table:
            # Instruction following call/ret is a leader
            if idx + 1 < len(instructions):
                leaders.add(instructions[idx + 1].address)

    sorted_leaders = sorted(leaders)

    # ── Step 2: Construct Basic Blocks ────────────────────────────────────────
    blocks: Dict[str, BasicBlock] = {}
    addr_to_bb: Dict[int, str] = {}

    for i, l_addr in enumerate(sorted_leaders):
        bb_id = f"BB_{l_addr:08x}"
        # End of this block is the next leader or end of instruction stream
        next_l_addr = sorted_leaders[i + 1] if i + 1 < len(sorted_leaders) else None

        bb_insns: List[Instruction] = []
        curr_idx = insn_indices[l_addr]
        while curr_idx < len(instructions):
            insn = instructions[curr_idx]
            if next_l_addr is not None and insn.address >= next_l_addr:
                break
            bb_insns.append(insn)
            addr_to_bb[insn.address] = bb_id
            curr_idx += 1

        block = BasicBlock(
            id=bb_id,
            address=l_addr,
            instructions=bb_insns,
            successors=[],
            predecessors=[],
        )
        blocks[bb_id] = block

    # ── Step 3: Construct Directed CFG Edges ──────────────────────────────────
    edges: List[CFGEdge] = []
    exit_bbs: List[str] = []

    for bb_id, bb in blocks.items():
        if not bb.instructions:
            continue
        term_insn = bb.instructions[-1]
        term_m = term_insn.mnemonic.lower()
        term_idx = insn_indices[term_insn.address]
        has_next_insn = (term_idx + 1 < len(instructions))
        next_insn_addr = instructions[term_idx + 1].address if has_next_insn else None

        if is_return_instruction(term_insn):
            # Function return
            exit_bbs.append(bb_id)

        elif is_conditional_branch(term_m):
            # 1. Taken edge
            target = extract_branch_target(term_insn)
            if target is not None and target in addr_to_bb:
                dst_id = addr_to_bb[target]
                edges.append(CFGEdge(src_id=bb_id, dst_id=dst_id, edge_type=EdgeType.BRANCH_TAKEN))
                bb.successors.append(dst_id)
                blocks[dst_id].predecessors.append(bb_id)

            # 2. Fall-through edge
            if next_insn_addr is not None and next_insn_addr in addr_to_bb:
                dst_id = addr_to_bb[next_insn_addr]
                edges.append(CFGEdge(src_id=bb_id, dst_id=dst_id, edge_type=EdgeType.FALL_THROUGH))
                bb.successors.append(dst_id)
                blocks[dst_id].predecessors.append(bb_id)
            else:
                exit_bbs.append(bb_id)

        elif is_unconditional_branch(term_m):
            target = extract_branch_target(term_insn)
            if target is not None and target in addr_to_bb:
                dst_id = addr_to_bb[target]
                edges.append(CFGEdge(src_id=bb_id, dst_id=dst_id, edge_type=EdgeType.BRANCH_UNCONDITIONAL))
                bb.successors.append(dst_id)
                blocks[dst_id].predecessors.append(bb_id)
            else:
                # Unconditional branch out of function (tail call)
                exit_bbs.append(bb_id)

        elif is_call_instruction(term_m):
            # Subroutine call: calls callee and returns to next instruction
            if next_insn_addr is not None and next_insn_addr in addr_to_bb:
                dst_id = addr_to_bb[next_insn_addr]
                edges.append(CFGEdge(src_id=bb_id, dst_id=dst_id, edge_type=EdgeType.FALL_THROUGH))
                bb.successors.append(dst_id)
                blocks[dst_id].predecessors.append(bb_id)
            else:
                exit_bbs.append(bb_id)

        else:
            # Sequential fall-through to next basic block
            if next_insn_addr is not None and next_insn_addr in addr_to_bb:
                dst_id = addr_to_bb[next_insn_addr]
                edges.append(CFGEdge(src_id=bb_id, dst_id=dst_id, edge_type=EdgeType.FALL_THROUGH))
                bb.successors.append(dst_id)
                blocks[dst_id].predecessors.append(bb_id)
            else:
                exit_bbs.append(bb_id)

    # De-duplicate successors/predecessors while preserving order
    for bb in blocks.values():
        bb.successors = list(dict.fromkeys(bb.successors))
        bb.predecessors = list(dict.fromkeys(bb.predecessors))

    exit_bbs = list(dict.fromkeys(exit_bbs))
    entry_bb = f"BB_{func_start:08x}"
    if not exit_bbs and blocks:
        # Fallback if no explicit return: the last block is an exit block
        exit_bbs = [list(blocks.keys())[-1]]

    # ── Step 4: Back-Edge Detection (Loop Headers) via DFS ───────────────────
    # Using 3-color DFS:
    #   WHITE (0): Unvisited
    #   GRAY  (1): In current DFS recursion stack
    #   BLACK (2): Completed exploration
    # An edge (u, v) where color[v] == GRAY is a back-edge, and v is the loop header.
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {bid: WHITE for bid in blocks}
    back_edges: Set[Tuple[str, str]] = set()

    def dfs(node_id: str):
        color[node_id] = GRAY
        for succ_id in blocks[node_id].successors:
            c = color.get(succ_id, BLACK)
            if c == GRAY:
                # Back-edge detected!
                back_edges.add((node_id, succ_id))
                target_block = blocks[succ_id]
                target_block.is_loop_header = True
                target_block.loop_id = f"LOOP_{target_block.address:08x}"
            elif c == WHITE:
                dfs(succ_id)
        color[node_id] = BLACK

    if entry_bb in blocks:
        dfs(entry_bb)

    # In case there are disconnected/unreachable components, explore them too
    for bid in blocks:
        if color[bid] == WHITE:
            dfs(bid)

    # ── Step 5: Reducibility Verification ─────────────────────────────────────
    # In a reducible control flow graph, every natural loop has a single entry
    # (the loop header) that dominates all body nodes. If any other body node has
    # predecessors outside the loop, the graph contains an irreducible loop.
    is_reducible = True
    irreducible_loops: List[str] = []

    for src_id, dst_id in back_edges:
        loop_body = {dst_id, src_id}
        queue = [src_id]
        visited = {src_id, dst_id}
        while queue:
            curr = queue.pop(0)
            for pred in blocks[curr].predecessors:
                if pred not in visited and pred in blocks:
                    visited.add(pred)
                    loop_body.add(pred)
                    queue.append(pred)

        for node in loop_body:
            if node == dst_id:
                continue
            for pred in blocks[node].predecessors:
                if pred not in loop_body:
                    is_reducible = False
                    irreducible_loops.append(f"Irreducible cycle at header {dst_id} with secondary entry at {node}")
                    break

    return FunctionCFG(
        name=function_name,
        entry_bb=entry_bb,
        exit_bbs=exit_bbs,
        blocks=blocks,
        edges=edges,
        back_edges=back_edges,
        is_reducible=is_reducible,
        irreducible_loops=irreducible_loops,
    )

