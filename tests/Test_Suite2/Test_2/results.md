
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 15,412,282 / 33,554,432 bytes (45.9%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 85 / 100
  Deductions: explicit_stack_found (-0), autosar_utilization_warning (-15)

--------------------------------------------------
FINDINGS (2 total: 0 critical, 1 warnings, 1 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (0) - None Detected                                    │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [CALCULATED] autosar_utilization_warning
    Core 0: utilization in INDETERMINATE zone.
      Utilization   : 77.0%
      RM bound      : 74.3% (n=5 tasks)
      Liu & Layland guarantee does NOT apply above the RM bound.
      The task set MAY still be schedulable — check RTA results.
    Fix: Verify via RTA. Reduce utilization or adopt a specific priority assignment.

┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (1)                                               │
└──────────────────────────────────────────────────────────────────────────┘

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_E                     160000  19200.00  69200.00    160000    90800.00     PASS
  Task_D                      80000  12000.00  30000.00     80000    50000.00     PASS
  Task_C                      40000   6000.00  13000.00     40000    27000.00     PASS
  Task_B                      20000   3000.00   5000.00     20000    15000.00     PASS
  Task_A                      10000   2000.00   2000.00     10000     8000.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [CALCULATED] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_E                   task_e                     19200.00     [CALCULATED]     [Core 0]
  Task_D                   task_d                     12000.00     [CALCULATED]     [Core 0]
  Task_C                   task_c                     6000.00      [CALCULATED]     [Core 0]
  Task_B                   task_b                     3000.00      [CALCULATED]     [Core 0]
  Task_A                   task_a                     2000.00      [CALCULATED]     [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (5 periodic tasks):
    [█████████████████████████████|█░░░░░░░░░░]  77.0%  RM bound: 74.3%  →  INDETERMINATE (above RM bound)

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_E                     0     5     160000  19200.00    0.00   CALCULATED  69200.00       160000   90800.00
  Task_D                     0     4      80000  12000.00    0.00   CALCULATED  30000.00        80000   50000.00
  Task_C                     0     3      40000   6000.00    0.00   CALCULATED  13000.00        40000   27000.00
  Task_B                     0     2      20000   3000.00    0.00   CALCULATED   5000.00        20000   15000.00
  Task_A                     0     1      10000   2000.00    0.00   CALCULATED   2000.00        10000    8000.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 160000 µs  (scale: 2500.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] █░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░
  Task_B           [B] ██░░░░░░██░░░░░░██░░░░░░██░░░░░░██░░░░░░██░░░░░░██░░░░░░██░░░░░░
  Task_C           [C] ░░████░░░░░░░░░░░░████░░░░░░░░░░░░████░░░░░░░░░░░░████░░░░░░░░░░
  Task_D           [D] ░░░░░███>░██░░░░░░░░░░░░░░░░░░░░░░░░░███>░██░░░░░░░░░░░░░░░░░░░░
  Task_E           [E] ░░░░░░░░░░░░████>░░░░███>░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0       20000   40000   60000   80000   100000  120000  140000  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C
    [D]  Task_D
    [E]  Task_E

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                           16           0.00            0.00  EXCELLENT  (<1% of period)
  Task_B                            8        2000.00         2000.00  MODERATE   (<20% of period)
  Task_C                            4        5000.00         5000.00  MODERATE   (<20% of period)
  Task_D                            2       13000.00        13000.00  MODERATE   (<20% of period)
  Task_E                            1       32000.00        32000.00  HIGH       (>20% of period — review priority assignment)
  ────────────────────────────────────────────────────────────────────────────
  NOTE: Jitter is measured against the ideal periodic release time.
  Non-zero jitter is caused by higher-priority task preemption.
  For sensor/control loops, high jitter degrades control stability.
  Jitter on single-task cores reflects simulation granularity/drift, not real-world preemption delay.

6. VISUAL ARTIFACTS GENERATED (MATPLOTLIB CHARTS)
  ──────────────────────────────────────────────────────────────────────────────
  Output     Description                      Artifact File
  ──────────────────────────────────────────────────────────────────────────────
  Output 1   Schedulability Dashboard         charts/schedulability_dashboard.png
  Output 2   Gantt Schedule Timeline          charts/gantt_chart.png
  Output 3   Response Time vs Deadline        charts/response_time_chart.png
  Output 4   Start-Time Jitter Plot           charts/jitter_chart.png
  ──────────────────────────────────────────────────────────────────────────────

7. CONFIDENCE NOTES

  All WCETs are [CALCULATED] from code-size heuristic.
  Response times are OPTIMISTIC LOWER BOUNDS — not measured values.
  The analysis is conservative for schedulability (real silicon may be slower).

  WCET Derivation Method:
    [CALCULATED]  Code-size heuristic: size_bytes / 2.5 bytes_per_insn × 1.15 penalty
                  Source: Thumb-2 ISA encoding statistics + ARMv7-M pipeline model.
                  Treat response times as OPTIMISTIC LOWER BOUNDS.

    [SIMULATED]   Instruction counts from Renode functional trace.
                  Renode does NOT model cache effects or bus arbitration.
                  Timing is functional only — treat as APPROXIMATE.

  RTA Assumptions:
    - Single-core analysis uses configured scheduling algorithm (RM/DM/EDF).
    - Tasks are strictly periodic with synchronous release at t=0.
    - Inter-core communication modeled as priority ceiling blocking term.
    - Resource dependencies utilize Priority Ceiling Protocol (PCP/SRP).
    - ISRs treated as highest-priority periodic tasks.

  For production use: measure actual WCET with on-hardware profiling
  (e.g. Segger SystemView, TRACE32) to validate these estimates.

========================================================================

