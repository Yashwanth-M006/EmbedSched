"""
report/autosar_report.py

Terminal report section for AUTOSAR Schedulability Analysis.

Produces six visual outputs:
  1. Schedulability Dashboard — per-core utilization bars + verdict
  2. Task-to-Function Mapping Table — shows where each WCET came from
  3. Response Time Table — WCET [tag], WCRT, deadline, margin (color-coded)
  4. Gantt Chart — ASCII execution timeline (from gantt_chart.py)
  5. Jitter Table — start-time variation analysis (from gantt_chart.py)
  6. Warning Flags summary — injected findings

Confidence note is always appended at the bottom of the section, consistent
with the existing tool philosophy.
"""

from typing import List, Dict, Optional
from models.autosar_task import AutosarTask
from analysis.scheduler_sim import SimulationResult
from report.gantt_chart import render_gantt_chart, render_jitter_table
import sys
import os

# ---------------------------------------------------------------------------
# ANSI color helpers (dynamic: disabled if stdout is redirected to file/pipe)
# ---------------------------------------------------------------------------

def _use_color() -> bool:
    if os.environ.get('FORCE_COLOR') == '1':
        return True
    if os.environ.get('NO_COLOR') == '1':
        return False
    return sys.stdout.isatty()

def _red(s):    return f"\033[91m{s}\033[0m" if _use_color() else str(s)
def _yellow(s): return f"\033[93m{s}\033[0m" if _use_color() else str(s)
def _green(s):  return f"\033[92m{s}\033[0m" if _use_color() else str(s)
def _cyan(s):   return f"\033[96m{s}\033[0m" if _use_color() else str(s)
def _bold(s):   return f"\033[1m{s}\033[0m" if _use_color() else str(s)
def _dim(s):    return f"\033[2m{s}\033[0m" if _use_color() else str(s)

class _ColorPalette:
    @property
    def RESET(self): return "\033[0m" if _use_color() else ""
    @property
    def BOLD(self): return "\033[1m" if _use_color() else ""
    @property
    def RED(self): return "\033[91m" if _use_color() else ""
    @property
    def YELLOW(self): return "\033[93m" if _use_color() else ""
    @property
    def GREEN(self): return "\033[92m" if _use_color() else ""
    @property
    def CYAN(self): return "\033[96m" if _use_color() else ""
    @property
    def WHITE(self): return "\033[97m" if _use_color() else ""
    @property
    def DIM(self): return "\033[2m" if _use_color() else ""
    @property
    def MAGENTA(self): return "\033[95m" if _use_color() else ""

C = _ColorPalette()


# ---------------------------------------------------------------------------
# Utilization bar
# ---------------------------------------------------------------------------

BAR_WIDTH = 40   # characters for the bar

def _util_bar(utilization: float, rm_bound: float, info: dict = None) -> str:
    """
    Render a coloured ASCII utilization bar.

      [█████████████████░░░░░░░░░░░░░░░░░░░░░░]  47.2% / RM bound 75.7%

    Green  = below RM bound / demand analysis satisfied
    Yellow = above RM bound but below 100% (indeterminate)
    Red    = above 100% / deadline miss
    """
    if info is None:
        info = {}

    pct = min(utilization, 1.0)
    filled = int(pct * BAR_WIDTH)
    bar_chars = '█' * filled + '░' * (BAR_WIDTH - filled)

    algorithm = info.get('algorithm', 'RM')
    is_edf = info.get('is_edf', algorithm == 'EDF')
    has_constrained = info.get('has_constrained_deadline', False)
    pda_passed = info.get('pda_passed')

    if is_edf:
        if has_constrained:
            bound_str = "EDF bound: 100.0% (constrained deadline)"
            if pda_passed is False:
                color = C.RED
                verdict = _red("DEADLINE MISS (demand analysis: h(t) > t)")
            elif pda_passed is True:
                color = C.GREEN
                verdict = _green("GUARANTEED (demand analysis: h(t) <= t)")
            else:
                color = C.YELLOW
                verdict = _yellow("INDETERMINATE (demand analysis needed)")
        else:
            bound_str = "EDF bound: 100.0%"
            if utilization > 1.0:
                color = C.RED
                verdict = _red("OVERLOADED (above EDF bound)")
            else:
                color = C.GREEN
                verdict = _green("GUARANTEED (below EDF bound)")
    else:
        bound_str = f"RM bound: {rm_bound*100:.1f}%"
        if utilization > 1.0:
            color = C.RED
            verdict = _red("OVERLOADED")
        elif utilization > rm_bound:
            color = C.YELLOW
            verdict = _yellow("INDETERMINATE (above RM bound)")
        else:
            color = C.GREEN
            verdict = _green("GUARANTEED (below RM bound)")

    rm_col = min(int(rm_bound * BAR_WIDTH), BAR_WIDTH - 1)
    bar_display = bar_chars[:rm_col] + '|' + bar_chars[rm_col:]   # mark bound

    return (
        f"{color}[{bar_display}]{C.RESET}  "
        f"{utilization*100:.1f}%  {bound_str}  →  {verdict}"
    )


