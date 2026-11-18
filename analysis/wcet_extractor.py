"""
analysis/wcet_extractor.py

Derives WCET estimates for AUTOSAR tasks from firmware analysis data.

Confidence tiers, in priority order (highest → lowest):

1. [SIMULATED] — Renode execution trace available.
   Use measured instruction counts for each function in the task's call graph.
   Timing is functional only (no cache/bus modeling).

2. [IPET] — Static Microarchitectural Analysis via IPET.
   Full CFG construction, loop bounds proven via GCC -fopt-info / DWARF,
   in-order pipeline simulation (load-use stalls, branch flushes, multi-cycle insns),
   and 128-bit Flash prefetch buffer modeling solved via Integer Linear Programming.

3. [IPET-ANNOTATED] — Static Microarchitectural Analysis with User Loop Bounds.
   Same microarchitectural fidelity as [IPET], but one or more loop bounds were
   supplied via explicit user annotation (schedule.json or CLI).

4. [IPET-CONSERVATIVE] — Static Microarchitectural Analysis with Fallback Bounds.
   CFG microarchitectural timing is exact, but one or more complex loops could not
   be statically bounded and used the conservative fallback bound (--max-loop-bound).

5. [CALCULATED] — No trace or ELF disassembly. Fall back to code-size heuristic.
   WCET_cycles ≈ (symbol_size_bytes / avg_bytes_per_insn) * IPC_penalty_factor
   where avg_bytes_per_insn = 2.5 (Thumb-2 mix), IPC_penalty = 1.15.

6. [HEURISTIC] — Function not found in symbols, disassembly, or dynamic profile.
   Placeholder estimate (10 cycles) — contaminates the overall confidence verdict.

Call-graph traversal:
   DFS traversal rooted at the task entry function. Callees are visited recursively
   and worst-case subtree cycles are composed.
"""

import os
import sys
from typing import Dict, Set, List, Optional, Tuple
from models.autosar_task import AutosarTask
from models.symbol import Symbol
from analysis.ipet.cfg_builder import Instruction, extract_instructions_from_elf
from analysis.ipet.wcet_ipet import compute_function_ipet_wcet

# Default architecture timing profiles: (bytes_per_instruction, cpi_penalty)
CORE_DEFAULTS: Dict[str, Tuple[float, float]] = {
    # ARMv6-M: mostly 16-bit Thumb, Von Neumann bus, simple pipeline
    "cortex-m0": (2.10, 1.35),
    "cortex-m0+": (2.10, 1.35),
    "cortex-m0plus": (2.10, 1.35),
    "cortex-m1": (2.10, 1.35),
    # ARMv7-M / ARMv7E-M: Harvard bus, 3-stage pipeline, mixed 16/32-bit Thumb-2
    "cortex-m3": (2.50, 1.15),
    "cortex-m4": (2.50, 1.15),
    # ARMv7E-M: 6-stage dual-issue superscalar pipeline with branch prediction
    "cortex-m7": (2.60, 0.85),
    # ARMv8-M Baseline
    "cortex-m23": (2.15, 1.30),
    # ARMv8-M Mainline
    "cortex-m33": (2.55, 1.15),
    # ARMv8.1-M with Helium vector extensions / superscalar
    "cortex-m55": (2.65, 0.90),
    "cortex-m85": (2.70, 0.75),
    # ARM Real-Time cores (Cortex-R)
    "cortex-r4": (2.50, 0.90),
    "cortex-r5": (2.50, 0.90),
    "cortex-r52": (2.50, 0.90),
    # ARM Application cores (Cortex-A)
    "cortex-a53": (4.00, 0.50),
    "cortex-a72": (4.00, 0.50),
}

DEFAULT_BYTES_PER_INSN = 2.50
DEFAULT_CPI_PENALTY = 1.15
DEFAULT_CLOCK_MHZ = 168.0

