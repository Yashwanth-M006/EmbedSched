"""
Tests/test_autosar_extension.py

Unit tests for the AUTOSAR Schedulability Extension.

Tests are self-contained — they do NOT require a real .elf or .map file.
Mock data is constructed inline to exercise each module independently.

Run with: python -m pytest Tests/test_autosar_extension.py -v
       or: python Tests/test_autosar_extension.py
"""

import sys
import os
import math

# Add project root to path so imports work from any cwd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.autosar_task import AutosarTask
from models.symbol import Symbol
from analysis.wcet_extractor import extract_wcets
from analysis.rta_engine import run_rta, compute_utilization
from analysis.scheduler_sim import simulate_schedule


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_task(name, period, deadline, priority, function, core=0):
    return AutosarTask(
        name=name,
        period_us=period,
        deadline_us=deadline,
        priority=priority,
        core_id=core,
        function=function,
    )


def _make_symbol(name, size, section='.text'):
    return Symbol(name=name, address=0x08000000, size=size, section=section, object_file='test.o')


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: WCET extractor — code-size heuristic
# ─────────────────────────────────────────────────────────────────────────────

def test_wcet_code_size_heuristic():
    """WCET from code size: 100 bytes, no Renode trace."""
    task = _make_task('T1', 1000, 1000, 10, 'func_a')
    sym = _make_symbol('func_a', 100)
    call_graph = {}

    extract_wcets(
        tasks=[task],
        symbols=[sym],
        call_graph=call_graph,
        chip_profile={'clock_max_mhz': 216.0},
        dynamic_profile=None,
    )

    # 100 bytes / 2.5 bytes_per_insn * 1.15 = 46 cycles
    expected_cycles = int(100 / 2.5 * 1.15)
    cycle_ns = 1000.0 / 216.0
    expected_us = (expected_cycles * cycle_ns) / 1000.0

    assert task.wcet_tag == "[CALCULATED]", f"Expected [CALCULATED], got {task.wcet_tag}"
    assert task.wcet_cycles == expected_cycles, f"Expected {expected_cycles}, got {task.wcet_cycles}"
    assert abs(task.wcet_us - round(expected_us, 2)) < 1e-4, f"Expected {expected_us:.4f} µs, got {task.wcet_us:.4f} µs"
    print(f"  PASS  WCET code-size: {task.wcet_us:.4f} µs  {task.wcet_tag}")


def test_wcet_renode_trace():
    """WCET from Renode trace — instruction count."""
    task = _make_task('T1', 1000, 1000, 10, 'func_b')
    sym = _make_symbol('func_b', 100)
    dynamic_profile = {'func_b': 200}   # 200 instructions observed

    extract_wcets(
        tasks=[task],
        symbols=[sym],
        call_graph={},
        chip_profile={'clock_max_mhz': 216.0},
        dynamic_profile=dynamic_profile,
    )

    # 200 instructions, 1 cycle/instr at 216 MHz
    expected_cycles = 200
    cycle_ns = 1000.0 / 216.0
    expected_us = (expected_cycles * cycle_ns) / 1000.0

    assert task.wcet_tag == "[SIMULATED]"
    assert task.wcet_cycles == expected_cycles
    assert abs(task.wcet_us - round(expected_us, 2)) < 1e-4
    print(f"  PASS  WCET Renode: {task.wcet_us:.4f} µs  {task.wcet_tag}")


def test_wcet_call_graph_traversal():
    """WCET includes callees via call-graph DFS."""
    caller = _make_task('T1', 1000, 1000, 10, 'caller')
    syms = [_make_symbol('caller', 50), _make_symbol('callee', 80)]
    call_graph = {'caller': {'callee'}}

    extract_wcets(
        tasks=[caller],
        symbols=syms,
        call_graph=call_graph,
        chip_profile={'clock_max_mhz': 216.0},
        dynamic_profile=None,
    )

    # caller: 50/2.5*1.15=23 + callee: 80/2.5*1.15=36 = 59 cycles
    caller_cycles = int(50 / 2.5 * 1.15)
    callee_cycles = int(80 / 2.5 * 1.15)
    expected = caller_cycles + callee_cycles

    assert caller.wcet_cycles == expected, (
        f"Expected {expected} cycles (caller={caller_cycles} + callee={callee_cycles}), "
        f"got {caller.wcet_cycles}"
    )
    print(f"  PASS  WCET call-graph: {caller.wcet_us:.4f} µs (includes callee)")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: RTA engine
