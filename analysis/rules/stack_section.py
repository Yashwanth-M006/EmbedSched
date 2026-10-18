from typing import List
from models.finding import Finding

def check_no_stack_section(
    linker_regions: dict,
    linker_symbols: dict,
    chip_regions: dict
) -> List[Finding]:
    """
    Detects when the linker script has no explicit STACK section or
    _Min_Stack_Size symbol. Infers headroom from _estack - __bss_end__
    when available.
    linker_symbols: dict of special linker symbols {name: address_int}
    """
    findings = []
    
    # Check if a STACK section exists by looking for __stack_start or __stack_end
    has_stack_section = '__stack_start' in linker_symbols or '__stack_end' in linker_symbols
    has_min_stack = '_Min_Stack_Size' in linker_symbols
    
    if not has_stack_section and not has_min_stack:
        # Try to infer headroom
        estack = linker_symbols.get('_estack', 0)
        bss_end = linker_symbols.get('__bss_end__', 0) or linker_symbols.get('_ebss', 0)
        
        headroom_str = ""
        if estack and bss_end and estack > bss_end:
            headroom_bytes = estack - bss_end
            headroom_kb = headroom_bytes / 1024.0
            headroom_str = (
                f"\n  Inferred headroom: _estack (0x{estack:08x}) - "
                f"__bss_end__ (0x{bss_end:08x}) = {headroom_bytes:,} bytes ({headroom_kb:.1f} KB)"
                f"\n  WARNING: BSS growth will silently reduce this headroom."
            )
        
        findings.append(Finding(
            rule="no_explicit_stack_section",
            severity="WARNING",
            tag="[STATIC]",
            message=(
                "No _Min_Stack_Size or explicit STACK section found in linker script.\n"
                "  Stack size is unverifiable at link time.\n"
                "  The stack exists implicitly: SP is loaded from _estack at reset,\n"
                "  growing down toward __bss_end__."
                + headroom_str
            ),
            fix="Add to linker script: _Min_Stack_Size = 0x400; and a STACK section."
        ))
    elif has_stack_section or has_min_stack:
        min_stack_size = linker_symbols.get('_Min_Stack_Size', 0)
        stack_start = linker_symbols.get('__stack_start', 0)
        stack_end = linker_symbols.get('__stack_end', 0)
        msg_lines = ["Explicit stack reservation found."]
        if min_stack_size:
            msg_lines.append(f"  _Min_Stack_Size = 0x{min_stack_size:04x} ({min_stack_size} bytes).")
        if stack_start and stack_end:
            msg_lines.append(f"  __stack_start = 0x{stack_start:08x}, __stack_end = 0x{stack_end:08x}.")
        findings.append(Finding(
            rule="explicit_stack_found",
            severity="INFO",
            tag="[STATIC]",
            message="\n".join(msg_lines),
            fix="No action needed."
        ))
    
    return findings
