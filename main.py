import argparse
import sys
import os
import glob

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from collections import defaultdict
from parsers.map_parser import parse_map_file, parse_map_special_symbols
from parsers.ld_parser import parse_ld_file, parse_ld_symbols, MemoryRegion
from parsers.su_parser import parse_su_files
from parsers.startup_parser import parse_startup_file
from parsers.elf_parser import run_objdump_disassembly
from models.chip_profile import load_chip_profile
from analysis.region_classifier import classify_address
from analysis.call_graph import build_call_graph_from_disassembly
from analysis.stack_analyzer import analyze_all_stacks
from analysis.rules.isr_placement import check_isr_placement
from analysis.rules.itcm_overflow import check_itcm_overflow
from analysis.rules.stack_risk import check_stack_risk
from analysis.rules.dma_alignment import check_dma_alignment
from analysis.rules.bus_contention import check_bus_contention
from analysis.rules.stack_section import check_no_stack_section
from analysis.rules.chip_specific import check_no_itcm_chip, check_stack_in_sram_not_ccm
from analysis.rules.stack_bss_proximity import check_stack_bss_proximity
from analysis.rules.isr_blocking_calls import check_isr_blocking_calls
from analysis.rules.flash_fragmentation import check_flash_fragmentation
from report.terminal_report import compute_score, print_terminal_report