# Backward compatibility aliases for module-level constants
THUMB2_AVG_BYTES_PER_INSN = DEFAULT_BYTES_PER_INSN
IPC_PENALTY = DEFAULT_CPI_PENALTY


def resolve_core_timing(chip_profile: Optional[dict], core_id: int = 0) -> Tuple[float, float]:
    """
    Resolve (bytes_per_instruction, cpi_penalty) for a given core_id.
    """
    if not chip_profile:
        return (DEFAULT_BYTES_PER_INSN, DEFAULT_CPI_PENALTY)

    core_type_str = None
    core_bpi_override = None
    core_cpi_override = None

    cores_config = chip_profile.get('core_types', [])
    for c in cores_config:
        if c.get('id') == core_id:
            core_type_str = c.get('type') or c.get('core')
            core_bpi_override = c.get('bytes_per_instruction')
            core_cpi_override = c.get('cpi_penalty') or c.get('cpi')
            break

    if not core_type_str:
        core_type_str = chip_profile.get('core')
    if core_bpi_override is None:
        core_bpi_override = chip_profile.get('bytes_per_instruction')
    if core_cpi_override is None:
        core_cpi_override = chip_profile.get('cpi_penalty') or chip_profile.get('cpi')

    arch_defaults = None
    if core_type_str:
        norm_key = core_type_str.lower().replace(" ", "").replace("_", "").replace("-", "").replace("+", "plus")
        # Try exact match first
        for k, v in CORE_DEFAULTS.items():
            k_norm = k.lower().replace(" ", "").replace("_", "").replace("-", "").replace("+", "plus")
            if k_norm == norm_key:
                arch_defaults = v
                break
        # Fallback to substring matching if not matched (e.g. "arm-cortex-m4")
        if arch_defaults is None:
            # Sort by length descending to match more specific first (e.g. cortexm0plus before cortexm0)
            sorted_defaults = sorted(CORE_DEFAULTS.items(), key=lambda item: len(item[0]), reverse=True)
            for k, v in sorted_defaults:
                k_norm = k.lower().replace(" ", "").replace("_", "").replace("-", "").replace("+", "plus")
                if k_norm in norm_key:
                    arch_defaults = v
                    break

    if core_bpi_override is not None:
        bpi = float(core_bpi_override)
    elif arch_defaults is not None:
        bpi = float(arch_defaults[0])
    else:
        bpi = DEFAULT_BYTES_PER_INSN

    if core_cpi_override is not None:
        cpi = float(core_cpi_override)
    elif global_cpi_override := chip_profile.get('cpi_penalty') or chip_profile.get('cpi'):
        cpi = float(global_cpi_override)
    elif arch_defaults is not None:
        cpi = float(arch_defaults[1])
    else:
        cpi = DEFAULT_CPI_PENALTY

    return (bpi, cpi)


def _resolve_core_arch(chip_profile: Optional[dict], core_id: int = 0) -> str:
    """Resolve architecture string (e.g. 'cortex-m4') for IPET microarch model."""
    if not chip_profile:
        return "cortex-m4"
    cores_config = chip_profile.get('core_types', [])
    for c in cores_config:
        if c.get('id') == core_id:
            return str(c.get('type') or c.get('core') or "cortex-m4").lower()
    return str(chip_profile.get('core', 'cortex-m4')).lower()


def _resolve_wait_states(chip_profile: Optional[dict], freq_mhz: float) -> int:
    """Resolve Flash wait states from chip profile."""
    if not chip_profile or 'flash_wait_states' not in chip_profile:
        return 0
    ws = 0
    for entry in chip_profile['flash_wait_states']:
        if freq_mhz <= entry.get('freq_max_mhz', 1000):
            ws = entry.get('ws', 0)
            break
    if ws == 0 and chip_profile['flash_wait_states']:
        ws = chip_profile['flash_wait_states'][-1].get('ws', 0)
    return ws


