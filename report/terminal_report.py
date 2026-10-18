from typing import List
from models.finding import Finding

WEIGHTS = {
    'stack_recursion':              30,
    'stack_overflow_risk':          30,
    'stack_bss_zero_gap':           30,  # CRITICAL — zero gap between BSS and stack section
    'stack_declared_too_small':     25,  # WARNING  — depth ratio too high with zero margin
    'isr_calls_blocking_function':  25,  # WARNING  — ISR calls HAL_Delay / polling HAL
    'itcm_overflow_risk':           25,
    'dma_bus_contention':          20,
    'isr_in_flash':                15,
    'flash_fragmentation':         15,  # INFO     — hot functions spread across Flash
    'no_explicit_stack_section':   10,
    'unaligned_dma_buffer':        10,
    # ── AUTOSAR Schedulability rules ──────────────────────────────────────
    'autosar_deadline_miss':        30,  # CRITICAL — RTA confirms deadline miss
    'autosar_cpu_overload':         25,  # CRITICAL — utilization > 100%
    'autosar_deadlock_risk':        30,  # CRITICAL — circular lock acquisition order
    'autosar_entry_function_mismatch': 25, # CRITICAL — entry function not in firmware symbols
    'autosar_utilization_warning':  15,  # WARNING  — above RM bound, indeterminate
    'autosar_wcet_dominates':       10,  # WARNING  — WCET > 50% of period
    'autosar_double_risk':          10,  # WARNING  — recursion + tight deadline
    'autosar_heuristic_wcet':       10,  # WARNING  — function not found, WCET is a guess
    'autosar_concurrent_stack':     20,  # WARNING  — concurrent stack pressure exceeds _Min_Stack_Size
    'autosar_isr_flash_wcet':        5,  # WARNING  — ISR in Flash inflates WCET
    'autosar_rm_suboptimal':        10,  # WARNING  — RM used when DM should be used
    'autosar_no_margin':             0,  # INFO only — margin < 5% of deadline
    'autosar_pcp_blocking':          0,  # INFO only — blocking term info
    'autosar_edf_priority_null':     0,  # INFO only — priority ignored for EDF
    'autosar_edf_constrained_deadline': 0, # INFO only — PDA used for constrained deadline
    # ── Existing INFO / positive findings ─────────────────────────────────
    'isr_always_in_flash':          0,  # INFO only — hardware constraint, not a bug
    'isr_in_flash_info':            0,  # INFO only — no ITCM chip, hardware constraint
    'stack_in_sram_not_ccm':        0,  # INFO only — improvement opportunity
    'stack_in_ccm_good':            0,  # INFO only — positive finding
    'stack_in_dtcm_confirmed':      0,  # INFO only — positive finding
    'explicit_stack_found':         0,  # INFO only — positive finding
    'dma_buffers_correctly_placed': 0,  # INFO only — positive finding
    'dma_buffers_in_sram2_correct': 0,  # INFO only — positive finding
    'isr_in_itcm_confirmed':        0,  # INFO only — positive finding
    'hot_functions_in_itcm':        0,  # INFO only — positive finding
    'itcm_section_budget':          0,  # INFO only — positive finding
}

def compute_score(findings: List[Finding]) -> int:
    dma_rules = {'unaligned_dma_buffer', 'dma_bus_contention'}
    dma_penalty = min(50, sum(WEIGHTS.get(f.rule, 0) for f in findings if f.rule in dma_rules))
    other_penalty = sum(WEIGHTS.get(f.rule, 0) for f in findings if f.rule not in dma_rules)
    return max(0, 100 - (dma_penalty + other_penalty))

import sys
import os

def _use_color() -> bool:
    if os.environ.get('FORCE_COLOR') == '1':
        return True
    if os.environ.get('NO_COLOR') == '1':
        return False
    return sys.stdout.isatty()

def _red(s: str) -> str:
    return f"\033[91m{s}\033[0m" if _use_color() else str(s)

def _yellow(s: str) -> str:
    return f"\033[93m{s}\033[0m" if _use_color() else str(s)

def _gray(s: str) -> str:
    return f"\033[90m{s}\033[0m" if _use_color() else str(s)

