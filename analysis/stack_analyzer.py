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

    Uses an explicit work stack (iterative DFS) to prevent Python RecursionError
    on deep firmware call chains.
    """
    if visited is None:
        visited = set()
    if entry in visited:
        return (0, [entry], True)

    root_callees = sorted(list(call_graph.get(entry, set())))
    ancestors = set(visited)
    ancestors.add(entry)

    # stack frames: [node, callees, callee_idx, best_depth, best_chain, any_recursion]
    stack = [[entry, root_callees, 0, -1, [], False]]
    memo: Dict[str, Tuple[int, List[str], bool]] = {}

    while stack:
        frame = stack[-1]
        node, callees, idx, best_depth, best_chain, any_rec = frame

        if idx < len(callees):
            callee = callees[idx]
            frame[2] += 1

            if callee in ancestors:
                # Cycle / recursion detected
                frame[5] = True
                if 0 > frame[3]:
                    frame[3] = 0
                    frame[4] = [callee]
            elif callee in memo:
                c_depth, c_chain, c_rec = memo[callee]
                if c_rec:
                    frame[5] = True
                if c_depth > frame[3]:
                    frame[3] = c_depth
                    frame[4] = c_chain
            else:
                ancestors.add(callee)
                c_callees = sorted(list(call_graph.get(callee, set())))
                stack.append([callee, c_callees, 0, -1, [], False])
        else:
            stack.pop()
            ancestors.discard(node)
            own = stack_usage.get(node, 0)
            if best_depth < 0:
                best_depth = 0
            total_depth = own + best_depth
            final_chain = [node] + best_chain
            memo[node] = (total_depth, final_chain, any_rec)

            if stack:
                parent = stack[-1]
                if any_rec:
                    parent[5] = True
                if total_depth > parent[3]:
                    parent[3] = total_depth
                    parent[4] = final_chain

    return memo[entry]

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
