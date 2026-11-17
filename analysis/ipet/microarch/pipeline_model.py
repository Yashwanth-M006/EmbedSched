"""
analysis/ipet/microarch/pipeline_model.py — In-Order Pipeline Simulator & Instruction Latencies

Implements Phase 4a of the IPET microarchitectural timing analysis:
  Models the execution pipeline state machine for ARM Cortex-M0, M3, and M4.
  Calculates exact instruction cycles, intra-block and inter-block load-use
  hazard stalls, multiply/divide latencies, FPU non-pipelined delays,
  POP {..., PC} branch redirect penalties, and prefetch buffer line crossings.
"""

from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import Dict, List, Optional, Tuple

from ..cfg_builder import BasicBlock, Instruction
from .memory_model import PrefetchBufferState, fetch_cost_m0, fetch_cost_m3m4


class InsnClass(Enum):
    """
    Coarse instruction classification that determines inter-instruction hazards.
    """
    ALU = auto()           # ADD, SUB, AND, ORR, LSL, MOV, etc.
    MULTIPLY = auto()      # MUL, MLA, MLS, SMULL, UMULL
    LOAD = auto()          # LDR, LDRH, LDRB, LDRSB, LDRSH, LDRD, VLDR
    STORE = auto()         # STR, STRH, STRB, STRD, VSTR
    LOAD_MULTI = auto()    # LDM, LDMIA, LDMFD, POP
    STORE_MULTI = auto()   # STM, STMIA, STMFD, PUSH
    DIVIDE = auto()        # UDIV, SDIV (M3/M4)
    FPU_FAST = auto()      # VADD, VSUB, VMUL, VCMP, VMOV (M4F - pipelined)
    FPU_SLOW = auto()      # VDIV.F32, VSQRT.F32 (fixed 14 cycles, non-pipelined)
    BRANCH = auto()        # B, BL, BLX, BX, Bcc, CBZ, CBNZ
    SYSTEM = auto()        # DMB, DSB, ISB, MRS, MSR, NOP, SEV, WFI


@dataclass(frozen=True)
class PipelineState:
    """
    The microarchitectural state carried across instructions and block boundaries.
      last_insn_class: The instruction class of the immediately preceding instruction.
      loaded_reg:      The destination register of the preceding load, if any (e.g. 'r3').
      pending_stalls:  Committed stall cycles.
    """
    last_insn_class: InsnClass = InsnClass.ALU
    loaded_reg: Optional[str] = None
    pending_stalls: int = 0

    def __eq__(self, other):
        if not isinstance(other, PipelineState):
            return False
        return (
            self.last_insn_class == other.last_insn_class
            and self.loaded_reg == other.loaded_reg
            and self.pending_stalls == other.pending_stalls
        )

    def __hash__(self):
        return hash((self.last_insn_class, self.loaded_reg, self.pending_stalls))


# ─────────────────────────────────────────────────────────────────────────────
# Base Latency Table (ARM Cortex-M0 / M3 / M4 TRMs)
# ─────────────────────────────────────────────────────────────────────────────

