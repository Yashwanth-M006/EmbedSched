"""
stack_bss_proximity.py — Detects zero/insufficient gap between .bss end and
the start of the declared .stack section, and checks for undersized stack.

Rules:
  stack_bss_zero_gap       CRITICAL  — gap == 0 bytes between __bss_end__ and __stack_start
  stack_declared_too_small WARNING   — stack depth ratio >= 40% of _Min_Stack_Size
"""
from typing import List, Dict
from models.finding import Finding
from models.symbol import Symbol
from analysis.region_classifier import classify_address


def check_stack_bss_proximity(
    linker_symbols: dict,
    linker_regions: dict,
    chip_regions: dict,
    chip: dict,
    symbols: List[Symbol],
    max_depth: int,
    max_chain: List[str],
    isr_max_depth: int,
    isr_max_chain: List[str],
    main_max_depth: int,
    main_max_chain: List[str],
) -> List[Finding]:
    """
    Fires when:
      1. An explicit .stack section exists (_Min_Stack_Size present AND __stack_start present)
      2. __bss_end__ and __stack_start are identical (zero gap) → CRITICAL
      3. stack worst-case depth / _Min_Stack_Size >= 40% → WARNING
    """
    findings = []

    has_stack_section = '__stack_start' in linker_symbols
    has_min_stack = '_Min_Stack_Size' in linker_symbols

    # Only run if the stack section is fully declared (otherwise stack_section.py handles it)
    if not has_stack_section or not has_min_stack:
        return []

    bss_end = linker_symbols.get('__bss_end__', 0) or linker_symbols.get('_ebss', 0)
    stack_start = linker_symbols.get('__stack_start', 0)
    stack_end = linker_symbols.get('__stack_end', 0)
    min_stack_size = linker_symbols.get('_Min_Stack_Size', 0)
    estack = linker_symbols.get('_estack', 0)

    if bss_end == 0 or stack_start == 0:
        return []

    gap = stack_start - bss_end

    # ── Rule A: Zero-gap CRITICAL ───────────────────────────────────────────
    if gap == 0:
        # Find the last symbols before __bss_end__ in .bss
        bss_symbols_near_end = []
        for sym in sorted(symbols, key=lambda s: s.address, reverse=True):
            region = classify_address(sym.address, linker_regions, chip_regions)
            if region in ('SRAM1', 'SRAM') and sym.address < bss_end and sym.size > 0:
                if not sym.name.startswith('__') and not sym.name.startswith('_e'):
                    bss_symbols_near_end.append(sym)
                if len(bss_symbols_near_end) >= 3:
                    break

        at_risk = ', '.join(f"{s.name} (0x{s.address:08X})" for s in bss_symbols_near_end)
        at_risk_str = f"\n  Symbols at corruption risk: {at_risk}" if at_risk else ""

        msg = (
            f"__bss_end__   = 0x{bss_end:08X}\n"
            f"  __stack_start = 0x{stack_start:08X}\n"
            f"  Gap between end of .bss and start of .stack section = 0 bytes\n"
            f"\n"
            f"  The .stack section is placed IMMEDIATELY after .bss with no gap.\n"
            f"  If ANY new global variable is added, the linker will overlap .bss\n"
            f"  or overflow SRAM1 entirely.\n"
            f"\n"
            f"  At runtime: hardware SP starts at _estack (0x{estack:08X}) and grows\n"
            f"  DOWN freely — no MPU guard region declared. Stack growth below\n"
            f"  __stack_start silently corrupts the end of .bss."
            + at_risk_str
        )

        findings.append(Finding(
            rule="stack_bss_zero_gap",
            severity="CRITICAL",
            tag="[STATIC]",
            message=msg,
            fix=(
                "Increase _Min_Stack_Size in linker script (recommend >= 0x400 = 1024B) "
                "OR move .stack section to CCM (0x10000000 on F407) to eliminate BSS adjacency risk."
            )
        ))

    # ── Rule B: Stack declared too small (ratio-based WARNING) ─────────────
    if min_stack_size > 0 and max_depth > 0:
        ratio = max_depth / min_stack_size
        headroom = min_stack_size - max_depth

        if ratio >= 0.40:  # 40% threshold → WARNING
            # Combined ISR + main preemption scenario
            combined = isr_max_depth + main_max_depth
            combined_ratio = (combined / min_stack_size) * 100 if min_stack_size > 0 else 0
            combined_headroom = min_stack_size - combined

            isr_chain_str  = ' -> '.join(isr_max_chain)  if isr_max_chain  else 'N/A'
            main_chain_str = ' -> '.join(main_max_chain) if main_max_chain else 'N/A'

            gap_context = " With zero BSS-to-stack gap (see CRITICAL above), any BSS growth reduces the usable .stack section further." if gap == 0 else ""

            msg = (
                f"_Min_Stack_Size  = {min_stack_size} bytes (0x{min_stack_size:X}, from linker script)\n"
                f"  Worst-case depth = {max_depth} bytes ({ratio*100:.1f}% of budget)\n"
                f"  Headroom         = {headroom} bytes\n"
                f"\n"
                f"  Worst-case call chain: {' -> '.join(max_chain)}\n"
                f"\n"
                f"  ISR path:  {isr_chain_str} = {isr_max_depth}B\n"
                f"  Main path: {main_chain_str} = {main_max_depth}B\n"
                f"  Combined preemption (ISR interrupts main): {isr_max_depth}B + {main_max_depth}B = {combined}B vs {min_stack_size}B budget"
                f" -> {combined_headroom}B headroom ({100-combined_ratio:.1f}% remaining)."
                + gap_context
            )

            findings.append(Finding(
                rule="stack_declared_too_small",
                severity="WARNING",
                tag="[STATIC]",
                message=msg,
                fix=(
                    f"Increase _Min_Stack_Size to at least 0x{combined * 2:X} ({combined * 2}B) "
                    "and consider moving .stack to CCM."
                )
            ))

    return findings
