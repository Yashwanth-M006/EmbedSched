from typing import Dict, Set, Tuple, List

def worst_case_stack_depth(
    call_graph: Dict[str, Set[str]],
    stack_usage: Dict[str, int],
    entry: str,
    visited: Set[str] = None
) -> Tuple[int, List[str], bool]:
    """
    Returns (max_bytes, call_chain, has_recursion).
    has_recursion=True means depth is unbounded — flag separately.

    IMPORTANT: has_recursion is propagated independently of depth.
    A callee that is shallower but recursive does NOT override the
    deepest non-recursive callee for the call chain — but the
    has_recursion flag is still set so the caller reports it.
    """
    if visited is None:
        visited = set()
    if entry in visited:
        return (0, [entry], True)   # cycle detected — unbounded depth
        
    visited = visited | {entry}
    own = stack_usage.get(entry, 0)
    callees = call_graph.get(entry, set())
    
    if not callees:
        return (own, [entry], False)

    best_depth = -1
    best_chain: List[str] = []
    # Track recursion separately — ANY recursive callee sets this True
    # regardless of whether that callee is the deepest path.
    any_recursion = False

    for callee in callees:
        depth, chain, recurse = worst_case_stack_depth(
            call_graph, stack_usage, callee, visited
        )
        if recurse:
            any_recursion = True          # propagate unconditionally
        if depth > best_depth:
            best_depth = depth
            best_chain = chain

    if best_depth < 0:
        best_depth = 0

    total = own + best_depth
    return (total, [entry] + best_chain, any_recursion)

def analyze_all_stacks(call_graph: Dict[str, Set[str]], stack_usage: Dict[str, int], entry_points: List[str]) -> Tuple[int, List[str], bool]:
    """
    Finds the absolute worst-case stack depth among all known entry points.
    Returns (max_depth, deepest_chain, has_recursion_anywhere).
    """
    max_d = 0
    max_c: List[str] = []
    has_rec = False
    
    for ep in entry_points:
        d, c, r = worst_case_stack_depth(call_graph, stack_usage, ep)
        if r:
            has_rec = True        # recursion flag is OR'd across all entry points
        if d > max_d:
            max_d = d
            max_c = c
            
    return max_d, max_c, has_rec