BASE_LATENCY: Dict[str, int] = {
    # Data Processing (1 cycle on M3/M4)
    "add": 1, "adds": 1, "adc": 1, "adcs": 1,
    "sub": 1, "subs": 1, "sbc": 1, "sbcs": 1,
    "rsb": 1, "rsbs": 1,
    "and": 1, "ands": 1, "bic": 1, "bics": 1,
    "orr": 1, "orrs": 1, "orn": 1, "orns": 1,
    "eor": 1, "eors": 1,
    "mvn": 1, "mvns": 1,
    "mov": 1, "movs": 1, "movw": 1, "movt": 1,
    "lsl": 1, "lsls": 1, "lsr": 1, "lsrs": 1,
    "asr": 1, "asrs": 1, "ror": 1, "rors": 1, "rrx": 1,
    "clz": 1,
    "cmp": 1, "cmn": 1, "tst": 1, "teq": 1,
    "adr": 1,
    "uxtb": 1, "uxth": 1, "sxtb": 1, "sxth": 1,
    "uxtb16": 1, "sxtb16": 1,
    "rev": 1, "rev16": 1, "revsh": 1,
    "pkhbt": 1, "pkhtb": 1,
    "sel": 1, "ssat": 1, "usat": 1,
    # Multiply
    "mul": 1, "muls": 1,     # 1 cycle on M3/M4, up to 32 on M0
    "mla": 2, "mlas": 2,     # 2 cycles on M3/M4
    "mls": 2,
    "smull": 1, "umull": 1,
    "smlal": 1, "umlal": 1,
    "smulbb": 1, "smulbt": 1, "smultb": 1, "smultt": 1,
    "smuad": 1, "smusd": 1,
    # Divide
    "udiv": 12, "sdiv": 12,  # 2-12 cycles on M3/M4; worst-case 12
    # Single Loads (2 cycles latency to result)
    "ldr": 2, "ldrh": 2, "ldrb": 2, "ldrsb": 2, "ldrsh": 2,
    "ldrd": 2,
    # Stores
    "str": 2, "strh": 2, "strb": 2, "strd": 2,
    # Multiple Loads / Stores (-1 sentinel: 1 + number of registers)
    "ldm": -1, "ldmia": -1, "ldmfd": -1, "ldmdb": -1, "ldmea": -1,
    "stm": -1, "stmia": -1, "stmfd": -1, "stmdb": -1, "stmea": -1,
    "push": -1, "pop": -1,
    # Branches (pipeline latency)
    "b": 1, "bl": 3, "blx": 3, "bx": 1,
    "beq": 1, "bne": 1, "blt": 1, "bgt": 1,
    "ble": 1, "bge": 1, "blo": 1, "bhi": 1,
    "bls": 1, "bhs": 1, "bmi": 1, "bpl": 1,
    "bvs": 1, "bvc": 1, "bcc": 1, "bcs": 1,
    "cbz": 1, "cbnz": 1,
    "tbb": 2, "tbh": 2,
    # FPU Single-Precision (Cortex-M4F - Pipelined, 1-2 cycles, non-blocking)
    "vadd": 1, "vsub": 1, "vmul": 1, "vmla": 1, "vmls": 1,
    "vabs": 1, "vneg": 1, "vcvt": 1, "vcmp": 1, "vcmpe": 1,
    "vmov": 1, "vmrs": 1, "vmsr": 1,
    "vldr": 2, "vstr": 2,
    "vldm": -1, "vstm": -1,
    # FPU Non-Pipelined (fixed 14 cycles, Cortex-M4 TRM Table 3-6, core blocking)
    "vdiv": 14, "vsqrt": 14,
    # System / Barriers
    "nop": 1, "sev": 1, "wfi": 1, "wfe": 1,
    "dmb": 4, "dsb": 4, "isb": 4,
    "mrs": 2, "msr": 2,
    "bkpt": 2, "svc": 10,
}


def classify_instruction(mnemonic: str) -> InsnClass:
    """Classifies an instruction mnemonic into an InsnClass."""
    m = mnemonic.lower().split('.')[0]
    if m in ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd', 'vldr'):
        return InsnClass.LOAD
    if m in ('ldm', 'ldmia', 'ldmfd', 'pop'):
        return InsnClass.LOAD_MULTI
    if m in ('str', 'strh', 'strb', 'strd', 'vstr', 'stm', 'stmia', 'stmfd', 'push'):
        return InsnClass.STORE
    if m in ('udiv', 'sdiv'):
        return InsnClass.DIVIDE
    if m in ('vdiv', 'vsqrt'):
        return InsnClass.FPU_SLOW
    if m.startswith('v'):
        return InsnClass.FPU_FAST
    if m in ('mul', 'muls', 'mla', 'mls', 'smull', 'umull', 'smlal', 'umlal'):
        return InsnClass.MULTIPLY
    if m in ('b', 'bl', 'blx', 'bx', 'cbz', 'cbnz', 'tbb', 'tbh') or m in (
        'beq', 'bne', 'blt', 'bgt', 'ble', 'bge', 'blo', 'bhi', 'bls', 'bhs',
        'bmi', 'bpl', 'bvs', 'bvc', 'bcc', 'bcs'
    ):
        return InsnClass.BRANCH
    if m in ('dmb', 'dsb', 'isb', 'mrs', 'msr', 'nop', 'sev', 'wfi', 'wfe', 'svc'):
        return InsnClass.SYSTEM
    return InsnClass.ALU


def extract_dst_register(insn: Instruction) -> Optional[str]:
    """Extracts the destination register from a load instruction if possible."""
    parts = insn.op_str.split(',')
    if parts:
        candidate = parts[0].strip().lower()
        if re.match(r'^[r|s|d]\d+$|^sp$|^lr$|^pc$', candidate):
            return candidate
    return None


def instruction_reads_register(insn: Instruction, reg: Optional[str]) -> bool:
    """Checks if an instruction reads the specified register as an operand."""
    if not reg:
        return False
    op_lower = insn.op_str.lower()
    # Check word boundary for register name
    return bool(re.search(r'\b' + re.escape(reg) + r'\b', op_lower))