# ---------------------------------------------------------------------------
# Main print function
# ---------------------------------------------------------------------------

def print_autosar_report(
    tasks: List[AutosarTask],
    all_tasks_with_isrs: List[AutosarTask],
    util_info: Dict[int, Dict],
    sim: Optional[SimulationResult],
    isr_task_names: set,
    wcet_confidence_note: str,
    deadlock_findings: list = None,
    lowest_confidence_tag: str = "[CALCULATED]",
    charts_dir: Optional[str] = None,
) -> None:
    """
    Print the full AUTOSAR Schedulability Analysis section to stdout.

    Args:
        tasks                : Periodic tasks (AutosarTask, with WCET + RTA filled)
        all_tasks_with_isrs  : tasks + ISR pseudo-tasks combined
        util_info            : {core_id: {utilization, rm_bound, ...}} from rta_engine
        sim                  : SimulationResult from scheduler_sim (may be None if skipped)
        isr_task_names       : set of ISR task names (for display differentiation)
        wcet_confidence_note : Propagated confidence tag string for the section footer
        deadlock_findings    : Findings from check_deadlock_risk (may be None or [])
        lowest_confidence_tag: Lowest confidence tag among all inputs
        charts_dir           : Optional directory containing generated charts
    """
    print(f"\n{'='*78}")
    print(_bold(" AUTOSAR SCHEDULABILITY ANALYSIS"))
    print(f"{'='*78}")

    # ── Deadlock banner (shown prominently before everything else) ──────────
    if deadlock_findings:
        print()
        print(f"  {C.RED}{C.BOLD}⚠  DEADLOCK_RISK  ⚠{C.RESET}")
        print(f"  {C.RED}{'─' * 40}{C.RESET}")
        for f in deadlock_findings:
            for line in f.message.splitlines():
                print(f"  {C.RED}{line}{C.RESET}")
    # ── Executive Summary Table ──────────────────────────────────────────────
    print(f"\n{_bold('EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW')}")
    hdr_sum = f"  {'Task':<22} {'Period µs':>10} {'WCET µs':>9} {'R µs':>9} {'D µs':>9} {'Margin µs':>11} {'Verdict':>8}"
    sep_sum = "─" * (len(hdr_sum) - 2)
    print(f"  {sep_sum}")
    print(hdr_sum)
    print(f"  {sep_sum}")

    all_pass = True
    any_fail = False
    for t in sorted(all_tasks_with_isrs, key=lambda x: (x.core_id, -x.priority)):
        p_str    = f"{t.period_us:.0f}" if t.period_us > 0 else "async"
        wcet_str = f"{t.wcet_us:.2f}" if t.wcet_us > 0 else "???"
        r_str    = f"{t.wcrt_us:.2f}" if t.wcrt_us > 0 else "n/a"
        d_str    = f"{t.deadline_us:.0f}" if t.deadline_us > 0 else "n/a"
        m_str    = f"{t.margin_us:.2f}" if t.schedulable is not None else "n/a"

        if t.schedulable is False:
            all_pass = False
            any_fail = True
            v_col = _red(f"{'MISS':>8}")
            n_col = _red(f"{t.name:<22}")
            m_col = _red(f"{m_str:>11}")
        elif t.schedulable is True:
            v_col = _green(f"{'PASS':>8}")
            n_col = f"{t.name:<22}"
            m_col = _green(f"{m_str:>11}")
        else:
            all_pass = False
            v_col = _yellow(f"{'UNDET':>8}")
            n_col = f"{t.name:<22}"
            m_col = f"{m_str:>11}"

        print(f"  {n_col} {p_str:>10} {wcet_str:>9} {r_str:>9} {d_str:>9} {m_col} {v_col}")

    print(f"  {sep_sum}")
    tag_sfx = f" {_cyan(lowest_confidence_tag)}"
    if any_fail:
        print(f"  Overall: {_red('FAIL')}{tag_sfx} — deadline miss detected")
    elif all_pass:
        if deadlock_findings:
            print(f"  Overall: {_yellow('PASS')}{tag_sfx} — all tasks meet timing deadlines  {_yellow('⚠ DEADLOCK_RISK DETECTED')}")
        else:
            print(f"  Overall: {_green('PASS')}{tag_sfx} — all tasks meet deadlines")
    else:
        print(f"  Overall: {_yellow('UNDETERMINED')}{tag_sfx} — insufficient timing data")
    print()

    print(f"\n{_bold('1. TASK → FUNCTION MAPPING')}")
    hdr_1 = f"  {'AUTOSAR Task':<24} {'Entry Function':<26} {'WCET (µs)':<12} {'Source':<16} {'Core'}"
    sep_1 = "─" * (len(hdr_1) - 2)
    print(f"  {sep_1}")
    print(hdr_1)
    print(f"  {sep_1}")
    for t in sorted(all_tasks_with_isrs, key=lambda x: (x.core_id, -x.priority)):
        kind = "ISR" if t.is_isr else f"Core {t.core_id}"
        wcet_str = f"{t.wcet_us:.2f}" if t.wcet_us > 0 else "???"
        tag_col = _cyan(f"{t.wcet_tag:<16}")
        print(
            f"  {t.name:<24} {t.function:<26} "
            f"{wcet_str:<12} {tag_col} [{kind}]"
        )
    print(f"  {sep_1}")
    print()

    # ── 2. Schedulability Dashboard ─────────────────────────────────────────
    print(_bold("2. SCHEDULABILITY DASHBOARD"))
    for core_id, info in sorted(util_info.items()):
        print(f"\n  Core {core_id}  ({info['task_count']} periodic tasks):")
        print(f"    {_util_bar(info['utilization'], info.get('bound', info.get('rm_bound', 1.0)), info)}")

    # Overall verdict — append the propagated confidence tag
    all_schedulable = all(t.schedulable is not False for t in all_tasks_with_isrs)
    any_miss = any(t.schedulable is False for t in all_tasks_with_isrs)
    conf_suffix = f"  {_cyan(lowest_confidence_tag)}"
    print()
    if any_miss:
        print(f"  {_red('● VERDICT: NOT SCHEDULABLE')}  — deadline miss(es) detected by RTA.{conf_suffix}")
    elif all_schedulable:
        print(f"  {_green('● VERDICT: SCHEDULABLE')}  — all tasks meet their deadlines (per RTA).{conf_suffix}")
        if deadlock_findings:
            print(f"    {_yellow('⚠ WARNING: DEADLOCK_RISK detected — system may freeze at runtime despite')}")
            print(f"      {_yellow('meeting timing deadlines. See findings for details.')}")
    else:
        print(f"  {_yellow('● VERDICT: UNDETERMINED')}  — some tasks have insufficient WCET data.{conf_suffix}")
    print()

    # ── 3. Response Time Table ───────────────────────────────────────────────
    print(_bold("3. RESPONSE TIME ANALYSIS TABLE"))
    header = (
        f"  {'Task':<22} {'Core':>5} {'Prio':>5} {'Period µs':>10} "
        f"{'WCET µs':>9} {'Blk µs':>7} {'Source':>12} {'WCRT µs':>9} {'Deadline µs':>12} {'Margin µs':>10}"
    )
    sep_3 = "─" * (len(header) - 2)
    print(f"  {sep_3}")
    print(header)
    print(f"  {sep_3}")

    def _task_sort_key(t):
        is_edf = util_info.get(t.core_id, {}).get('algorithm') == 'EDF' or t.priority == 255
        prio_order = t.deadline_us if is_edf else -t.priority
        return (t.core_id, prio_order)

    for t in sorted(all_tasks_with_isrs, key=_task_sort_key):
        wcet_str   = f"{t.wcet_us:.2f}"  if t.wcet_us > 0   else "???"
        blk_str    = f"{t.blocking_us:.2f}"
        wcrt_str   = f"{t.wcrt_us:.2f}"  if t.wcrt_us > 0   else "n/a"
        margin_str = f"{t.margin_us:.2f}" if t.schedulable is not None else "n/a"
        period_str = f"{t.period_us:.0f}" if t.period_us > 0 else "async"

        is_edf_task = util_info.get(t.core_id, {}).get('algorithm') == 'EDF' or t.priority == 255
        prio_display = "EDF" if is_edf_task else str(t.priority)

        margin_fmt = f"{margin_str:>10}"
        if t.schedulable is False:
            margin_col = _red(margin_fmt)
            name_col   = _red(f"{t.name:<22}")
        elif t.margin_us >= 0 and t.margin_us < t.deadline_us * 0.05:
            margin_col = _yellow(margin_fmt)
            name_col   = f"{t.name:<22}"
        else:
            margin_col = _green(margin_fmt)
            name_col   = f"{t.name:<22}"

        tag_abbr = t.wcet_tag.replace('[', '').replace(']', '')
        tag_col  = _cyan(f"{tag_abbr:>12}")

        print(
            f"  {name_col} {t.core_id:>5} {prio_display:>5} {period_str:>10} "
            f"{wcet_str:>9} {blk_str:>7} {tag_col} {wcrt_str:>9} "
            f"{t.deadline_us:>12.0f} {margin_col}"
        )

    print(f"  {sep_3}")
    print()

    # ── 4. Gantt Chart ───────────────────────────────────────────────────────
    print(_bold("4. SIMULATED EXECUTION TIMELINE (Gantt Chart)"))
    print()
    if sim:
        print(render_gantt_chart(sim))
    else:
        print("  [Gantt chart skipped — simulation not run]\n")

    # ── 5. Jitter Table ──────────────────────────────────────────────────────
    print(_bold("5. JITTER ANALYSIS"))
    print()
    if sim:
        print(render_jitter_table(sim, all_tasks_with_isrs))
    else:
        print("  [Jitter analysis skipped — simulation not run]\n")

    # ── 6. Visual Artifacts (Matplotlib Charts) ──────────────────────────────
    if charts_dir:
        print(_bold("6. VISUAL ARTIFACTS GENERATED (MATPLOTLIB CHARTS)"))
        sep_charts = "─" * 78
        print(f"  {sep_charts}")
        print(f"  {'Output':<10} {'Description':<32} {'Artifact File'}")
        print(f"  {sep_charts}")
        print(f"  {'Output 1':<10} {'Schedulability Dashboard':<32} {charts_dir}/schedulability_dashboard.png")
        print(f"  {'Output 2':<10} {'Gantt Schedule Timeline':<32} {charts_dir}/gantt_chart.png")
        print(f"  {'Output 3':<10} {'Response Time vs Deadline':<32} {charts_dir}/response_time_chart.png")
        print(f"  {'Output 4':<10} {'Start-Time Jitter Plot':<32} {charts_dir}/jitter_chart.png")
        print(f"  {sep_charts}")
        print()
        print(_bold("7. CONFIDENCE NOTES"))
    else:
        print(_bold("6. CONFIDENCE NOTES"))
    print()
    print(f"  {wcet_confidence_note}")
    print()
    print(
        "  WCET Derivation Method:\n"
        "    [CALCULATED]  Code-size heuristic: size_bytes / 2.5 bytes_per_insn × 1.15 penalty\n"
        "                  Source: Thumb-2 ISA encoding statistics + ARMv7-M pipeline model.\n"
        "                  Treat response times as OPTIMISTIC LOWER BOUNDS.\n"
        "\n"
        "    [SIMULATED]   Instruction counts from Renode functional trace.\n"
        "                  Renode does NOT model cache effects or bus arbitration.\n"
        "                  Timing is functional only — treat as APPROXIMATE.\n"
        "\n"
        "  RTA Assumptions:\n"
        "    - Single-core analysis uses configured scheduling algorithm (RM/DM/EDF).\n"
        "    - Tasks are strictly periodic with synchronous release at t=0.\n"
        "    - Inter-core communication modeled as priority ceiling blocking term.\n"
        "    - Resource dependencies utilize Priority Ceiling Protocol (PCP/SRP).\n"
        "    - ISRs treated as highest-priority periodic tasks.\n"
        "\n"
        "  For production use: measure actual WCET with on-hardware profiling\n"
        "  (e.g. Segger SystemView, TRACE32) to validate these estimates."
    )

    print(f"\n{'='*72}\n")