def _render_box(title: str, color_fn, width: int = 76) -> str:
    inner = width - 2
    use_ascii = False
    if sys.platform == 'win32' and os.environ.get('FORCE_UTF8') != '1':
        use_ascii = True
    else:
        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        try:
            "┌─┐".encode(enc)
        except (UnicodeEncodeError, LookupError, AttributeError):
            use_ascii = True

    if not use_ascii:
        top = "┌" + "─" * inner + "┐"
        mid = f"│ {title:<{inner - 2}} │"
        bot = "└" + "─" * inner + "┘"
    else:
        top = "+" + "-" * inner + "+"
        mid = f"| {title:<{inner - 2}} |"
        bot = "+" + "-" * inner + "+"
    box_lines = f"{top}\n{mid}\n{bot}"
    return color_fn(box_lines)

def print_terminal_report(
    findings: List[Finding],
    score: int,
    dynamic_profile: dict = None
):
    print("\n====================================================")
    print(" FIRMWARE EFFICIENCY REPORT")
    print("====================================================")
    print(f"\nOVERALL SCORE: {score} / 100")
    
    if findings:
        deductions = ", ".join(f"{f.rule} (-{WEIGHTS.get(f.rule, 0)})" for f in findings)
        print(f"  Deductions: {deductions}")
        
    print("\n--------------------------------------------------")
    crit_list = [f for f in findings if f.severity == 'CRITICAL']
    warn_list = [f for f in findings if f.severity == 'WARNING']
    info_list = [f for f in findings if f.severity == 'INFO']
    
    print(f"FINDINGS ({len(findings)} total: {len(crit_list)} critical, {len(warn_list)} warnings, {len(info_list)} info)")
    print("--------------------------------------------------")
    
    # ── CRITICAL FINDINGS BLOCK (Red Box) ───────────────────────────────
    print()
    crit_title = f"CRITICAL FINDINGS ({len(crit_list)}) - {'ACTION REQUIRED' if crit_list else 'None Detected'}"
    print(_render_box(crit_title, _red))
    if crit_list:
        for f in crit_list:
            print(f"\n  [{f.severity}] {f.tag} {f.rule}")
            print(f"    {f.message.replace(chr(10), chr(10)+'    ')}")
            if f.fix:
                print(f"    Fix: {f.fix}")
        print()

    # ── WARNING FINDINGS BLOCK (Yellow Box) ─────────────────────────────
    warn_title = f"WARNING FINDINGS ({len(warn_list)}) - {'REVIEW RECOMMENDED' if warn_list else 'None Detected'}"
    print(_render_box(warn_title, _yellow))
    if warn_list:
        for f in warn_list:
            print(f"\n  [{f.severity}] {f.tag} {f.rule}")
            print(f"    {f.message.replace(chr(10), chr(10)+'    ')}")
            if f.fix:
                print(f"    Fix: {f.fix}")
        print()

    # ── INFORMATIONAL FINDINGS BLOCK (Gray Box) ─────────────────────────
    info_title = f"INFORMATIONAL FINDINGS ({len(info_list)})"
    print(_render_box(info_title, _gray))
    if info_list:
        for f in info_list:
            print(f"\n  [{f.severity}] {f.tag} {f.rule}")
            print(f"    {f.message.replace(chr(10), chr(10)+'    ')}")
            if f.fix:
                print(f"    Fix: {f.fix}")
        print()
            
    if dynamic_profile:
        print("\n--------------------------------------------------")
        print("DYNAMIC PROFILE [SIMULATED - Renode, functional only]")
        print("--------------------------------------------------")
        total_instructions = sum(dynamic_profile.values())
        if total_instructions == 0:
            print("  Trace empty or no functions resolved.")
        else:
            sorted_profile = sorted(dynamic_profile.items(), key=lambda x: x[1], reverse=True)
            for func_name, count in sorted_profile[:10]:
                pct = (count / total_instructions) * 100
                hot_tag = " (HOT)" if pct > 10.0 else ""
                print(f"  {func_name: <20}: {count:,} instrs - {pct:.1f}% of total{hot_tag}")
            
            print("\n  NOTE: Simulated execution (Renode) provides accurate control flow but")
            print("  does NOT model cache effects or bus arbitration. Timing is functional only.")

    print("\n====================================================")
