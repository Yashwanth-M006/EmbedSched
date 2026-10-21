import re
from collections import defaultdict
from typing import Dict, Set, Union, Iterable

def build_call_graph_from_disassembly(disassembly: Union[str, Iterable[str]]) -> Dict[str, Set[str]]:
    """
    Parses objdump -d output to find all BL/BLX instructions, 
    mapping caller function to a set of callee functions.
    Supports either full string or an iterable/generator of lines to optimize memory.
    Returns: {caller_name: set([callee_name, ...])}
    """
    call_graph = defaultdict(set)
    current_func = None
    
    # Matches: 08004120 <main_loop>:
    func_pattern = re.compile(r'^[0-9a-f]+ <([^>]+)>:')
    # Matches: 8004134: f7ff fffe bl 8004130 <adc_dma_isr> or capstone's bl #0x8004130
    call_pattern = re.compile(r'\bbl[x]?\s+(?:#0x)?[0-9a-fA-F]+\s+<([^>+]+)')

    lines = disassembly.splitlines() if isinstance(disassembly, str) else disassembly
    for line in lines:
        fm = func_pattern.match(line)
        if fm:
            current_func = fm.group(1)
            continue
        if current_func:
            cm = call_pattern.search(line)
            if cm:
                call_graph[current_func].add(cm.group(1))
                
    return dict(call_graph)
