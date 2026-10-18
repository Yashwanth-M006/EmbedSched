
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 3,725,288 / 33,554,432 bytes (11.1%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 60 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_rm_suboptimal (-10)

--------------------------------------------------
FINDINGS (3 total: 1 critical, 0 warnings, 2 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (1) - ACTION REQUIRED                                  │
└──────────────────────────────────────────────────────────────────────────┘

  [CRITICAL] [RTA/[CALCULATED]] autosar_deadline_miss
    Task 'Task_B' MISSES its deadline.
      Function mapped  : task_b
      WCET             : 3200.00 µs  [CALCULATED]
      Deadline         : 6000 µs
      Worst-case resp. : 6200.00 µs
      Overrun          : +200.00 µs
      Call chain       : task_b
      NOTE: WCET is [CALCULATED] — treat response time as optimistic lower bound.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (0) - None Detected                                     │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (2)                                               │
└──────────────────────────────────────────────────────────────────────────┘

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [STATIC] autosar_rm_suboptimal
    Task 'Task_B' has deadline < period (6000 µs < 15000 µs) — RM priority assignment is suboptimal, use DM. Switching to DM may resolve this miss.
    Fix: Change core scheduling algorithm to DM (Deadline Monotonic) or EDF.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_C                      20000   4000.00  13200.00     20000     6800.00     PASS
  Task_B                      15000   3200.00   6200.00      6000     -200.00     MISS
  Task_A                      10000   3000.00   3000.00     10000     7000.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [CALCULATED] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_C                   task_c                     4000.00      [CALCULATED]     [Core 0]
  Task_B                   task_b                     3200.00      [CALCULATED]     [Core 0]
  Task_A                   task_a                     3000.00      [CALCULATED]     [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [████████████████████████████░░░|░░░░░░░░░]  71.3%  RM bound: 78.0%  →  GUARANTEED (below RM bound)

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_C                     0     3      20000   4000.00    0.00   CALCULATED  13200.00        20000    6800.00
  Task_B                     0     2      15000   3200.00    0.00   CALCULATED   6200.00         6000    -200.00
  Task_A                     0     1      10000   3000.00    0.00   CALCULATED   3000.00        10000    7000.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 60000 µs  (scale: 937.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] ████░░░░░░████░░░░░░░████░░░░░░░████░░░░░░████░░░░░░░████░░░░░░░
  Task_B           [B] ░░░███[91m|[0m░░░░░░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░░░░░░░░░░░[91m█[0m[91m█[0m[91m█[0m[91m|[0m░░░░░░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░░░░░░░░
  Task_C           [C] ░░░░░░█████>░██░░░░░░░░░█████░░░░░░░░░░░░░░░░███>░░███>░█░░░░░░░
                         0         10000      20000      30000     40000      50000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C

  DEADLINE MISSES (2 events):
    [MISS]  Task_B               released @ 0 µs,  deadline @ 6000 µs,  finished @ 6200.00 µs  (+200.00 µs late)
    [MISS]  Task_B               released @ 30000 µs,  deadline @ 36000 µs,  finished @ 36200.00 µs  (+200.00 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                            6           0.00            0.00  EXCELLENT  (<1% of period)
  Task_B                            4        3000.00         1500.00  HIGH       (>20% of period — review priority assignment)
  Task_C                            3        6200.00         4066.67  HIGH       (>20% of period — review priority assignment)
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

