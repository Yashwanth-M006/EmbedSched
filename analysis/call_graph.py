import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union, Iterable

# Standard ARM general-purpose and special registers used for indirect calls
ARM_CALL_REGISTERS = {
    'r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7',
    'r8', 'r9', 'r10', 'r11', 'r12', 'ip', 'sp'
}


def extract_call_graph_and_indirect_calls(
    disassembly: Union[str, Iterable[str]]
) -> Tuple[Dict[str, Set[str]], Dict[str, List[Tuple[int, str, str]]]]:
    """
    Parses objdump -d disassembly in a single pass to extract:
      1. Direct call graph: {caller: set(callee_names)}
      2. Unresolved indirect callsites: {caller: [(addr, mnemonic, register)]}
    
    Identifies:
      - Direct calls: 'bl <target>' or 'blx <target>' with symbol in angle brackets.
      - Indirect calls: 'blx <reg>' or 'bx <reg>' (excluding 'bx lr' standard return).
    """
    call_graph: Dict[str, Set[str]] = defaultdict(set)
    indirect_calls: Dict[str, List[Tuple[int, str, str]]] = defaultdict(list)
    current_func = None

    # Matches function header: 08004120 <main_loop>:
    func_pattern = re.compile(r'^[0-9a-fA-F]+ <([^>]+)>:')
    # Matches direct calls: 8004134: f7ff fffe bl 8004130 <adc_dma_isr> or capstone's bl #0x8004130
    direct_call_pattern = re.compile(r'\bbl[x]?\s+(?:#?0x)?[0-9a-fA-F]+\s+<([^>+]+)')
    # Matches indirect register branch: 8004138: 4798 blx r3
    indirect_call_pattern = re.compile(r'^\s*([0-9a-fA-F]+):\s+.*?\b(blx|bx)\s+([a-zA-Z0-9]+)')

    lines = disassembly.splitlines() if isinstance(disassembly, str) else disassembly
    for line in lines:
        fm = func_pattern.match(line)
        if fm:
            current_func = fm.group(1)
            continue
        if not current_func:
            continue

        # Check for direct call
        cm = direct_call_pattern.search(line)
        if cm:
            call_graph[current_func].add(cm.group(1))
            continue

        # Check for indirect call (BLX <reg> or BX <reg> where reg != lr)
        im = indirect_call_pattern.search(line)
        if im:
            addr_str, mnem, reg = im.groups()
            mnem_lower = mnem.lower()
            reg_lower = reg.lower()
            # 'blx <reg>' is always an indirect call.
            # 'bx <reg>' where reg != lr is an indirect tail call / dispatch.
            is_indirect_blx = (mnem_lower == 'blx' and (reg_lower in ARM_CALL_REGISTERS or reg_lower == 'lr'))
            is_indirect_bx = (mnem_lower == 'bx' and reg_lower in ARM_CALL_REGISTERS)
            if is_indirect_blx or is_indirect_bx:
                try:
                    addr = int(addr_str, 16)
                    indirect_calls[current_func].append((addr, mnem_lower, reg_lower))
                except ValueError:
                    pass

    return dict(call_graph), dict(indirect_calls)


def build_call_graph_from_disassembly(disassembly: Union[str, Iterable[str]]) -> Dict[str, Set[str]]:
    """
    Parses objdump -d output to find all direct BL/BLX instructions, 
    mapping caller function to a set of callee functions.
    Returns: {caller_name: set([callee_name, ...])}
    """
    cg, _ = extract_call_graph_and_indirect_calls(disassembly)
    return cg


def detect_indirect_calls(disassembly: Union[str, Iterable[str]]) -> Dict[str, List[Tuple[int, str, str]]]:
    """
    Parses objdump -d output to find all indirect call instructions (BLX Rn).
    Returns: {caller_name: [(address, mnemonic, register), ...]}
    """
    _, ic = extract_call_graph_and_indirect_calls(disassembly)
    return ic
