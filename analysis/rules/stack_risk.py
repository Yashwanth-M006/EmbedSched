from typing import List
from models.finding import Finding

from analysis.region_classifier import classify_address

def check_stack_risk(
    max_depth: int,
    call_chain: List[str],
    has_recursion: bool,
    stack_capacity: int,
    linker_symbols: dict,
    linker_regions: dict,
    chip_regions: dict,
    stack_cap_src: str = '_Min_Stack_Size from map/ld',
) -> List[Finding]:
    findings = []
    
    # Check for stack placement in DTCM
    stack_start = linker_symbols.get('__stack_start', 0)
    region = classify_address(stack_start, linker_regions, chip_regions)
    if region == 'DTCM' and stack_start > 0:
        pct = (max_depth / stack_capacity) * 100 if stack_capacity > 0 else 0
        headroom = stack_capacity - max_depth if stack_capacity > 0 else 0
        findings.append(Finding(
            rule="stack_in_dtcm_confirmed",
            severity="INFO",
            tag="[STATIC]",
            message=f"__stack_start: 0x{stack_start:08X} -> DTCM\n  Stack in DTCM - correct placement on Cortex-M7.\n  DTCM is CPU-only (D-bus), DMA-isolated. Stack push/pop: 0 wait states.\n  Stack size: {stack_capacity} bytes. Usage: {max_depth}B ({pct:.1f}%). Headroom: {headroom} bytes.",
            fix="No action needed."
        ))

    
    if has_recursion:
        findings.append(Finding(
            rule="stack_recursion",
            severity="CRITICAL",
            tag="[STATIC]",
            message=f"Recursion detected in call chain: {' -> '.join(call_chain)}.\n  Stack depth unbounded.",
            fix="Refactor code to eliminate recursive calls."
        ))
        
    if stack_capacity > 0:
        pct = (max_depth / stack_capacity) * 100
        if pct >= 80:
            severity = "CRITICAL" if pct >= 90 else "WARNING"
            findings.append(Finding(
                rule="stack_overflow_risk",
                severity=severity,
                tag="[STATIC]",
                message=(
                    f"Worst-case call chain: {' -> '.join(call_chain)}\n"
                    f"  Stack usage: {max_depth:,} / {stack_capacity:,} bytes ({pct:.1f}%)"
                    f" - {stack_capacity - max_depth} byte margin\n"
                    f"  Capacity source: {stack_cap_src}"
                ),
                fix="Increase stack size in linker script or reduce local variables."
            ))
            
    return findings


def check_indirect_calls(
    indirect_calls: dict,
) -> List[Finding]:
    """
    Evaluates unresolved indirect callsites (e.g. blx r3) across the firmware.
    Provides diagnostic guidance on compiling with Whole-Program LTO
    (-flto -fwhole-program -fdevirtualize) to devirtualize static callback tables
    into direct calls visible to static call-graph and stack-depth analysis.
    """
    findings = []
    if not indirect_calls:
        return findings

    total_sites = sum(len(sites) for sites in indirect_calls.values())
    func_samples = []
    for func, sites in list(indirect_calls.items())[:5]:
        sample_str = ", ".join(f"0x{addr:08x}: {mnem} {reg}" for addr, mnem, reg in sites[:2])
        if len(sites) > 2:
            sample_str += f" (+{len(sites)-2} more)"
        func_samples.append(f"    - {func}(): {sample_str}")

    sample_block = "\n".join(func_samples)
    more_funcs = f"\n    ... and {len(indirect_calls) - 5} more functions" if len(indirect_calls) > 5 else ""

    findings.append(Finding(
        rule="indirect_calls_devirtualization_advisory",
        severity="INFO",
        tag="[STATIC]",
        message=(
            f"Detected {total_sites} unresolved indirect callsite(s) across {len(indirect_calls)} function(s):\n"
            f"{sample_block}{more_funcs}\n"
            f"  Indirect branches via register (e.g. 'blx Rn') obscure runtime call targets from static disassembly.\n"
            f"  If these callbacks initiate deep call trees or recursive cycles, stack depth bounds may be optimistic.\n"
            f"  Devirtualization Recommendation:\n"
            f"    Compile with Whole-Program Link-Time Optimization (LTO):\n"
            f"      -flto -fwhole-program -fdevirtualize\n"
            f"    GCC/Clang interprocedural constant propagation (IPA-CP) will devirtualize monomorphic callback tables\n"
            f"    into direct 'bl' calls, rendering them fully visible to static call-graph and stack-depth derivation."
        ),
        fix="Compile with '-flto -fwhole-program -fdevirtualize' to promote indirect calls to direct branches, and annotate remaining dynamic dispatch tables."
    ))

    return findings