def compute_instruction_cycles(
    insn: Instruction,
    prev_state: PipelineState,
    arch: str = "cortex-m4",
    wait_states: int = 0,
    is_first_in_block: bool = False,
    entry_via_branch: bool = False,
) -> Tuple[int, PipelineState]:
    """
    Computes worst-case instruction cycles considering pipeline stalls.

    Models:
      1. Intra-block and inter-block load-use hazard stalls.
      2. Multi-register LDM/POP unstacking penalties with PC redirection.
      3. Architecture-specific multiply (M0: 32 vs M4: 1 cycle).
      4. Hardware divide (M3/M4: 12 cycles worst case).
      5. FPU non-pipelined core blocking operations (VDIV/VSQRT: 14 cycles).

    Returns:
        (cycles, next_pipeline_state)
    """
    norm_arch = arch.lower().replace("-", "").replace("_", "")
    mnem = insn.mnemonic.lower().split('.')[0]
    out_class = classify_instruction(insn.mnemonic)

    # ── 1. Base Latency ───────────────────────────────────────────────────────
    if BASE_LATENCY.get(mnem) == -1:
        # Multiple registers: LDM/STM/PUSH/POP -> 1 + count(regs)
        regs_count = max(1, insn.op_str.count(',') + 1)
        base = 1 + regs_count

        # Issue 3: If PC is in register list (POP {..., PC}), add branch redirect penalty
        if 'pc' in insn.op_str.lower():
            if "m0" in norm_arch:
                base += 2
            elif "m3" in norm_arch or "m4" in norm_arch:
                base += 3
    else:
        base = BASE_LATENCY.get(mnem, 2)

    # ── 2. Load-Use Hazard Stall (Intra-Block & Inter-Block) ───────────────────
    # If the preceding instruction was a LOAD and the current instruction
    # reads the loaded register, inject 1 stall cycle.
    stall_cycles = 0
    if prev_state.last_insn_class in (InsnClass.LOAD, InsnClass.LOAD_MULTI):
        if prev_state.loaded_reg:
            if instruction_reads_register(insn, prev_state.loaded_reg):
                stall_cycles = 1
        else:
            # Conservative fallback if destination register could not be parsed
            stall_cycles = 1

    # ── 3. Architecture-Specific Overrides ─────────────────────────────────────
    if "m0" in norm_arch:
        if mnem in ("mul", "muls"):
            base = 32
        elif mnem in ("udiv", "sdiv"):
            base = 10  # Exception / trap on M0

    elif "m4" in norm_arch or "m3" in norm_arch:
        if mnem in ("udiv", "sdiv"):
            base = 12
        elif mnem in ("vdiv", "vsqrt"):
            base = 14

    # Determine loaded destination register for next instruction
    new_loaded_reg = extract_dst_register(insn) if out_class == InsnClass.LOAD else None

    next_state = PipelineState(
        last_insn_class=out_class,
        loaded_reg=new_loaded_reg,
        pending_stalls=0,
    )
    return (base + stall_cycles, next_state)


def simulate_block(
    bb: BasicBlock,
    entry_state: PipelineState,
    arch: str = "cortex-m4",
    wait_states: int = 0,
    entry_via_branch: bool = False,
    initial_buf_state: Optional[PrefetchBufferState] = None,
) -> Tuple[int, PipelineState, PrefetchBufferState]:
    """
    Simulates a basic block through the pipeline model.
    Tracks both intra-block load-use hazards and intra-block 16-byte prefetch
    buffer line crossings.

    Returns:
        (total_cycles, exit_pipeline_state, exit_prefetch_buffer_state)
    """
    buf_state = initial_buf_state or PrefetchBufferState(0, False)
    if not bb.instructions:
        return (0, entry_state, buf_state)

    total_cycles = 0
    curr_state = entry_state
    norm_arch = arch.lower().replace("-", "").replace("_", "")
    is_m0 = "m0" in norm_arch

    for idx, insn in enumerate(bb.instructions):
        is_first = (idx == 0)

        # Intra-block instruction fetch evaluation (Issue 5)
        if not is_first:
            if is_m0:
                fetch_p = fetch_cost_m0(insn, wait_states)
                total_cycles += fetch_p
            else:
                fetch_p, buf_state = fetch_cost_m3m4(
                    insn.address,
                    is_branch_target=False,
                    buf_state=buf_state,
                    wait_states=wait_states,
                )
                total_cycles += fetch_p

        cyc, next_state = compute_instruction_cycles(
            insn=insn,
            prev_state=curr_state,
            arch=arch,
            wait_states=wait_states,
            is_first_in_block=is_first,
            entry_via_branch=(entry_via_branch and is_first),
        )
        total_cycles += cyc
        curr_state = next_state

    return (total_cycles, curr_state, buf_state)
