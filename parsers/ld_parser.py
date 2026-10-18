import re
from dataclasses import dataclass
from typing import Dict

@dataclass
class MemoryRegion:
    name: str
    origin: int
    length: int

def parse_ld_file(filepath: str) -> Dict[str, MemoryRegion]:
    """
    Parses a GCC linker script (.ld) to extract memory regions from the MEMORY block.
    """
    regions = {}
    
    # Regex to match: REGION_NAME (flags) : ORIGIN = 0x..., LENGTH = ...[K|M]
    # Example: FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    region_pattern = re.compile(
        r'^\s*([A-Za-z0-9_]+)\s*(?:\([a-zA-Z!]+\))?\s*:\s*ORIGIN\s*=\s*(0x[0-9a-fA-F]+)\s*,\s*LENGTH\s*=\s*([0-9]+)([KkMmGg]?)\s*'
    )
    
    in_memory_block = False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Strip comments (single line or simple block comments on one line)
            line_clean = re.sub(r'/\*.*?\*/', '', line)
            line_clean = line_clean.split('/*')[0].strip()
            
            if line_clean.startswith('MEMORY'):
                in_memory_block = True
                continue
                
            if in_memory_block:
                if '}' in line_clean:
                    in_memory_block = False
                    continue
                    
                match = region_pattern.search(line_clean)
                if match:
                    name = match.group(1)
                    origin = int(match.group(2), 16)
                    length_val = int(match.group(3))
                    multiplier = match.group(4).upper()
                    
                    if multiplier == 'K':
                        length_val *= 1024
                    elif multiplier == 'M':
                        length_val *= 1024 * 1024
                    elif multiplier == 'G':
                        length_val *= 1024 * 1024 * 1024
                        
                    regions[name] = MemoryRegion(name=name, origin=origin, length=length_val)
                    
    return regions


def parse_ld_symbols(filepath: str) -> dict:
    """
    Extracts special linker symbol assignments from an .ld file.
    Captures patterns like:
        _estack = ORIGIN(SRAM) + LENGTH(SRAM);
        _Min_Stack_Size = 0x400;
        __bss_end__ = .;   (inside a SECTIONS block - captured as-is)
    Returns: {symbol_name: int_value_or_0}
    Note: ORIGIN()+LENGTH() expressions are evaluated using memory_regions data.
    """
    import re
    regions = parse_ld_file(filepath)
    symbols = {}

    # Simple constant assignments: SYM = 0xVALUE;
    const_pattern = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(0x[0-9a-fA-F]+)\s*;')
    # ORIGIN(REGION) + LENGTH(REGION) pattern
    origin_len_pattern = re.compile(
        r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*ORIGIN\(([A-Za-z0-9_]+)\)\s*\+\s*LENGTH\(([A-Za-z0-9_]+)\)\s*;'
    )
    min_stack_pattern = re.compile(
        r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+)\s*;'
    )

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_clean = re.sub(r'/\*.*?\*/', '', line).split('//')[0].strip()

            m = origin_len_pattern.match(line_clean)
            if m:
                sym = m.group(1)
                origin_region = m.group(2)
                len_region = m.group(3)
                if origin_region in regions and len_region in regions:
                    val = regions[origin_region].origin + regions[len_region].length
                    symbols[sym] = val
                continue

            m = const_pattern.match(line_clean)
            if m:
                symbols[m.group(1)] = int(m.group(2), 16)
                continue

            m = min_stack_pattern.match(line_clean)
            if m:
                try:
                    symbols[m.group(1)] = int(m.group(2))
                except ValueError:
                    pass

    return symbols