# ─────────────────────────────────────────────────────────────────────────────

def test_rta_trivially_schedulable():
    """Single task: WCRT = WCET, trivially schedulable."""
    t = _make_task('T1', 1000, 1000, 10, 'f')
    t.wcet_us = 50.0
    run_rta([t])
    assert t.schedulable is True
    assert abs(t.wcrt_us - 50.0) < 1e-6
    assert abs(t.margin_us - 950.0) < 1e-6
    print(f"  PASS  RTA trivial: WCRT={t.wcrt_us:.1f} µs, margin={t.margin_us:.1f} µs")


def test_rta_two_tasks_schedulable():
    """
    Two tasks on same core:
      T1: period=500, WCET=100, priority=1 (highest under RM)
      T2: period=1000, WCET=200, priority=2

    RTA for T2:
      R = 200 + ceil(200/500)*100 = 200 + 100 = 300 µs ≤ 1000 — schedulable
    """
    t1 = _make_task('T1', 500, 500, 1, 'f1')
    t1.wcet_us = 100.0
    t2 = _make_task('T2', 1000, 1000, 2, 'f2')
    t2.wcet_us = 200.0

    run_rta([t1, t2])

    assert t1.schedulable is True, f"T1 should be schedulable, got {t1.schedulable}"
    assert t2.schedulable is True, f"T2 should be schedulable, got {t2.schedulable}"

    # T1 has no higher-priority interference → WCRT = WCET = 100
    assert abs(t1.wcrt_us - 100.0) < 1e-6

    # T2: R = 200 + ceil(200/500)*100 = 300
    expected_t2_wcrt = 300.0
    assert abs(t2.wcrt_us - expected_t2_wcrt) < 1e-3, (
        f"T2 WCRT expected {expected_t2_wcrt}, got {t2.wcrt_us}"
    )
    print(f"  PASS  RTA 2-task: T1 WCRT={t1.wcrt_us:.0f} µs, T2 WCRT={t2.wcrt_us:.0f} µs")


def test_rta_deadline_miss():
    """Task misses deadline when WCET dominates period under interference."""
    t1 = _make_task('T1', 100, 100, 1, 'f1')
    t1.wcet_us = 60.0   # 60% utilization alone
    t2 = _make_task('T2', 200, 200, 2, 'f2')
    t2.wcet_us = 100.0  # needs 100 µs every 200 µs

    run_rta([t1, t2])

    # T2 WCRT: R = 100 + ceil(100/100)*60 = 160, still ≤ 200 — passes this iteration
    # Check another: R=160 → ceil(160/100)*60 = 2*60 = 120 → R = 220 > 200 → MISS
    assert t2.schedulable is False, (
        f"T2 should miss its deadline, but schedulable={t2.schedulable}, wcrt={t2.wcrt_us}"
    )
    assert t2.wcrt_us > t2.deadline_us
    print(f"  PASS  RTA deadline miss: T2 WCRT={t2.wcrt_us:.0f} µs > deadline={t2.deadline_us:.0f} µs")


