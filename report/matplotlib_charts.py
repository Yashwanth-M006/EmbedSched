"""
report/matplotlib_charts.py

Generates real graphical charts for the AUTOSAR Schedulability Analysis using matplotlib.
Outputs PNG files.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines
import numpy as np
from typing import List
from models.autosar_task import AutosarTask
from analysis.scheduler_sim import SimulationResult

def generate_charts(
    sim: SimulationResult,
    all_tasks: List[AutosarTask],
    out_dir: str = ".",
    util_info: dict = None,
    cores: dict = None,
    lowest_tag: str = "[CALCULATED]"
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    
    # Output 1: Schedulability Dashboard
    if util_info:
        _generate_schedulability_dashboard(util_info, all_tasks, os.path.join(out_dir, "schedulability_dashboard.png"), lowest_tag)

    # Output 2: Gantt Chart
    if sim:
        _generate_gantt(sim, all_tasks, os.path.join(out_dir, "gantt_chart.png"))

    # Output 3: Response Time Table / Plot
    _generate_response_time_chart(all_tasks, os.path.join(out_dir, "response_time_chart.png"), lowest_tag)

    # Output 4: Jitter Plot
    if sim:
        _generate_jitter(sim, all_tasks, os.path.join(out_dir, "jitter_chart.png"))


def _generate_schedulability_dashboard(
    util_info: dict,
    all_tasks: List[AutosarTask],
    filepath: str,
    lowest_tag: str = "[CALCULATED]"
) -> None:
    if not util_info:
        return

    cores = sorted(util_info.keys())
    fig, ax = plt.subplots(figsize=(11, max(3.5, 1.8 * len(cores))))
    y_positions = range(len(cores))

    all_schedulable = all(t.schedulable is not False for t in all_tasks if t.period_us > 0)
    any_miss = any(t.schedulable is False for t in all_tasks if t.period_us > 0)

    for i, c_id in enumerate(cores):
        info = util_info[c_id]
        u_pct = info['utilization'] * 100.0
        bound_pct = info.get('bound', info.get('rm_bound', 1.0)) * 100.0
        algorithm = info.get('algorithm', 'RM')
        is_edf = info.get('is_edf', algorithm == 'EDF')
        pda_passed = info.get('pda_passed')

        # Color coding: Green below 69% / bound, Yellow up to 85% / 100%, Red above 85% / 100%
        if u_pct <= bound_pct and (not is_edf or pda_passed is not False):
            if u_pct <= 69.0 or is_edf:
                bar_color = '#2ecc71'
            else:
                bar_color = '#f39c12'
        elif u_pct <= 85.0:
            bar_color = '#f39c12'
        else:
            bar_color = '#e74c3c'

        ax.barh(i, u_pct, height=0.45, color=bar_color, edgecolor='#2c3e50', linewidth=1.2, alpha=0.9, zorder=3)

        if bound_pct < 99.9:
            ax.axvline(bound_pct, color='#2980b9', linestyle='--', linewidth=1.8, label=f'RM Bound ({bound_pct:.1f}%)' if i==0 else None, zorder=2)
        ax.axvline(100.0, color='#c0392b', linestyle=':', linewidth=2.0, label='100% Limit' if i==0 else None, zorder=2)

        if is_edf:
            if info.get('has_constrained_deadline'):
                status = "GUARANTEED (Demand Analysis: h(t) <= t)" if pda_passed else "FAILED (Demand h(t) > t)"
            else:
                status = "GUARANTEED" if u_pct <= 100.0 else "OVERLOAD"
        else:
            if u_pct <= bound_pct:
                status = "GUARANTEED (below RM bound)"
            elif u_pct <= 100.0:
                status = "INDETERMINATE (above RM bound, RTA verified)"
            else:
                status = "OVERLOAD (exceeds 100%)"

        ax.text(u_pct + 1.5, i, f"{u_pct:.1f}% — {status}", va='center', fontweight='bold', fontsize=10, color='#2c3e50')

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"Core {c_id} ({util_info[c_id].get('algorithm', 'RM')})" for c_id in cores], fontsize=11, fontweight='bold')
    max_u = max((info['utilization'] * 100.0 for info in util_info.values()), default=80.0)
    ax.set_xlim(0, max(140.0, max_u + 55.0))
    ax.set_xlabel("CPU Utilization (%)", fontsize=11, fontweight='bold')

    verdict_text = "SCHEDULABLE" if all_schedulable and not any_miss else ("DEADLINE MISS" if any_miss else "UNDETERMINED")
    verdict_color = "#27ae60" if all_schedulable and not any_miss else "#c0392b"
    ax.set_title(
        f"AUTOSAR Schedulability Dashboard — Per-Core CPU Utilization\n"
        f"VERDICT: {verdict_text}  {lowest_tag}",
        fontsize=12, fontweight='bold', pad=14, color=verdict_color
    )
    ax.grid(True, axis='x', linestyle='--', alpha=0.6, zorder=1)
    if any(info.get('bound', 1.0) < 0.999 for info in util_info.values()):
        ax.legend(loc='lower right', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def _generate_response_time_chart(
    all_tasks: List[AutosarTask],
    filepath: str,
    lowest_tag: str = "[CALCULATED]"
) -> None:
    periodic = [t for t in all_tasks if t.period_us > 0 and t.wcet_us > 0]
    if not periodic:
        return

    def _sort_key(t):
        return (t.core_id, t.deadline_us)
    sorted_tasks = sorted(periodic, key=_sort_key, reverse=True)

    fig, ax = plt.subplots(figsize=(11, max(4.0, 1.2 * len(sorted_tasks))))
    y_pos = range(len(sorted_tasks))

    max_dl = max(t.deadline_us for t in sorted_tasks)
    use_ms = max_dl >= 2000.0
    scale = 1000.0 if use_ms else 1.0
    unit = "ms" if use_ms else "µs"

    def _fmt_time(val_us: float) -> str:
        abs_v = abs(val_us)
        if abs_v < 0.001:
            return "0µs"
        elif abs_v < 1000.0:
            return f"{val_us:.1f}µs" if val_us % 1 != 0 else f"{val_us:.0f}µs"
        elif abs_v % 1000.0 == 0:
            return f"{val_us / 1000.0:.1f}ms"
        else:
            return f"{val_us / 1000.0:.2f}ms"

    def _fmt_dl(val_us: float) -> str:
        if val_us < 1000.0:
            return f"{val_us:.0f}µs"
        elif val_us % 1000.0 == 0:
            return f"{val_us / 1000.0:.1f}ms"
        else:
            return f"{val_us / 1000.0:.2f}ms"

    for i, t in enumerate(sorted_tasks):
        wcet = t.wcet_us / scale
        wcrt = t.wcrt_us / scale
        dl = t.deadline_us / scale
        margin = dl - wcrt
        margin_us = t.deadline_us - t.wcrt_us

        ax.barh(i, wcet, height=0.42, color='#3498db', edgecolor='#2980b9', linewidth=0.8,
                label='WCET (Execution)' if i == 0 else None, zorder=3)

        if wcrt > wcet:
            ax.barh(i, wcrt - wcet, left=wcet, height=0.42, color='#e67e22', edgecolor='#d35400', linewidth=0.8,
                    label='Interference & Blocking' if i == 0 else None, zorder=3)

        r_str = _fmt_time(t.wcrt_us)
        dl_str = _fmt_dl(t.deadline_us)
        m_str = _fmt_time(margin_us)

        if margin_us >= 0:
            ax.barh(i, margin, left=wcrt, height=0.42, color='#2ecc71', alpha=0.75, edgecolor='#27ae60', linewidth=0.8,
                    label='Safe Margin (Slack)' if i == 0 else None, zorder=3)
            label_text = f"R={r_str} | D={dl_str} (+{m_str})"
            label_color = '#27ae60'
        else:
            ax.barh(i, -margin, left=dl, height=0.42, color='#e74c3c', alpha=0.85, edgecolor='#c0392b', linewidth=0.8,
                    label='Deadline Miss (Deficit)' if i == 0 else None, zorder=3)
            label_text = f"R={r_str} | D={dl_str} (MISS {m_str})"
            label_color = '#c0392b'

        ax.plot([dl, dl], [i - 0.28, i + 0.28], color='#c0392b', linewidth=2.5,
                label='Deadline Threshold' if i == 0 else None, zorder=4)

        ax.text(max(dl, wcrt) + (max_dl / scale * 0.02), i, label_text, va='center', fontsize=9.5, fontweight='bold', color=label_color)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{t.name}  {t.wcet_tag}" for t in sorted_tasks], fontsize=10, fontweight='bold')
    ax.set_xlim(0, (max_dl / scale) * 1.55)
    ax.set_xlabel(f"Time ({unit})", fontsize=11, fontweight='bold')
    ax.set_title(
        f"Task Worst-Case Response Time (WCRT) vs. Deadline\n"
        f"Confidence: {lowest_tag} — Safe Margin (Slack) shown in green",
        fontsize=12, fontweight='bold', pad=14
    )
    ax.grid(True, axis='x', linestyle='--', alpha=0.6, zorder=1)
    ax.legend(loc='upper right', framealpha=0.9, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()



def _generate_gantt(sim: SimulationResult, all_tasks: List[AutosarTask], filepath: str) -> None:
    # ── Curated Distinct Task Palette ───────────────────────────────────────
    TASK_PALETTE = [
        '#2980b9',  # rich blue
        '#27ae60',  # emerald green
        '#d35400',  # rust / burnt orange
        '#8e44ad',  # amethyst purple
        '#16a085',  # dark teal
        '#c0392b',  # crimson
        '#2c3e50',  # slate navy
        '#f39c12',  # bright amber
        '#1abc9c',  # turquoise
        '#7f8c8d',  # neutral slate
    ]
    task_colors = {
        task.name: TASK_PALETTE[i % len(TASK_PALETTE)]
        for i, task in enumerate(all_tasks)
    }

    # Organize tasks by core
    cores = {}
    for task in all_tasks:
        if task.core_id not in cores:
            cores[task.core_id] = []
        cores[task.core_id].append(task)

    sorted_cores = sorted(cores.keys())
    num_cores = len(sorted_cores)
    hp_us = max(sim.hyperperiod_us, 100.0)

    is_explosion = sim.capped or hp_us > 1_000_000.0

    if is_explosion:
        # Full timeline is meaningless for exploded hyperperiods — render representative panel only
        num_plots = num_cores
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 4.2 * num_plots))
        if num_cores == 1:
            core_zoom_axes = {sorted_cores[0]: axes}
        else:
            core_zoom_axes = {c_id: axes[idx] for idx, c_id in enumerate(sorted_cores)}
        ax_full = None
    elif num_cores > 1:
        # Full timeline + 1 zoomed panel per core
        num_plots = 1 + num_cores
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.8 * num_plots))
        ax_full = axes[0]
        core_zoom_axes = {c_id: axes[idx + 1] for idx, c_id in enumerate(sorted_cores)}
    else:
        fig, (ax_full, ax_zoom) = plt.subplots(2, 1, figsize=(12, 8.5))
        core_zoom_axes = {sorted_cores[0]: ax_zoom} if sorted_cores else {}

    # ── Full Timeline Rendering (Skipped if Hyperperiod Explosion) ───────────
    if ax_full is not None:
        y_ticks_full = []
        y_labels_full = []
        current_y = 10
        task_y_full = {}
        separators = []

        for idx, core_id in enumerate(sorted_cores):
            if idx > 0:
                separators.append(current_y - 5)
                y_ticks_full.append(current_y)
                y_labels_full.append(f"--- Core {core_id} ---")
                current_y += 10

            c_tasks = sorted(cores[core_id], key=lambda t: t.deadline_us if (t.priority is None or t.priority == 255) else -t.priority)
            for t in c_tasks:
                y_ticks_full.append(current_y)
                y_labels_full.append(t.name)
                task_y_full[t.name] = current_y
                current_y += 10

        # Global 5px Rule: guarantees visual visibility on screen
        min_width_full = max(5.0 * (hp_us / 1400.0), 2.0)

        for interval in sim.gantt:
            y_pos = task_y_full.get(interval.task_name)
            if y_pos is not None:
                width = interval.end_us - interval.start_us
                is_subpixel = width < min_width_full
                render_width = max(width, min_width_full)
                t_color = task_colors.get(interval.task_name, '#34495e')

                rect = patches.Rectangle(
                    (interval.start_us, y_pos - 3.8), render_width, 7.6,
                    facecolor=t_color, alpha=0.88, edgecolor='#1a1a1a', linewidth=0.6, zorder=3
                )
                ax_full.add_patch(rect)
                ax_full.vlines(interval.start_us, y_pos - 3.8, y_pos + 3.8, color=t_color, linewidth=3.0, zorder=4)

                if is_subpixel:
                    ax_full.plot(
                        interval.start_us + render_width / 2.0, y_pos,
                        marker='*', markersize=6.5,
                        color='#f1c40f', markeredgecolor='#2c3e50', markeredgewidth=0.5,
                        zorder=5
                    )

                if interval.preempted:
                    ax_full.plot(interval.end_us, y_pos, marker='>', color='#e74c3c', markersize=7, zorder=6)

        for sep_y in separators:
            ax_full.axhline(sep_y, color='gray', linestyle='--', linewidth=1.5, alpha=0.8)

        ax_full.set_yticks(y_ticks_full)
        ax_full.set_yticklabels(y_labels_full, fontsize=9.5, fontweight='bold')
        ax_full.set_ylim(0, current_y + 8)
        ax_full.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax_full.set_xlabel("Time (µs)", fontsize=10, fontweight='bold')
        ax_full.set_xlim(0, hp_us)
        ax_full.set_title("Full Hyperperiod Timeline (All Cores) — * marks bars widened to ≥4px minimum width",
                          fontsize=11.5, fontweight='bold', pad=10)

        legend_handles = [
            patches.Patch(facecolor=task_colors[t.name], edgecolor='black', label=f"{t.name}")
            for t in all_tasks if t.name in task_colors
        ]
        legend_handles.append(
            mlines.Line2D([], [], color='#f1c40f', marker='*', linestyle='None',
                          markersize=7, markeredgecolor='#2c3e50', label='Widened bar (<4px, *)')
        )
        legend_handles.append(
            mlines.Line2D([], [], color='#e74c3c', marker='>', linestyle='None',
                          markersize=7, label='Preempted (>)')
        )
        ax_full.legend(handles=legend_handles, loc='upper right', ncol=min(len(legend_handles), 4),
                       fontsize=8.5, framealpha=0.92)

    # ── Zoom / Representative Window Calculation ─────────────────────────────
    if is_explosion:
        zoom_window = 30000.0  # 30 ms representative window
    elif all_tasks:
        min_period = min(t.period_us for t in all_tasks if t.period_us > 0)
        burst_wcet = sum(t.wcet_us for t in all_tasks if t.wcet_us > 0)
        if min_period >= 10000.0 and burst_wcet < 2000.0:
            zoom_candidate = max(200.0, burst_wcet * 8.0)
        else:
            zoom_candidate = max(min_period * 2.5, burst_wcet * 2.5)
        zoom_window = min(hp_us, max(100.0, min(50000.0, zoom_candidate)))
    else:
        zoom_window = min(2000.0, hp_us)
    zoom_window = max(zoom_window, 10.0)

    # ── Draw Zoomed / Representative Panels per Core ─────────────────────────
    min_width_zoom = max(5.0 * (zoom_window / 1400.0), 1.0)
    hp_ms = int(round(sim.hyperperiod_us / 1000.0))

    for idx, (core_id, ax_z) in enumerate(core_zoom_axes.items()):
        c_tasks = sorted(cores[core_id], key=lambda t: t.deadline_us if (t.priority is None or t.priority == 255) else -t.priority)
        y_ticks_core = []
        y_labels_core = []
        task_y_core = {}
        cy = 10
        for t in c_tasks:
            y_ticks_core.append(cy)
            y_labels_core.append(t.name)
            task_y_core[t.name] = cy
            cy += 10

        for interval in sim.gantt:
            if interval.core_id == core_id:
                y_pos = task_y_core.get(interval.task_name)
                if y_pos is not None and interval.start_us < zoom_window:
                    end_clipped = min(interval.end_us, zoom_window)
                    width = end_clipped - interval.start_us
                    if width > 0:
                        is_subpixel_z = width < min_width_zoom
                        render_w_z = max(width, min_width_zoom)
                        t_color = task_colors.get(interval.task_name, '#34495e')

                        rect = patches.Rectangle(
                            (interval.start_us, y_pos - 3.8), render_w_z, 7.6,
                            facecolor=t_color, alpha=0.88, edgecolor='#1a1a1a', linewidth=0.6, zorder=3
                        )
                        ax_z.add_patch(rect)
                        ax_z.vlines(interval.start_us, y_pos - 3.8, y_pos + 3.8, color=t_color, linewidth=3.0, zorder=4)

                        if is_subpixel_z:
                            ax_z.plot(
                                interval.start_us + render_w_z / 2.0, y_pos,
                                marker='*', markersize=6.5,
                                color='#f1c40f', markeredgecolor='#2c3e50', markeredgewidth=0.5,
                                zorder=5
                            )

                        if interval.preempted and interval.end_us <= zoom_window:
                            ax_z.plot(interval.end_us, y_pos, marker='>', color='#e74c3c', markersize=7, zorder=6)

        ax_z.set_yticks(y_ticks_core)
        ax_z.set_yticklabels(y_labels_core, fontsize=9.5, fontweight='bold')
        ax_z.set_ylim(0, cy + (12 if is_explosion else 4))
        ax_z.set_xlim(0, zoom_window)
        ax_z.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax_z.set_xlabel("Time (µs)", fontsize=10, fontweight='bold')

        if is_explosion:
            ax_z.set_title(
                f"Representative Schedule Window (First {zoom_window/1000:.0f}ms) — "
                f"Full simulation disabled due to hyperperiod explosion ({hp_ms:,}ms)",
                fontsize=10.5, fontweight='bold', pad=8
            )
            # Add legend in representative mode
            legend_handles = [
                patches.Patch(facecolor=task_colors[t.name], edgecolor='black', label=f"{t.name}")
                for t in c_tasks if t.name in task_colors
            ]
            legend_handles.append(
                mlines.Line2D([], [], color='#f1c40f', marker='*', linestyle='None',
                              markersize=7, markeredgecolor='#2c3e50', label='Widened bar (<4px, *)')
            )
            legend_handles.append(
                mlines.Line2D([], [], color='#e74c3c', marker='>', linestyle='None',
                              markersize=7, label='Preempted (>)')
            )
            ax_z.legend(handles=legend_handles, loc='upper right', ncol=min(len(legend_handles), 4),
                        fontsize=8.5, framealpha=0.92)
        else:
            ax_z.set_title(
                f"Zoomed Inset — Core {core_id} (First {zoom_window:.0f} µs) — Detailed Interleaving",
                fontsize=11, fontweight='bold', pad=8
            )

    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def _generate_jitter(sim: SimulationResult, all_tasks: List[AutosarTask], filepath: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.2))
    
    task_map = {t.name: t for t in all_tasks}
    colors = plt.cm.tab10.colors
    c_idx = 0
    
    for task_name, start_times in sim.start_times.items():
        if not start_times: continue
        task = task_map.get(task_name)
        if not task or task.period_us <= 0: continue
        
        jitters = []
        for i, actual_start in enumerate(start_times):
            ideal_start = i * task.period_us
            jitter = min(abs(actual_start - ideal_start), task.period_us)
            jitters.append(jitter)
            
        x_vals = list(range(len(jitters)))
        ls = '--' if len(jitters) <= 2 else '-'
        ax.plot(x_vals, jitters, marker='o', markersize=6 if len(jitters) > 2 else 8,
                linestyle=ls, label=task_name, color=colors[c_idx % len(colors)], alpha=0.9)
        c_idx += 1
        
    ax.set_xlabel("Activation #", fontsize=10, fontweight='bold')
    ax.set_ylabel("Jitter (µs)", fontsize=10, fontweight='bold')
    ax.set_title("Start-time Jitter per Task", fontsize=12, fontweight='bold')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    if c_idx > 0:
        ax.legend(title="Tasks", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    ax.text(
        0.5, -0.15,
        "Note: Jitter on single-task cores reflects simulation granularity/drift, not real-world preemption delay.",
        transform=ax.transAxes, ha='center', fontsize=9, style='italic', color='#555555'
    )
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()