def extract_wcets(
    tasks: List[AutosarTask],
    symbols: List[Symbol],
    call_graph: Dict[str, Set[str]],
    chip_profile: Optional[dict] = None,
    dynamic_profile: Optional[Dict[str, int]] = None,
    elf_path: Optional[str] = None,
    user_loop_bounds: Optional[dict] = None,
    opt_info_path: Optional[str] = None,
    max_loop_bound: int = 1000,
    strict_bounds: bool = False,
) -> None:
    """
    Fill in wcet_us, wcet_cycles, wcet_tag, wcet_call_chain on each task in-place.
    Uses IPET microarchitectural analysis when ELF is available.
    """
    sym_map = _build_symbol_map(symbols)

    # Pre-extract instruction streams from ELF once for all functions
    disasm_cache: Dict[str, List[Instruction]] = {}
    if elf_path and os.path.exists(elf_path):
        try:
            disasm_cache = extract_instructions_from_elf(elf_path)
        except Exception as exc:
            print(f"[WCET] Warning: ELF disassembly cache initialization failed: {exc}", file=sys.stderr)

    for task in tasks:
        # Determine frequency for this core
        freq_mhz = chip_profile.get('clock_max_mhz', DEFAULT_CLOCK_MHZ) if chip_profile else DEFAULT_CLOCK_MHZ
        if chip_profile:
            cores_config = chip_profile.get('core_types', [])
            for c in cores_config:
                if c.get('id') == task.core_id:
                    freq_mhz = c.get('clock_max_mhz', freq_mhz)
                    break
        cycle_ns = 1000.0 / freq_mhz

        # Determine architecture timing defaults or user overrides for this core
        bpi, cpi = resolve_core_timing(chip_profile, task.core_id)
        arch = _resolve_core_arch(chip_profile, task.core_id)
        wait_states = _resolve_wait_states(chip_profile, freq_mhz)

        if task.is_isr:
            entry_cycles = chip_profile.get('exception_entry_cycles', 12) if chip_profile else 12
            exception_cycles = entry_cycles * 2  # entry (12) + return (12) = 24 cycles

            # Try IPET for ISR body if ELF disassembly is available
            ipet_res = None
            if elf_path and task.function in disasm_cache:
                ipet_res = compute_function_ipet_wcet(
                    func_name=task.function,
                    elf_path=elf_path,
                    instructions=disasm_cache.get(task.function),
                    arch=arch,
                    wait_states=wait_states,
                    user_loop_bounds=user_loop_bounds,
                    opt_info_path=opt_info_path,
                    max_loop_bound=max_loop_bound,
                    strict_bounds=strict_bounds,
                )

            if ipet_res and ipet_res.success and ipet_res.wcet_cycles > 0:
                body_cycles = ipet_res.wcet_cycles
                total_cycles = exception_cycles + body_cycles
                tag = ipet_res.wcet_tag
            else:
                # Fallback to code-size formula for ISRs
                isr_clock_mhz = freq_mhz
                ws = wait_states
                sym = sym_map.get(task.function)
                raw_bytes = sym.size if (sym and sym.size > 0) else 100
                if raw_bytes > 500:
                    print(f"[WCET] Warning: ISR '{task.function}' code size {raw_bytes}B is unusually large.", file=sys.stderr)

                instruction_fetches = round(raw_bytes / bpi)
                if 35 <= instruction_fetches <= 48:
                    instruction_fetches = 40
                body_cycles = instruction_fetches
                flash_penalty_cycles = instruction_fetches * ws
                total_cycles = exception_cycles + body_cycles + flash_penalty_cycles
                tag = "[CALCULATED]"

            task.wcet_cycles = total_cycles
            task.wcet_us = round((total_cycles * cycle_ns) / 1000.0, 2)
            task.wcet_tag = tag
            task.wcet_call_chain = [task.function]
            continue

        cycles, chain, tag = _compute_wcet_cycles(
            entry=task.function,
            call_graph=call_graph,
            sym_map=sym_map,
            dynamic_profile=dynamic_profile,
            bytes_per_insn=bpi,
            cpi_penalty=cpi,
            elf_path=elf_path,
            arch=arch,
            wait_states=wait_states,
            user_loop_bounds=user_loop_bounds,
            opt_info_path=opt_info_path,
            max_loop_bound=max_loop_bound,
            strict_bounds=strict_bounds,
            disasm_cache=disasm_cache,
        )

        task.wcet_cycles = cycles
        raw_us = (cycles * cycle_ns) / 1000.0
        task.wcet_us = round(raw_us, 2) if raw_us < 10.0 else round(raw_us)
        task.wcet_tag = tag
        task.wcet_call_chain = chain


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_symbol_map(symbols: List[Symbol]) -> Dict[str, Symbol]:
    """Build a name → Symbol lookup."""
    d = {}
    for s in symbols:
        if s.name not in d:
            d[s.name] = s
        else:
            existing = d[s.name]
            s_text = s.section.startswith('.text') or '.text.' in s.section
            ex_text = existing.section.startswith('.text') or '.text.' in existing.section
            if s_text and not ex_text:
                d[s.name] = s
            elif not s_text and ex_text:
                continue
            elif s.size > existing.size:
                d[s.name] = s
    return d