def test_rta_liu_layland_bound():
    """Utilization check: n tasks, compute Liu & Layland bound correctly."""
    tasks = [
        _make_task('T1', 1000, 1000, 30, 'f1'),
        _make_task('T2', 2000, 2000, 20, 'f2'),
        _make_task('T3', 4000, 4000, 10, 'f3'),
    ]
    for t in tasks:
        t.wcet_us = 100.0  # 10% + 5% + 2.5% = 17.5% total

    info = compute_utilization(tasks)

    assert 0 in info
    U = info[0]['utilization']
    n = 3
    expected_bound = n * (2 ** (1.0 / n) - 1.0)

    assert abs(info[0]['rm_bound'] - expected_bound) < 1e-9
    assert U < expected_bound, f"Should be below RM bound: U={U:.4f}, bound={expected_bound:.4f}"
    assert info[0]['schedulable_by_utilization'] is True
    print(f"  PASS  Liu & Layland: U={U*100:.1f}% < bound={expected_bound*100:.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Scheduler simulation
# ─────────────────────────────────────────────────────────────────────────────

def test_sim_no_deadline_misses():
    """Lightly loaded task set should produce no deadline misses."""
    tasks = [
        _make_task('T1', 1000, 1000, 20, 'f1'),
        _make_task('T2', 2000, 2000, 10, 'f2'),
    ]
    tasks[0].wcet_us = 100.0   # 10% utilization
    tasks[1].wcet_us = 200.0   # 10% utilization

    result = simulate_schedule(tasks)

    assert len(result.deadline_misses) == 0, (
        f"Expected no deadline misses, got {len(result.deadline_misses)}"
    )
    assert len(result.gantt) > 0, "Gantt should have execution slots"
    print(f"  PASS  Simulation: {len(result.gantt)} slots, 0 deadline misses")


def test_sim_hyperperiod_correct():
    """Hyperperiod should be LCM of task periods."""
    tasks = [
        _make_task('T1', 500, 500, 20, 'f1'),
        _make_task('T2', 1000, 1000, 10, 'f2'),
    ]
    tasks[0].wcet_us = 50.0
    tasks[1].wcet_us = 100.0

    result = simulate_schedule(tasks)

    # LCM(500, 1000) = 1000
    assert abs(result.hyperperiod_us - 1000.0) < 1e-6, (
        f"Expected hyperperiod=1000 µs, got {result.hyperperiod_us}"
    )
    print(f"  PASS  Hyperperiod: {result.hyperperiod_us:.0f} µs")


def test_sim_start_times_populated():
    """Start times should be recorded for each task activation."""
    tasks = [_make_task('T1', 1000, 1000, 10, 'f1')]
    tasks[0].wcet_us = 100.0

    result = simulate_schedule(tasks)

    assert 'T1' in result.start_times
    assert len(result.start_times['T1']) >= 1
    print(f"  PASS  Start times: T1 has {len(result.start_times['T1'])} activation(s)")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: AUTOSAR parser (JSON)
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_autosar_json():
    """Parse the sample AUTOSAR config and verify task count."""
    from parsers.autosar_parser import parse_autosar_config
    sample_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'sample_autosar_config.json'
    )
    if not os.path.exists(sample_path):
        print("  SKIP  sample_autosar_config.json not found")
        return

    autosar_cfg = parse_autosar_config(sample_path)
    tasks = autosar_cfg.tasks
    isrs = autosar_cfg.isrs
    assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
    assert len(isrs)  == 1, f"Expected 1 ISRs, got {len(isrs)}"
    names = {t.name for t in tasks}
    assert 'Task_MotorControl' in names
    assert 'Task_Telemetry' in names
    print(f"  PASS  JSON parser: {len(tasks)} tasks, {len(isrs)} ISRs parsed")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests():
    tests = [
        test_wcet_code_size_heuristic,
        test_wcet_renode_trace,
        test_wcet_call_graph_traversal,
        test_rta_trivially_schedulable,
        test_rta_two_tasks_schedulable,
        test_rta_deadline_miss,
        test_rta_liu_layland_bound,
        test_sim_no_deadline_misses,
        test_sim_hyperperiod_correct,
        test_sim_start_times_populated,
        test_parse_autosar_json,
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print(" AUTOSAR Extension — Unit Tests")
    print("=" * 60)

    for test_fn in tests:
        name = test_fn.__name__
        print(f"\n[TEST] {name}")
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {e}")
            failed += 1
        except Exception as e:
            import traceback
            print(f"  ERROR {e}")
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f" Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