def main():
    parser = argparse.ArgumentParser(description="Firmware Efficiency Analyzer")
    parser.add_argument('--project-dir', type=str, help="Project directory to auto-discover firmware.elf, firmware.map, linker script, and chip profile")
    parser.add_argument('--elf', type=str, required=False, help="Path to firmware.elf")
    parser.add_argument('--map', type=str, required=False, help="Path to firmware.map")
    parser.add_argument('--ld', type=str, required=False, help="Path to linker script (.ld)")
    parser.add_argument('--chip', type=str, required=False, help="Path to chip profile YAML")
    parser.add_argument('--su-dir', type=str, help="Directory containing .su files")
    parser.add_argument('--startup', type=str, help="Path to startup_*.s assembly file")
    parser.add_argument('--freq-mhz', type=float, help="MCU Frequency in MHz")
    parser.add_argument('--renode-trace', type=str, help="Path to pre-generated Renode trace file")
    parser.add_argument('--renode-repl', type=str, help="Path to Renode .repl platform description to run live simulation")
    parser.add_argument('--renode-sim-ms', type=int, default=2000, help="Duration to run Renode simulation in ms")
    parser.add_argument('--hot-funcs', type=str, help="Path to text file listing hot function names (one per line)")
    parser.add_argument(
        '--autosar-config', type=str,
        help=(
            "Path to AUTOSAR OS task configuration file (.json or .oil). "
            "Enables the AUTOSAR Schedulability Analysis section. "
            "JSON format: {\"tasks\": [{\"name\": ..., \"period_us\": ..., "
            "\"deadline_us\": ..., \"priority\": ..., \"core_id\": ..., "
            "\"function\": ...}], \"isrs\": [...]}"
        )
    )
    parser.add_argument(
        '--no-autosar-sim', action='store_true',
        help="Skip discrete-event scheduler simulation (faster, no Gantt chart)."
    )
    parser.add_argument(
        '--charts-dir', type=str,
        help="Directory to output matplotlib charts (Gantt/Jitter). Simulation must run."
    )
    parser.add_argument(
        '--stochastic-sim', action='store_true',
        help="Inject random execution variance (85-100% WCET) and release drift to the scheduler simulation."
    )
    parser.add_argument(
        '--output', type=str,
        help="Path to output markdown report file (e.g. reports/analysis_report.md)"
    )
    
    args = parser.parse_args()

    if args.project_dir:
        import glob
        pdir = args.project_dir
        if not args.elf:
            elfs = glob.glob(os.path.join(pdir, "*.elf"))
            if elfs: args.elf = elfs[0]
        if not args.map:
            maps = glob.glob(os.path.join(pdir, "*.map"))
            if maps: args.map = maps[0]
        if not args.ld:
            lds = glob.glob(os.path.join(pdir, "*.ld"))
            if lds: args.ld = lds[0]
        if not args.chip:
            yamls = glob.glob(os.path.join(pdir, "*.yaml")) + glob.glob(os.path.join(pdir, "*.yml"))
            if yamls: args.chip = yamls[0]

    missing = []
    if not args.elf: missing.append('--elf')
    if not args.map: missing.append('--map')
    if not args.ld: missing.append('--ld')
    if not args.chip: missing.append('--chip')
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)} (or supply --project-dir with matching files)")
    
    try:
        symbols = parse_map_file(args.map)
        linker_symbols = parse_map_special_symbols(args.map)  # _estack, __bss_end__, etc.
        linker_regions = parse_ld_file(args.ld)
        ld_symbols = parse_ld_symbols(args.ld)  # resolves ORIGIN()+LENGTH() expressions
        # Merge: map file values take priority (they're the actual linked result)
        merged_linker_symbols = {**ld_symbols, **linker_symbols}
        chip_profile = load_chip_profile(args.chip)
        
        # Filter veneer symbols (linker-generated trampolines)
        symbols = [sym for sym in symbols if not sym.name.endswith('_veneer')]

        
        stack_usage = parse_su_files(args.su_dir) if args.su_dir else {}
        isr_names = parse_startup_file(args.startup) if args.startup else []
        
        disassembly = run_objdump_disassembly(args.elf)
        call_graph = build_call_graph_from_disassembly(disassembly)

        # Parse hot functions list (optional, for flash fragmentation analysis)
        hot_func_names = []
        if args.hot_funcs:
            try:
                with open(args.hot_funcs, 'r', encoding='utf-8') as hf:
                    for line in hf:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            hot_func_names.append(line)
            except Exception as e:
                print(f"Warning: could not read --hot-funcs file: {e}")
    except Exception as e:
        print(f"Error loading inputs: {e}")
        sys.exit(1)
        
    chip_regions = chip_profile.get('memory_regions', {})
    
    # Phase 2 & 3 Analysis
    findings = []
    
    freq_mhz = args.freq_mhz or chip_profile.get('clock_max_mhz', 100)
    
    # Rule 1: ISR placement
    if isr_names:
        findings.extend(check_isr_placement(isr_names, symbols, linker_regions, chip_regions, chip_profile, freq_mhz))

    # Rule 10: ISR calls blocking function (HAL_Delay, HAL_UART_Transmit, etc.)
    if isr_names:
        findings.extend(check_isr_blocking_calls(isr_names, call_graph))

    # Rule 11: Flash fragmentation — hot function cache locality
    if hot_func_names:
        findings.extend(check_flash_fragmentation(hot_func_names, symbols))
        
    # Rule 2: Bus Contention
    findings.extend(check_bus_contention(symbols, linker_regions, chip_regions, chip_profile, merged_linker_symbols))

    # Rule 3: ITCM Overflow
    findings.extend(check_itcm_overflow(symbols, linker_regions, chip_regions))
    
    # Rule 5: DMA Alignment
    findings.extend(check_dma_alignment(symbols, chip_regions, chip_profile))
    
    # Rule 6: No explicit stack section (Test_1 scenario)
    findings.extend(check_no_stack_section(linker_regions, merged_linker_symbols, chip_regions))
    
    # Rule 7: Chip-specific — no ITCM on STM32F407 family
    if isr_names:
        findings.extend(check_no_itcm_chip(isr_names, chip_profile))
    
    # Rule 8: Stack in SRAM when CCM is available
    findings.extend(check_stack_in_sram_not_ccm(merged_linker_symbols, chip_profile, chip_regions))
    
    # Rule 4: Stack Risk
    entry_points = set(isr_names)
    entry_points.add('main')
    valid_ep = [ep for ep in entry_points if ep in call_graph or ep in stack_usage]
    
    max_d, max_c, has_rec = 0, [], False
    isr_max_d, isr_max_c = 0, []
    main_max_d, main_max_c = 0, []
    
    if valid_ep:
        # Overall worst case
        max_d, max_c, has_rec = analyze_all_stacks(call_graph, stack_usage, valid_ep)
        
        # ISR entry points only (for preemption math)
        isr_eps = [ep for ep in isr_names if ep in call_graph or ep in stack_usage]
        if isr_eps:
            isr_max_d, isr_max_c, _ = analyze_all_stacks(call_graph, stack_usage, isr_eps)
        
        # Main entry point only
        if 'main' in call_graph or 'main' in stack_usage:
            main_max_d, main_max_c, _ = analyze_all_stacks(call_graph, stack_usage, ['main'])
        
        # ---------------------------------------------------------------------------
        # Stack capacity resolution — priority order:
        #
        #  1. _Min_Stack_Size from the map file (most explicit, now correctly parsed
        #     for short hex values like 0x400 that were previously silently skipped).
        #
        #  2. __stack_end - __stack_start: both emitted by CubeMX-style scripts that
        #     declare a named .stack section with explicit start/end markers.
        #
        #  3. _estack - __stack_start: _estack is the hardware initial SP (top of RAM);
        #     __stack_start marks the bottom of the reserved section. Their difference
        #     is exactly the reserved stack region.
        #
        #  4. _estack - __bss_end__: implicit headroom when no named stack section
        #     exists. This is the worst-case available space; BSS growth silently
        #     reduces it (see stack_bss_proximity rule).
        #
        #  5. 4096 bytes — last-resort default. Printed as a warning so the user
        #     knows the analysis may be unreliable.
        # ---------------------------------------------------------------------------
        def resolve_stack_capacity(syms: dict) -> tuple:
            """Returns (capacity_bytes, source_description)."""
            # Priority 1: explicit _Min_Stack_Size
            if '_Min_Stack_Size' in syms and syms['_Min_Stack_Size'] > 0:
                return syms['_Min_Stack_Size'], '_Min_Stack_Size from map/ld'

            # Priority 2: __stack_end - __stack_start (named section markers)
            s_start = syms.get('__stack_start', 0)
            s_end   = syms.get('__stack_end',   0)
            if s_end > s_start > 0:
                return s_end - s_start, '__stack_end - __stack_start'

            # Priority 3: _estack - __stack_start
            estack = syms.get('_estack', 0)
            if estack > s_start > 0:
                return estack - s_start, '_estack - __stack_start'

            # Priority 4: _estack - __bss_end__ (implicit headroom)
            bss_end = syms.get('__bss_end__', syms.get('_ebss', 0))
            if estack > bss_end > 0:
                return estack - bss_end, '_estack - __bss_end__ (implicit headroom — BSS growth reduces this)'

            # Priority 5: hardcoded default
            import sys
            print('[WARNING] Could not determine stack capacity from map/ld symbols; '
                  'using fallback 4096 bytes. Provide _Min_Stack_Size in your linker '
                  'script for accurate analysis.', file=sys.stderr)
            return 4096, 'fallback default'

        stack_cap, stack_cap_src = resolve_stack_capacity(merged_linker_symbols)
        findings.extend(check_stack_risk(max_d, max_c, has_rec, stack_cap, merged_linker_symbols, linker_regions, chip_regions, stack_cap_src=stack_cap_src))

    # Rule 9: Stack-BSS proximity (zero gap detection — Test 5 pattern)
    findings.extend(check_stack_bss_proximity(
        merged_linker_symbols, linker_regions, chip_regions, chip_profile,
        symbols, max_d, max_c,
        isr_max_d, isr_max_c,
        main_max_d, main_max_c,
    ))
        
    dynamic_profile = None
    if args.renode_repl:
        from simulation.renode_runner import run_renode_trace, parse_renode_trace
        print(f"Running Renode live simulation for {args.renode_sim_ms}ms...")
        trace_file = run_renode_trace(args.elf, args.renode_repl, args.renode_sim_ms)
        dynamic_profile = parse_renode_trace(trace_file, symbols)
    elif args.renode_trace:
        from simulation.renode_runner import parse_renode_trace
        dynamic_profile = parse_renode_trace(args.renode_trace, symbols)
        
    # Postponed printing report until after AUTOSAR so findings are included.
    # ---------------------------------------------------------------------------
    # AUTOSAR Schedulability Extension
    # ---------------------------------------------------------------------------
    has_error = False
    autosar_reporter = None
    if args.autosar_config:
        res = _run_autosar_analysis(
            args=args,
            symbols=symbols,
            call_graph=call_graph,
            isr_names=isr_names,
            dynamic_profile=dynamic_profile,
            chip_profile=chip_profile,
            linker_regions=linker_regions,
            chip_regions=chip_regions,
            findings=findings,
            stack_usage=stack_usage,
            merged_linker_symbols=merged_linker_symbols
        )
        if isinstance(res, tuple):
            has_error, autosar_reporter = res
        else:
            has_error = res

    # Phase 1: Memory Map
    usage_by_region = defaultdict(int)
    for sym in symbols:
        region = classify_address(sym.address, linker_regions, chip_regions)
        usage_by_region[region] += sym.size

    # Account for declared stack section reservation if not represented in symbols
    estack = merged_linker_symbols.get('_estack', 0)
    min_stack = merged_linker_symbols.get('_Min_Stack_Size', 0)
    if min_stack > 0 and estack > 0:
        stack_addr = estack - min_stack
        stack_reg = classify_address(stack_addr, linker_regions, chip_regions)
        if stack_reg != 'UNKNOWN':
            has_sym = any(stack_addr <= s.address < estack for s in symbols)
            if not has_sym:
                usage_by_region[stack_reg] += min_stack
        
    print("====================================================")
    print(" MEMORY MAP SUMMARY [STATIC]")
    print("====================================================")
    
    all_regions = list(linker_regions.keys())
    for r in chip_regions:
        if r not in all_regions:
            all_regions.append(r)
            
    for region_name in all_regions:
        usage = usage_by_region[region_name]
        
        capacity = 0
        if region_name in linker_regions:
            capacity = linker_regions[region_name].length
        elif region_name in chip_regions:
            capacity = chip_regions[region_name].get('size_kb', 0) * 1024
            
        if capacity > 0:
            percentage = (usage / capacity) * 100
            print(f"  {region_name: <7}: {usage:,} / {capacity:,} bytes ({percentage:.1f}%)")
        else:
            if usage > 0:
                print(f"  {region_name: <7}: {usage:,} bytes (unknown capacity)")

    unknown_usage = usage_by_region.get('UNKNOWN', 0)
    if unknown_usage > 0:
        print(f"  UNKNOWN: {unknown_usage:,} bytes")

    score = compute_score(findings)
    print_terminal_report(findings, score, dynamic_profile)

    # AUTOSAR Schedulability Analysis section at the end
    if autosar_reporter:
        autosar_reporter()

    if args.output:
        from report.markdown_report import write_markdown_report
        mem_data = {}
        for region_name in all_regions:
            usage = usage_by_region[region_name]
            capacity = 0
            if region_name in linker_regions:
                capacity = linker_regions[region_name].length
            elif region_name in chip_regions:
                capacity = chip_regions[region_name].get('size_kb', 0) * 1024
            mem_data[region_name] = {'used': usage, 'capacity': capacity}

        autosar_dict = None
        if hasattr(main, '_last_autosar_data'):
            autosar_dict = main._last_autosar_data

        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        write_markdown_report(args.output, findings, score, mem_data, autosar_dict)
        print(f"\n[REPORT] Saved markdown report to {args.output}")

    if has_error:
        sys.exit(1)


