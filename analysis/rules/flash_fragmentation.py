"""
flash_fragmentation.py — Detects poor Flash cache locality for hot functions.

Rule: flash_fragmentation  INFO (-15)

When performance-critical ("hot") functions are spread across Flash with large
gaps between them, the ART accelerator's sequential prefetch buffer is useless
and every call from one hot function to another triggers a cold I-cache miss.

On STM32F407 the ART accelerator is an 8 × 128-bit (8 × 16 byte) prefetch
buffer. On STM32F7/H7 the I-cache line is 32 bytes. This rule uses 32 bytes as
a conservative cache-line estimate (works for both families).

Inputs:
  hot_func_names : ordered list of function names (from --hot-funcs file)
  symbols        : list of Symbol objects (address + size from .map)

Gap thresholds:
  ≥ 1 cache line  (32 B)   → MODERATE (minor penalty, warn only)
  ≥ 16 cache lines (512 B) → LARGE    (significant jitter)
  ≥ 64 cache lines (2 KB)  → SEVERE   (catastrophic thrashing)
"""

from typing import List, Dict, Optional
from models.finding import Finding
from models.symbol import Symbol

CACHE_LINE_BYTES = 32   # conservative: matches Cortex-M7 I-cache; also useful for ART

GAP_LARGE_BYTES   = 512     # ≥ 16 lines → LARGE GAP
GAP_SEVERE_BYTES  = 2048    # ≥ 64 lines → SEVERE GAP
SCORE_THRESHOLD   = 512     # any gap above this contributes to the penalty finding


def _find_symbol(name: str, symbols: List[Symbol]) -> Optional[Symbol]:
    """Return the first symbol matching `name` (exact)."""
    for sym in symbols:
        if sym.name == name:
            return sym
    return None


def check_flash_fragmentation(
    hot_func_names: List[str],
    symbols: List[Symbol],
) -> List[Finding]:
    """
    Analyse the Flash layout of `hot_func_names` in address order.
    Report gaps between consecutive hot functions that are larger than
    SCORE_THRESHOLD bytes (i.e., not in the same cache line).
    """
    if not hot_func_names:
        return []

    # Resolve each name to a Symbol
    resolved: List[Dict] = []
    for name in hot_func_names:
        sym = _find_symbol(name, symbols)
        if sym:
            resolved.append({'name': name, 'addr': sym.address, 'size': sym.size})

    if len(resolved) < 2:
        return []

    # Sort by address (in case hot_functions.txt is not in address order)
    resolved.sort(key=lambda x: x['addr'])

    # Compute gaps between consecutive hot functions
    gap_details = []
    total_lines = 0
    significant_gaps = 0

    for i in range(len(resolved) - 1):
        cur  = resolved[i]
        nxt  = resolved[i + 1]
        cur_end = cur['addr'] + cur['size']
        gap_bytes = nxt['addr'] - cur_end

        if gap_bytes <= 0:
            continue  # functions are adjacent or overlapping — fine

        lines = (gap_bytes + CACHE_LINE_BYTES - 1) // CACHE_LINE_BYTES

        if gap_bytes >= GAP_SEVERE_BYTES:
            status = "SEVERE GAP — catastrophic I-cache thrashing"
        elif gap_bytes >= GAP_LARGE_BYTES:
            status = "LARGE GAP — multiple I-cache misses predicted"
        else:
            status = "MODERATE GAP — minor cache pressure"

        gap_details.append({
            'from': cur['name'],
            'to':   nxt['name'],
            'start': cur_end,
            'end':   nxt['addr'],
            'bytes': gap_bytes,
            'lines': lines,
            'status': status,
        })

        if gap_bytes >= SCORE_THRESHOLD:
            significant_gaps += 1
            total_lines += lines

    if not gap_details:
        return []

    # Build the finding message
    func_list_str = ", ".join(r['name'] for r in resolved)
    func_map_lines = []
    for r in resolved:
        func_map_lines.append(
            f"    {r['name']:<20} @ 0x{r['addr']:08X}  size 0x{r['size']:X} ({r['size']} bytes)"
        )
    func_map_str = "\n".join(func_map_lines)

    gap_lines_str = []
    for idx, g in enumerate(gap_details, 1):
        gap_lines_str.append(
            f"    Gap {idx}: {g['from']} -> {g['to']}\n"
            f"      Start:  0x{g['start']:08X}  ({g['from']} end)\n"
            f"      End:    0x{g['end']:08X}  ({g['to']} start)\n"
            f"      Size:   0x{g['bytes']:X} = {g['bytes']} bytes\n"
            f"      Lines:  {g['bytes']} / {CACHE_LINE_BYTES} = {g['lines']} cache lines\n"
            f"      Status: {g['status']}\n"
            f"      Fix:    Reorder link flags; use -fno-function-sections; add linker\n"
            f"              script grouping (e.g., KEEP() for related code)"
        )
    gap_str = "\n\n".join(gap_lines_str)

    # Aggregate impact estimate
    total_misses = total_lines
    penalty_cycles = total_misses * 4   # conservative: 4-cycle ART miss penalty
    penalty_us = (penalty_cycles / (168e6)) * 1e6 if total_misses else 0

    suffix = "s" if total_misses != 1 else ""
    seq = " -> ".join(r['name'] for r in resolved)
    msg = (
        f"Hot function list: {func_list_str}\n\n"
        f"  Function Map:\n{func_map_str}\n\n"
        f"  Gap Analysis ({CACHE_LINE_BYTES}-byte cache line assumed):\n{gap_str}\n\n"
        f"  Aggregate Impact:\n"
        f"    - Calling sequence {seq} involves "
        f"{total_misses} cache line{suffix} of separation\n"
        f"    - At 4-cycle penalty per miss (conservative): {penalty_cycles} cycles\n"
        f"    - At 168 MHz: ~{penalty_us:.1f} microseconds per round trip (worst-case)\n"
        f"    - Hot loop penalty if called 1000x: {penalty_us:.1f}ms overhead\n\n"
        f"  Notes:\n"
        f"    - Compiler -ffunction-sections with --gc-sections causes fragmentation\n"
        f"    - Issue NOT fixable at runtime; requires relink or recompile"
    )

    return [Finding(
        rule="flash_fragmentation",
        severity="INFO",
        tag="[STATIC]",
        message=msg,
        fix=(
            "Group hot functions using a dedicated linker section or KEEP() directives. "
            "Alternatively use -fno-function-sections to prevent per-function sections, "
            "then let the linker pack related functions together."
        )
    )]
