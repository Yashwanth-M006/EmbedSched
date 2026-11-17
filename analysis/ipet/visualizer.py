"""
analysis/ipet/visualizer.py — Control Flow Graph (CFG) Visualization using Matplotlib

Renders an annotated, publication-quality CFG for a function:
  - Hierarchical top-to-bottom layout with horizontal layering
  - Color-coded basic block boxes (Entry, Exit, Loop Header, Standard)
  - Color-coded edges (Fall-Through, Branch Taken, Unconditional Branch, Loop Back-Edge)
  - Disassembly instruction previews inside each basic block
  - Distinct curved rendering for loop back-edges
  - Comprehensive legend and architecture metrics
"""

import os
import tempfile

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib")

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import matplotlib.pyplot as plt

from .cfg_builder import EdgeType, FunctionCFG


def _compute_hierarchical_layout(
    cfg: FunctionCFG,
    node_width: float = 3.6,
    node_height: float = 2.2,
    x_gap: float = 1.0,
    y_gap: float = 1.2,
) -> Dict[str, Tuple[float, float]]:
    """
    Computes (x, y) coordinates for each basic block in a top-down hierarchical layout.
    Breaks back-edges to form a DAG, computes rank/layer per node, and centers nodes horizontally.
    """
    blocks = [bid for bid, bb in cfg.blocks.items() if bb.instructions and (bb.predecessors or bid == cfg.entry_bb)]
    if not blocks:
        blocks = list(cfg.blocks.keys())

    # Build forward DAG adjacency ignoring back-edges
    forward_succs: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {bid: 0 for bid in blocks}

    for edge in cfg.edges:
        if (edge.src_id, edge.dst_id) in cfg.back_edges:
            continue
        if edge.src_id in in_degree and edge.dst_id in in_degree:
            forward_succs[edge.src_id].append(edge.dst_id)
            in_degree[edge.dst_id] += 1

    # Compute layer using longest-path leveling from entry
    layers: Dict[str, int] = {bid: 0 for bid in blocks}
    queue = deque([bid for bid in blocks if in_degree[bid] == 0])
    if cfg.entry_bb in blocks and cfg.entry_bb not in queue:
        queue.append(cfg.entry_bb)

    visited_count = 0
    while queue:
        u = queue.popleft()
        visited_count += 1
        for v in forward_succs[u]:
            if layers[v] < layers[u] + 1:
                layers[v] = layers[u] + 1
            in_degree[v] -= 1
            if in_degree[v] <= 0:
                queue.append(v)

    # For any unplaced/cycle nodes, assign based on BFS from entry
    if visited_count < len(blocks):
        bfs_queue = deque([(cfg.entry_bb, 0)])
        bfs_visited = {cfg.entry_bb}
        while bfs_queue:
            curr, d = bfs_queue.popleft()
            layers[curr] = max(layers.get(curr, 0), d)
            for succ in cfg.blocks[curr].successors:
                if succ in blocks and succ not in bfs_visited:
                    bfs_visited.add(succ)
                    bfs_queue.append((succ, d + 1))

    # Group nodes by layer
    layer_to_nodes: Dict[int, List[str]] = defaultdict(list)
    for bid in blocks:
        layer_to_nodes[layers[bid]].append(bid)

    # Sort nodes within each layer by address to keep deterministic flow
    positions: Dict[str, Tuple[float, float]] = {}
    for layer, nodes in layer_to_nodes.items():
        nodes.sort(key=lambda b: cfg.blocks[b].address)
        num_nodes = len(nodes)
        total_width = num_nodes * node_width + (num_nodes - 1) * x_gap
        start_x = -total_width / 2.0 + node_width / 2.0
        for idx, bid in enumerate(nodes):
            x = start_x + idx * (node_width + x_gap)
            y = -layer * (node_height + y_gap)
            positions[bid] = (x, y)

    return positions