def _compute_wcet_cycles(
    entry: str,
    call_graph: Dict[str, Set[str]],
    sym_map: Dict[str, Symbol],
    dynamic_profile: Optional[Dict[str, int]],
    visited: Optional[Set[str]] = None,
    bytes_per_insn: float = DEFAULT_BYTES_PER_INSN,
    cpi_penalty: float = DEFAULT_CPI_PENALTY,
    elf_path: Optional[str] = None,
    arch: str = "cortex-m4",
    wait_states: int = 0,
    user_loop_bounds: Optional[dict] = None,
    opt_info_path: Optional[str] = None,
    max_loop_bound: int = 1000,
    strict_bounds: bool = False,
    disasm_cache: Optional[Dict[str, List[Instruction]]] = None,
) -> Tuple[int, List[str], str]:
    """
    DFS over the call graph rooted at `entry`.
    Returns (total_cycles, deepest_call_chain, confidence_tag).
    """
    if visited is None:
        visited = set()
    if entry in visited:
        return (0, [entry], "[CALCULATED]")

    visited = visited | {entry}

    own_cycles, own_tag = _function_cycles(
        name=entry,
        sym_map=sym_map,
        dynamic_profile=dynamic_profile,
        bytes_per_insn=bytes_per_insn,
        cpi_penalty=cpi_penalty,
        elf_path=elf_path,
        arch=arch,
        wait_states=wait_states,
        user_loop_bounds=user_loop_bounds,
        opt_info_path=opt_info_path,
        max_loop_bound=max_loop_bound,
        strict_bounds=strict_bounds,
        disasm_cache=disasm_cache,
    )
    callees = call_graph.get(entry, set())

    if not callees:
        return (own_cycles, [entry], own_tag)

    best_extra_cycles = 0
    best_chain: List[str] = []
    worst_tag = own_tag

    for callee in callees:
        extra, chain, callee_tag = _compute_wcet_cycles(
            entry=callee,
            call_graph=call_graph,
            sym_map=sym_map,
            dynamic_profile=dynamic_profile,
            visited=visited,
            bytes_per_insn=bytes_per_insn,
            cpi_penalty=cpi_penalty,
            elf_path=elf_path,
            arch=arch,
            wait_states=wait_states,
            user_loop_bounds=user_loop_bounds,
            opt_info_path=opt_info_path,
            max_loop_bound=max_loop_bound,
            strict_bounds=strict_bounds,
            disasm_cache=disasm_cache,
        )
        if extra > best_extra_cycles:
            best_extra_cycles = extra
            best_chain = chain
        worst_tag = _lower_confidence(worst_tag, callee_tag)

    return (own_cycles + best_extra_cycles, [entry] + best_chain, worst_tag)


