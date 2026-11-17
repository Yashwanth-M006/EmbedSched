"""
analysis/ipet/microarch/memory_model.py — Flash Prefetch Buffer & Memory Hierarchy Latencies

Implements Phase 4b of the IPET microarchitectural timing analysis:
  Models the 128-bit wide AHB Flash prefetch buffer for Cortex-M3/M4,
  Von Neumann bus fetch timings for Cortex-M0, and data bus access wait states.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

from ..cfg_builder import Instruction

PREFETCH_BUFFER_WIDTH_BYTES = 16   # 128-bit wide Flash interface (Cortex-M3/M4)


@dataclass(frozen=True)
class PrefetchBufferState:
    """
    State of the instruction prefetch buffer at a basic block boundary.
    Cortex-M3 and M4 load 128 bits (16 bytes = 4x Thumb-2 or 8x Thumb-16) per transaction.
    """
    buffer_base_addr: int = 0
    valid: bool = False


# Data region latencies (cycles)
DATA_LATENCY_CYCLES: Dict[str, int] = {
    "SRAM": 1,        # 0 wait states, 1 cycle
    "CCM": 1,         # Core-coupled memory, 0 wait states
    "DTCM": 1,        # Data tightly-coupled memory, 0 wait states
    "PERIPHERAL": 2,  # AHB bus peripheral
    "APB": 4,         # APB bus peripheral through bus bridge
}


def fetch_cost_m3m4(
    insn_addr: int,
    is_branch_target: bool,
    buf_state: PrefetchBufferState,
    wait_states: int,
) -> Tuple[int, PrefetchBufferState]:
    """
    Computes instruction fetch latency for Cortex-M3/M4 with 128-bit prefetch buffer.

    Properties (STM32F4 Reference Manual RM0090 §3.4):
      - 128-bit wide AHB transaction fetches up to 16 bytes at once.
      - Sequential code: instructions residing within the same 128-bit window are free (0 cycles).
      - Branch targets / cold buffer: requires a fresh 128-bit transaction costing (1 + wait_states).
      - Sequential boundary crossing: crossing to the next 16-byte boundary costs (1 + wait_states).

    Returns:
        (extra_cycles_for_fetch, new_buffer_state)
    """
    new_base = insn_addr & ~(PREFETCH_BUFFER_WIDTH_BYTES - 1)

    if not buf_state.valid or is_branch_target:
        # Cold fetch: 1 AHB bus cycle + wait_states penalty
        return (1 + wait_states, PrefetchBufferState(buffer_base_addr=new_base, valid=True))

    buf_end = buf_state.buffer_base_addr + PREFETCH_BUFFER_WIDTH_BYTES
    if buf_state.buffer_base_addr <= insn_addr < buf_end:
        # Buffer hit: already pre-buffered
        return (0, buf_state)

    # Sequential line crossing: requires fetching next 128-bit buffer line
    return (1 + wait_states, PrefetchBufferState(buffer_base_addr=new_base, valid=True))


def fetch_cost_m0(insn: Instruction, wait_states: int) -> int:
    """
    Computes instruction fetch latency for Cortex-M0 (ARMv6-M).
    Cortex-M0 has a Von Neumann single bus and no instruction prefetch buffer.
    Every instruction fetch requires 1 bus transaction per 16-bit word.

    Returns:
        cycles_consumed_by_fetch
    """
    halfwords = max(1, insn.size // 2)
    return halfwords * (1 + wait_states)