def visualize_cfg(
    cfg: FunctionCFG,
    output_path: Optional[str] = None,
    show: bool = False,
    title: Optional[str] = None,
    max_insns_per_block: int = 6,
    dpi: int = 200,
    dark_theme: bool = False,
) -> plt.Figure:
    """
    Renders a FunctionCFG using Matplotlib.
    
    Args:
        cfg: FunctionCFG instance from build_cfg.
        output_path: Path to save generated image (e.g. .png or .pdf).
        show: If True, calls plt.show().
        title: Custom plot title.
        max_insns_per_block: Maximum instruction lines to preview in each block.
        dpi: Output resolution.
        dark_theme: If True, uses dark background; defaults to False (white background).

    Returns:
        matplotlib.figure.Figure
    """
    # Filter to reachable blocks (or all if none filtered)
    reachable_blocks = {
        bid: bb for bid, bb in cfg.blocks.items()
        if bb.instructions and (bb.predecessors or bid == cfg.entry_bb)
    }
    if not reachable_blocks:
        reachable_blocks = cfg.blocks

    node_width = 3.8
    node_height = 2.4
    positions = _compute_hierarchical_layout(cfg, node_width=node_width, node_height=node_height)

    # Determine bounding box
    if positions:
        all_x = [p[0] for p in positions.values()]
        all_y = [p[1] for p in positions.values()]
        min_x, max_x = min(all_x) - node_width, max(all_x) + node_width
        min_y, max_y = min(all_y) - node_height, max(all_y) + node_height
    else:
        min_x, max_x, min_y, max_y = -5, 5, -5, 5

    fig_w = max(12, min(36, (max_x - min_x) * 1.5))
    fig_h = max(8, min(42, (max_y - min_y) * 1.3))

    # ── Color Palette Configuration ───────────────────────────────────────────
    if dark_theme:
        bg_canvas = "#181825"
        bg_ax = "#1e1e2e"

        ENTRY_BG = "#a6e3a1"      # Green
        ENTRY_EDGE = "#40a02b"
        EXIT_BG = "#f38ba8"       # Red/Coral
        EXIT_EDGE = "#d20f39"
        LOOP_BG = "#f9e2af"       # Yellow/Gold
        LOOP_EDGE = "#df8e1d"
        NORMAL_BG = "#cdd6f4"     # Light Slate
        NORMAL_EDGE = "#585b70"

        TEXT_DARK = "#11111b"
        TEXT_MUTED = "#45475a"
        TEXT_INSNS = "#181825"

        COLOR_FALL_THROUGH = "#89b4fa"      # Blue
        COLOR_BRANCH_TAKEN = "#a6e3a1"      # Green
        COLOR_UNCONDITIONAL = "#cba6f7"     # Purple
        COLOR_BACK_EDGE = "#f38ba8"         # Coral Red

        PILL_BG = "#181825"
        LEGEND_BG = "#181825"
        LEGEND_EDGE = "#45475a"
        LEGEND_TEXT = "#cdd6f4"
        TITLE_COLOR = "#cdd6f4"
    else:
        bg_canvas = "#ffffff"
        bg_ax = "#ffffff"

        ENTRY_BG = "#e8f5e9"      # Clean soft green
        ENTRY_EDGE = "#2e7d32"    # Dark green border
        EXIT_BG = "#ffebee"       # Clean soft red/pink
        EXIT_EDGE = "#c62828"     # Dark red border
        LOOP_BG = "#fff8e1"       # Clean soft amber
        LOOP_EDGE = "#d97706"     # Dark amber border
        NORMAL_BG = "#f8fafc"     # Crisp slate-50 off-white
        NORMAL_EDGE = "#64748b"   # Slate-500 border

        TEXT_DARK = "#0f172a"     # Slate-900 header
        TEXT_MUTED = "#64748b"    # Slate-500
        TEXT_INSNS = "#1e293b"    # Slate-800 instructions

        COLOR_FALL_THROUGH = "#1d4ed8"      # Deep Royal Blue
        COLOR_BRANCH_TAKEN = "#15803d"      # Deep Forest Green
        COLOR_UNCONDITIONAL = "#7c3aed"     # Deep Violet
        COLOR_BACK_EDGE = "#dc2626"         # High-contrast Crimson

        PILL_BG = "#ffffff"
        LEGEND_BG = "#ffffff"
        LEGEND_EDGE = "#cbd5e1"
        LEGEND_TEXT = "#0f172a"
        TITLE_COLOR = "#0f172a"

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_facecolor(bg_ax)
    fig.patch.set_facecolor(bg_canvas)

    # ── Draw Edges ────────────────────────────────────────────────────────────
    for edge in cfg.edges:
        if edge.src_id not in positions or edge.dst_id not in positions:
            continue
        src_pos = positions[edge.src_id]
        dst_pos = positions[edge.dst_id]

        is_back = (edge.src_id, edge.dst_id) in cfg.back_edges

        # Determine edge styling
        if is_back:
            edge_color = COLOR_BACK_EDGE
            linestyle = "dashed"
            linewidth = 2.4
            rad = -0.45 if src_pos[0] >= dst_pos[0] else 0.45
        elif edge.edge_type == EdgeType.BRANCH_TAKEN:
            edge_color = COLOR_BRANCH_TAKEN
            linestyle = "dashed"
            linewidth = 1.8
            rad = 0.15 if src_pos[0] < dst_pos[0] else -0.15
        elif edge.edge_type == EdgeType.BRANCH_UNCONDITIONAL:
            edge_color = COLOR_UNCONDITIONAL
            linestyle = "solid"
            linewidth = 2.0
            rad = 0.2 if src_pos[0] < dst_pos[0] else -0.2
        else:
            edge_color = COLOR_FALL_THROUGH
            linestyle = "solid"
            linewidth = 1.8
            rad = 0.05 if src_pos[0] != dst_pos[0] else 0.0

        # Anchor points: src bottom, dst top
        start_pt = (src_pos[0], src_pos[1] - node_height * 0.45)
        end_pt = (dst_pos[0], dst_pos[1] + node_height * 0.45)

        arrow = FancyArrowPatch(
            start_pt,
            end_pt,
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            color=edge_color,
            linestyle=linestyle,
            linewidth=linewidth,
            mutation_scale=15,
            zorder=2,
            alpha=0.9,
        )
        ax.add_patch(arrow)

        # Draw edge label if back-edge or taken branch
        if is_back:
            mid_x = (start_pt[0] + end_pt[0]) / 2.0 + rad * 1.5
            mid_y = (start_pt[1] + end_pt[1]) / 2.0
            lbl = f"loop ({edge.cost_cycles}c)" if edge.cost_cycles > 0 else "loop back-edge"
            ax.text(
                mid_x, mid_y, lbl,
                color=COLOR_BACK_EDGE,
                fontsize=7.5,
                fontweight="bold",
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=PILL_BG, edgecolor=COLOR_BACK_EDGE, alpha=0.92),
                zorder=4,
            )
        elif edge.cost_cycles > 0:
            # Draw subtle cost tag along the edge
            mid_x = (start_pt[0] + end_pt[0]) / 2.0 + rad * 0.8
            mid_y = (start_pt[1] + end_pt[1]) / 2.0
            ax.text(
                mid_x, mid_y, f"{edge.cost_cycles}c",
                color=edge_color,
                fontsize=6.5,
                fontweight="bold",
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.15", facecolor=PILL_BG, edgecolor=edge_color, alpha=0.92),
                zorder=4,
            )

    # ── Draw Nodes (Basic Blocks) ─────────────────────────────────────────────
    for bid, pos in positions.items():
        bb = cfg.blocks[bid]
        is_entry = (bid == cfg.entry_bb)
        is_exit = (bid in cfg.exit_bbs)
        is_loop = bb.is_loop_header

        if is_entry:
            facecolor = ENTRY_BG
            edgecolor = ENTRY_EDGE
            badge = "[ENTRY]"
        elif is_loop:
            facecolor = LOOP_BG
            edgecolor = LOOP_EDGE
            bound_str = f" | bound={bb.loop_bound}" if bb.loop_bound is not None else ""
            badge = f"[{bb.loop_id or 'LOOP'}{bound_str}]"
        elif is_exit:
            facecolor = EXIT_BG
            edgecolor = EXIT_EDGE
            badge = "[EXIT / RETURN]"
        else:
            facecolor = NORMAL_BG
            edgecolor = NORMAL_EDGE
            badge = f"BB ({len(bb.instructions)} insns)"

        # Draw card container
        x, y = pos
        rect = FancyBboxPatch(
            (x - node_width / 2.0, y - node_height / 2.0),
            node_width,
            node_height,
            boxstyle="round,pad=0.15,rounding_size=0.18",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=2.2 if (is_loop or is_entry or is_exit) else 1.2,
            zorder=3,
        )
        ax.add_patch(rect)

        # Text: Header
        header_text = f"{bid} {badge}\n0x{bb.address:08x} .. 0x{bb.end_address:08x}"
        ax.text(
            x,
            y + node_height * 0.32,
            header_text,
            fontsize=8.5,
            fontweight="bold",
            color=TEXT_DARK,
            ha="center",
            va="center",
            family="monospace",
            zorder=4,
        )

        # Divider line
        div_y = y + node_height * 0.16
        ax.plot(
            [x - node_width * 0.44, x + node_width * 0.44],
            [div_y, div_y],
            color=edgecolor,
            linewidth=0.8,
            linestyle="-",
            zorder=4,
        )

        # Text: Disassembly lines
        insn_lines = []
        display_insns = bb.instructions[:max_insns_per_block]
        for ins in display_insns:
            insn_lines.append(f"{ins.address & 0xffff:04x}: {ins.mnemonic:<6} {ins.op_str}")
        if len(bb.instructions) > max_insns_per_block:
            insn_lines.append(f"... (+{len(bb.instructions) - max_insns_per_block} more)")

        body_text = "\n".join(insn_lines)
        ax.text(
            x - node_width * 0.42,
            y - node_height * 0.15,
            body_text,
            fontsize=7.2,
            color=TEXT_INSNS,
            ha="left",
            va="center",
            family="monospace",
            zorder=4,
        )

    # ── Legend & Metadata Banner ──────────────────────────────────────────────
    legend_elements = [
        mpatches.Patch(facecolor=ENTRY_BG, edgecolor=ENTRY_EDGE, label="Entry Block"),
        mpatches.Patch(facecolor=LOOP_BG, edgecolor=LOOP_EDGE, label="Loop Header Block"),
        mpatches.Patch(facecolor=EXIT_BG, edgecolor=EXIT_EDGE, label="Exit / Return Block"),
        mpatches.Patch(facecolor=NORMAL_BG, edgecolor=NORMAL_EDGE, label="Standard Basic Block"),
        plt.Line2D([0], [0], color=COLOR_FALL_THROUGH, lw=2, label="Fall-Through Edge"),
        plt.Line2D([0], [0], color=COLOR_BRANCH_TAKEN, lw=2, ls="--", label="Branch Taken Edge"),
        plt.Line2D([0], [0], color=COLOR_UNCONDITIONAL, lw=2, label="Unconditional Branch"),
        plt.Line2D([0], [0], color=COLOR_BACK_EDGE, lw=2.4, ls="--", label="Loop Back-Edge (Cycle)"),
    ]

    leg = ax.legend(
        handles=legend_elements,
        loc="upper right",
        facecolor=LEGEND_BG,
        edgecolor=LEGEND_EDGE,
        fontsize=9,
        labelcolor=LEGEND_TEXT,
        framealpha=0.95,
    )
    leg.set_zorder(10)

    # Title & Stats
    if not title:
        title = f"Control Flow Graph (CFG) — Function: {cfg.name}()"
    stats_str = (
        f"Blocks: {len(cfg.blocks)} | "
        f"Edges: {len(cfg.edges)} | "
        f"Loop Headers: {sum(1 for b in cfg.blocks.values() if b.is_loop_header)} | "
        f"Back-Edges: {len(cfg.back_edges)}"
    )

    ax.set_title(
        f"{title}\n{stats_str}",
        fontsize=13,
        fontweight="bold",
        color=TITLE_COLOR,
        pad=18,
        family="sans-serif",
    )

    ax.set_xlim(min_x - 1.0, max_x + 1.0)
    ax.set_ylim(min_y - 1.0, max_y + 1.5)
    ax.axis("off")
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"[CFG Visualizer] Saved CFG visualization to: {output_path}")

    if show:
        plt.show()

    return fig