def _run_autosar_analysis(
    args,
    symbols,
    call_graph,
    isr_names,
    dynamic_profile,
    chip_profile,
    linker_regions,
    chip_regions,
    findings,
    stack_usage,
    merged_linker_symbols
):
    """
    Orchestrate the full AUTOSAR Schedulability Analysis extension.

    Called from main() only when --autosar-config is provided.
    Modifies `findings` in-place to add AUTOSAR rule findings.
    """
    # ── Imports (deferred to keep startup fast when AUTOSAR not used) ────────
    from parsers.autosar_parser import parse_autosar_config
    from analysis.wcet_extractor import extract_wcets, lowest_confidence_tag
    from analysis.rta_engine import run_rta, compute_utilization
    from analysis.scheduler_sim import simulate_schedule
    from analysis.rules.autosar_rules import (
        check_deadline_misses,
        check_heuristic_wcet,
        check_cpu_overload,
        check_utilization_warning,
        check_wcet_dominates,
        check_double_risk,
        check_isr_flash_wcet,
        check_near_deadline,
        check_rm_suboptimal_assignment,
        check_pcp_blocking,
        check_edf_priority_null,
        check_edf_constrained_deadline,
        check_concurrent_stack_pressure,
        check_hyperperiod_explosion,
        check_deadlock_risk,
        check_entry_function_mismatches
    )
    from analysis.stack_analyzer import worst_case_stack_depth
    from analysis.region_classifier import classify_address
    from report.autosar_report import print_autosar_report

    print("\n[AUTOSAR] Loading task configuration...")

    try:
        autosar_cfg = parse_autosar_config(args.autosar_config)
        tasks = autosar_cfg.tasks
        isr_tasks = autosar_cfg.isrs
    except Exception as e:
        print(f"[AUTOSAR] Error parsing config: {e}", file=sys.stderr)
        return True

    # ── Validate task entry functions against firmware symbols ─────────────────
    tasks, mismatch_findings, has_mismatch_error = check_entry_function_mismatches(tasks, symbols)
    findings.extend(mismatch_findings)

    if not tasks and not isr_tasks:
        print("[AUTOSAR] No valid tasks remaining — skipping analysis.")
        return has_mismatch_error

    # ── Add ISR pseudo-tasks from startup file ───────────────────────────────
    # Non-periodic exception/fault handlers run once at boot or on errors and are not periodic schedulable entities.
    NON_PERIODIC_HANDLERS = {
        'Reset_Handler', 'HardFault_Handler', 'NMI_Handler',
        'MemManage_Handler', 'BusFault_Handler', 'UsageFault_Handler',
        'Default_Handler', 'DebugMon_Handler'
    }

    explicit_isr_names = {t.name for t in isr_tasks} | {t.function for t in isr_tasks}
    from models.autosar_task import AutosarTask
    from models.finding import Finding

    for isr_name in isr_names:
        if isr_name in NON_PERIODIC_HANDLERS or (isr_name.endswith('_Handler') and isr_name not in ('SysTick_Handler', 'PendSV_Handler')):
            if isr_name == 'Reset_Handler':
                findings.append(Finding(
                    rule='autosar_reset_handler_excluded',
                    severity='INFO',
                    tag='[STATIC]',
                    message="Reset_Handler excluded — not a periodic ISR",
                    fix="Startup handlers execute once at boot and are not schedulable entities."
                ))
            else:
                findings.append(Finding(
                    rule='autosar_non_periodic_handler_excluded',
                    severity='INFO',
                    tag='[STATIC]',
                    message=f"{isr_name} excluded — not a periodic ISR",
                    fix="Fault/exception handlers are not periodic schedulable entities."
                ))
            continue

        if isr_name == 'SysTick_Handler':
            findings.append(Finding(
                rule='autosar_systick_periodic_info',
                severity='INFO',
                tag='[STATIC]',
                message="SysTick_Handler detected as periodic ISR at OS tick rate — include if tick rate specified in schedule.json",
                fix="Include SysTick_Handler in schedule.json if tick overhead modeling is desired."
            ))
            if isr_name in explicit_isr_names:
                continue

        if isr_name not in explicit_isr_names:
            parts = isr_name.split('_')
            suffix = parts[0].upper()
            formatted_name = "Task_ISR_" + suffix
            target_core = 0
            if hasattr(autosar_cfg, 'tasks') and autosar_cfg.tasks:
                for t in autosar_cfg.tasks:
                    if t.function == isr_name:
                        target_core = t.core_id
                        break
            isr_tasks.append(AutosarTask(
                name=formatted_name,
                period_us=1000,
                deadline_us=1000,
                priority=0,
                core_id=target_core,
                function=isr_name,
                is_isr=True,
            ))

    all_tasks = tasks + isr_tasks

    # ── Extract WCETs ────────────────────────────────────────────────────────
    print("[AUTOSAR] Extracting WCETs from firmware artifacts...")
    extract_wcets(
        tasks=all_tasks,
        symbols=symbols,
        call_graph=call_graph,
        chip_profile=chip_profile,
        dynamic_profile=dynamic_profile,
    )

    # ── Run RTA ──────────────────────────────────────────────────────────────
    # RTA only on periodic tasks (period_us > 0)
    print("[AUTOSAR] Running Response Time Analysis (RTA)...")
    periodic_tasks = [t for t in all_tasks if t.period_us > 0]
    run_rta(
        tasks=periodic_tasks, 
        cores=autosar_cfg.cores, 
        resources=autosar_cfg.resources, 
        channels=autosar_cfg.inter_core_channels,
        chip_regions=chip_regions,
        chip_profile=chip_profile
    )

    util_info = compute_utilization(periodic_tasks, autosar_cfg.cores)

    # ── Scheduler simulation ─────────────────────────────────────────────────
    sim = None
    if not getattr(args, 'no_autosar_sim', False):
        print("[AUTOSAR] Running discrete-event scheduler simulation...")
        try:
            is_stoch = getattr(args, 'stochastic_sim', False)
            sim = simulate_schedule(
                [t for t in all_tasks if t.period_us > 0 and t.wcet_us > 0],
                stochastic=is_stoch,
                cores=autosar_cfg.cores if autosar_cfg else None
            )
        except Exception as e:
            print(f"[AUTOSAR] Simulation failed: {e} — Gantt chart unavailable.", file=sys.stderr)

    # ── Determine which ISRs are in Flash (for WCET inflation warning) ───────
    isr_in_flash = set()
    for sym in symbols:
        region = classify_address(sym.address, linker_regions, chip_regions)
        if sym.name in isr_names and region not in ('ITCM', 'DTCM'):
            isr_in_flash.add(sym.name)

    # ── Detect functions with recursion (for double-risk rule) ───────────────
    # A function is "recursive" if worst_case_stack_depth finds a cycle.
    recursive_functions = set()
    stack_usage_empty: dict = {}
    for func in call_graph:
        _, _, has_rec = worst_case_stack_depth(call_graph, stack_usage_empty, func)
        if has_rec:
            recursive_functions.add(func)

    # ── Fire AUTOSAR rules ───────────────────────────────────────────────────
    autosar_findings = []
    autosar_findings.extend(check_deadline_misses(all_tasks))
    autosar_findings.extend(check_heuristic_wcet(all_tasks))
    autosar_findings.extend(check_cpu_overload(util_info))
    autosar_findings.extend(check_utilization_warning(util_info))
    autosar_findings.extend(check_wcet_dominates(tasks))
    autosar_findings.extend(check_double_risk(tasks, recursive_functions))
    autosar_findings.extend(check_isr_flash_wcet(isr_tasks, isr_in_flash, chip_profile))
    autosar_findings.extend(check_near_deadline(tasks))
    autosar_findings.extend(check_rm_suboptimal_assignment(tasks, autosar_cfg.cores))
    autosar_findings.extend(check_pcp_blocking(tasks))
    autosar_findings.extend(check_edf_priority_null(tasks, autosar_cfg.cores))
    autosar_findings.extend(check_edf_constrained_deadline(tasks, autosar_cfg.cores))
    if sim:
        autosar_findings.extend(check_hyperperiod_explosion(tasks, sim.hyperperiod_us, sim.capped))
    autosar_findings.extend(check_concurrent_stack_pressure(
        all_tasks, call_graph, stack_usage, worst_case_stack_depth, merged_linker_symbols
    ))
    deadlock_findings = check_deadlock_risk(autosar_cfg.resources)
    autosar_findings.extend(deadlock_findings)

    # Merge into the master findings list (affects the overall score)
    findings.extend(autosar_findings)

    # ── Determine propagated confidence note (3-tier: SIMULATED > CALCULATED > HEURISTIC) ──
    # Use wcet_cycles (not wcet_us) to catch HEURISTIC tasks whose tiny 10-cycle
    # placeholder rounds to 0 µs but is still a real (unreliable) estimate.
    all_tags = {t.wcet_tag for t in all_tasks if t.wcet_cycles > 0 or t.wcet_tag == '[HEURISTIC]'}
    lowest_tag = lowest_confidence_tag(all_tags)

    if lowest_tag == "[HEURISTIC]":
        heuristic_tasks = [t.name for t in all_tasks if t.wcet_tag == "[HEURISTIC]"]
        conf_note = (
            f"LOWEST CONFIDENCE: [HEURISTIC]\n"
            f"  Tasks with heuristic WCET: {', '.join(heuristic_tasks)}\n"
            f"  These functions were not found in the ELF symbol table, .su files, or Renode trace.\n"
            f"  The 10-cycle placeholder is NOT a measured value — schedulability verdict is UNRELIABLE.\n"
            f"  Fix: verify entry_function names and recompile with -ffunction-sections -fstack-usage."
        )
    elif "[CALCULATED]" in all_tags and "[SIMULATED]" in all_tags:
        conf_note = (
            "Mixed confidence: some WCETs are [CALCULATED] (code-size heuristic) "
            "and some are [SIMULATED] (Renode trace).\n"
            "  Response times are OPTIMISTIC — treat as lower bounds for [CALCULATED] tasks."
        )
    elif "[CALCULATED]" in all_tags:
        conf_note = (
            "All WCETs are [CALCULATED] from code-size heuristic.\n"
            "  Response times are OPTIMISTIC LOWER BOUNDS — not measured values.\n"
            "  The analysis is conservative for schedulability (real silicon may be slower)."
        )
    else:
        conf_note = (
            "All WCETs are [SIMULATED] from Renode functional trace.\n"
            "  Renode does NOT model cache or bus arbitration — timing is approximate."
        )

    # ── Generate matplotlib charts (Outputs 1, 2, 3, 4) ──────────────────────
    if getattr(args, 'charts_dir', None):
        print(f"[AUTOSAR] Generating matplotlib charts in {args.charts_dir}...")
        try:
            from report.matplotlib_charts import generate_charts
            generate_charts(
                sim=sim,
                all_tasks=all_tasks,
                out_dir=args.charts_dir,
                util_info=util_info,
                cores=autosar_cfg.cores,
                lowest_tag=lowest_tag,
            )
        except Exception as e:
            print(f"[AUTOSAR] Chart generation failed: {e}", file=sys.stderr)

    # ── Defer printing AUTOSAR report to the end of main() ───────────────────
    def reporter():
        print_autosar_report(
            tasks=tasks,
            all_tasks_with_isrs=all_tasks,
            util_info=util_info,
            sim=sim,
            isr_task_names={t.name for t in isr_tasks},
            wcet_confidence_note=conf_note,
            deadlock_findings=deadlock_findings,
            lowest_confidence_tag=lowest_tag,
            charts_dir=getattr(args, 'charts_dir', None),
        )

    # Store for markdown exporter
    task_list_data = []
    for t in all_tasks:
        task_list_data.append({
            'name': t.name,
            'core': t.core_id,
            'priority': t.priority,
            'period': t.period_us,
            'wcet': round(t.wcet_us, 2),
            'blocking': round(t.blocking_us, 2),
            'wcrt': round(t.wcrt_us, 2),
            'deadline': t.deadline_us,
            'schedulable': t.schedulable,
        })
    main._last_autosar_data = {
        'tasks': task_list_data,
        'confidence_note': conf_note,
        'verdict': "SCHEDULABLE" if not has_mismatch_error and all(t.schedulable for t in all_tasks) else "UNSCHEDULABLE / MISMATCH"
    }

    return has_mismatch_error, reporter


if __name__ == "__main__":
    main()