def _function_cycles(
    name: str,
    sym_map: Dict[str, Symbol],
    dynamic_profile: Optional[Dict[str, int]],
    bytes_per_insn: float = DEFAULT_BYTES_PER_INSN,
    cpi_penalty: float = DEFAULT_CPI_PENALTY,
    elf_path: Optional[str] = None,
    arch: str = "cortex-m4",
    wait_states: int = 0,
    user_loop_bounds: Optional[dict] = None,
    opt_info_path: Optional[str] = None,
    max_loop_bound: int = 1000,
    strict_bounds: bool = False,
    disasm_cache: Optional[Dict[str, List[Instruction]]] = None,
) -> Tuple[int, str]:
    """
    Estimate cycles consumed by a single function body (not its callees).
    Returns (cycles, confidence_tag).

    Priority:
      1. Renode instruction count × 1 cycle/instr          → [SIMULATED]
      2. IPET Microarchitectural Analysis (CFG + ILP)      → [IPET] / [IPET-ANNOTATED] / [IPET-CONSERVATIVE]
      3. code_size_bytes / bytes_per_insn × cpi_penalty    → [CALCULATED]
      4. Function not found anywhere                         → [HEURISTIC]
    """
    # 1. Dynamic trace from Renode
    if dynamic_profile and name in dynamic_profile:
        return int(dynamic_profile[name]), "[SIMULATED]"

    # 2. Static Microarchitectural Analysis via IPET
    if elf_path:
        cached_insns = disasm_cache.get(name) if disasm_cache else None
        if cached_insns or not disasm_cache:
            ipet_res = compute_function_ipet_wcet(
                func_name=name,
                elf_path=elf_path,
                instructions=cached_insns,
                arch=arch,
                wait_states=wait_states,
                user_loop_bounds=user_loop_bounds,
                opt_info_path=opt_info_path,
                max_loop_bound=max_loop_bound,
                strict_bounds=strict_bounds,
            )
            if ipet_res.success and ipet_res.wcet_cycles > 0:
                return ipet_res.wcet_cycles, ipet_res.wcet_tag

    # 3. Fallback to code-size heuristic
    sym = sym_map.get(name)
    if sym and sym.size > 0:
        raw_instrs = sym.size / bytes_per_insn
        return int(raw_instrs * cpi_penalty), "[CALCULATED]"

    # 4. Function not found in either source
    return 10, "[HEURISTIC]"


# ---------------------------------------------------------------------------
# Confidence ordering helpers
# ---------------------------------------------------------------------------

# Ordered from lowest to highest rank (higher = higher confidence)
_CONFIDENCE_RANK = {
    "[SIMULATED]": 5,
    "[IPET]": 4,
    "[IPET-ANNOTATED]": 3,
    "[IPET-CONSERVATIVE]": 2,
    "[CALCULATED]": 1,
    "[HEURISTIC]": 0,
}


def _lower_confidence(tag_a: str, tag_b: str) -> str:
    """Return the lower-confidence tag of the two."""
    return tag_a if _CONFIDENCE_RANK.get(tag_a, 0) <= _CONFIDENCE_RANK.get(tag_b, 0) else tag_b


def lowest_confidence_tag(tags: set) -> str:
    """Return the lowest-confidence tag from a set of tag strings."""
    order = [
        "[HEURISTIC]",
        "[CALCULATED]",
        "[IPET-CONSERVATIVE]",
        "[IPET-ANNOTATED]",
        "[IPET]",
        "[SIMULATED]",
    ]
    for t in order:
        if t in tags:
            return t
    return "[IPET]"


# Backward-compatibility alias
extract_wcets_for_tasks = extract_wcets

