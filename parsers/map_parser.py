import re
from typing import List
from models.symbol import Symbol

def parse_map_file(filepath: str) -> List[Symbol]:
    """
    Parses a GCC linker .map file and extracts symbols.
    """
    symbols = []
    # Basic regex for symbol lines:
    #  .text.adc_dma_isr       0x000000000000000c   0x48   build/adc.o
    # Match group 1: section
    # Match group 2: address (hex)
    pattern_single = re.compile(
        r'^\s+([.\w]+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(.*\.o)$'
    )
    pattern_section_only = re.compile(r'^\s+([.\w]+)$')
    pattern_addr_only = re.compile(
        r'^\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(.*\.o)$'
    )
    # Matches lines like:
    #                 0x00000000                TIM2_IRQHandler
    sym_pattern = re.compile(r'^\s+(0x[0-9a-fA-F]+)\s+([A-Za-z_][A-Za-z0-9_]*)$')
    
    current_section = ""
    current_obj = ""
    pending_section = ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern_single.match(line)
            if match:
                section = match.group(1)
                addr_str = match.group(2)
                size_str = match.group(3)
                obj = match.group(4).strip()
                
                size = int(size_str, 16)
                current_section = section
                current_obj = obj
                pending_section = ""
                
                if size == 0:
                    continue  # Ignore zero-size symbols
                
                name = section.split('.')[-1] if '.' in section else section
                
                symbols.append(Symbol(
                    name=name,
                    address=int(addr_str, 16),
                    size=size,
                    section=section,
                    object_file=obj
                ))
                continue
                
            match_addr = pattern_addr_only.match(line)
            if match_addr and pending_section:
                addr_str = match_addr.group(1)
                size_str = match_addr.group(2)
                obj = match_addr.group(3).strip()
                
                size = int(size_str, 16)
                section = pending_section
                current_section = section
                current_obj = obj
                pending_section = ""
                
                if size == 0:
                    continue
                    
                name = section.split('.')[-1] if '.' in section else section
                symbols.append(Symbol(
                    name=name,
                    address=int(addr_str, 16),
                    size=size,
                    section=section,
                    object_file=obj
                ))
                continue
                
            match_sec = pattern_section_only.match(line)
            if match_sec:
                pending_section = match_sec.group(1)
                continue
                
            sym_match = sym_pattern.match(line)
            if sym_match and current_section:
                addr_str = sym_match.group(1)
                sym_name = sym_match.group(2)
                addr = int(addr_str, 16)
                # Exclude linker markers starting with underscore
                if sym_name.startswith('_'):
                    continue
                    
                symbols.append(Symbol(
                    name=sym_name,
                    address=addr,
                    size=4, # Dummy size
                    section=current_section,
                    object_file=current_obj
                ))
                    
    return symbols


def parse_map_special_symbols(filepath: str) -> dict:
    """
    Extracts special linker-assigned symbols from the map file.
    These are more reliable than parsing the .ld because the linker
    resolves all expressions (like ORIGIN(SRAM)+LENGTH(SRAM)) to final values.

    Handles two formats:
      Full address (8+ hex digits):
        0x0000000020020000   _estack = ORIGIN (SRAM) + LENGTH (SRAM)
        0x0000000020001034   __bss_end__ = .
      Short constant (e.g. _Min_Stack_Size):
        0x0000000000000400   _Min_Stack_Size = 0x400

    Returns {symbol_name: int_value}
    """
    import re
    special_syms = {}

    # Full-address lines (8+ hex nibbles) — covers _estack, __bss_end__, etc.
    abs_pattern = re.compile(
        r'^\s*(0x[0-9a-fA-F]{8,})\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|$)'
    )
    # Short-constant lines (any length) — catches _Min_Stack_Size = 0x400
    short_pattern = re.compile(
        r'^\s*(0x[0-9a-fA-F]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|$)'
    )

    INTERESTING = {
        '_estack', '__bss_end__', '_ebss', '_sbss', '_sdata', '_edata',
        '_Min_Stack_Size', '_Min_Heap_Size',
        '__stack_start', '__stack_end', '__bss_start__',
        '_heap_end', 'end',
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Try the full-address pattern first (most common)
            m = abs_pattern.match(line)
            if not m:
                # Fall back to short-constant pattern
                m = short_pattern.match(line)
            if m:
                addr = int(m.group(1), 16)
                sym = m.group(2)
                if sym in INTERESTING:
                    special_syms[sym] = addr
    return special_syms