if __name__ == "__main__":
    import argparse
    from .cfg_builder import extract_instructions_from_elf, build_cfg
    from .loop_bound_extractor import extract_loop_bounds
    from .microarch import annotate_edges

    parser = argparse.ArgumentParser(
        description="Extract and visualize Control Flow Graph (CFG) for ARM Cortex-M firmware functions."
    )
    parser.add_argument("--elf", required=True, help="Path to firmware ELF binary")
    parser.add_argument("--function", required=True, help="Target function symbol name")
    parser.add_argument(
        "--output",
        default="reports/charts/cfg.png",
        help="Path for output image (default: reports/charts/cfg.png)",
    )
    parser.add_argument("--arch", default="cortex-m4", help="Core architecture (default: cortex-m4)")
    parser.add_argument("--wait-states", type=int, default=5, help="Flash wait states (default: 5)")
    parser.add_argument("--dpi", type=int, default=180, help="Resolution in DPI (default: 180)")
    parser.add_argument("--max-loop-bound", type=int, default=1000, help="Fallback max loop bound")
    parser.add_argument("--opt-info", default=None, help="Path to GCC -fopt-info-loop output file")
    parser.add_argument("--dark", action="store_true", help="Render in dark theme instead of white background")
    args = parser.parse_args()

    insn_dict = extract_instructions_from_elf(args.elf, target_function=args.function)
    if args.function not in insn_dict:
        print(f"Error: Function '{args.function}' not found in {args.elf}")
        exit(1)

    cfg = build_cfg(args.function, insn_dict[args.function])
    # Annotate loop bounds from Phase 3
    lb_res = extract_loop_bounds(
        cfg,
        elf_path=args.elf,
        opt_info_path=args.opt_info,
        max_loop_bound=args.max_loop_bound,
    )
    print(f"[Phase 3] Resolved loop bounds: {lb_res.bounds} (provenance: {lb_res.sources})")

    # Annotate microarchitectural edge costs from Phase 4
    edge_costs = annotate_edges(cfg, arch=args.arch, wait_states=args.wait_states)
    print(f"[Phase 4] Microarchitectural edge annotation: {len(edge_costs)} edges annotated with cycle costs.")

    visualize_cfg(cfg, output_path=args.output, dpi=args.dpi, dark_theme=args.dark)


