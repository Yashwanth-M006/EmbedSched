
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 2,921,772 / 33,554,432 bytes (8.7%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 30 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_wcet_dominates (-10), autosar_edf_priority_null (-0), autosar_edf_constrained_deadline (-0)

--------------------------------------------------
FINDINGS (6 total: 3 critical, 1 warnings, 2 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (3) - ACTION REQUIRED                                  │
└──────────────────────────────────────────────────────────────────────────┘

  [CRITICAL] [RTA/[CALCULATED]] autosar_deadline_miss
    Task 'tau1' MISSES its deadline.
      Function mapped  : task1
      WCET             : 2000.00 µs  [CALCULATED]
      Deadline         : 5000 µs
      Worst-case resp. : 6000.00 µs
      Overrun          : +1000.00 µs
      Call chain       : task1
      NOTE: WCET is [CALCULATED] — treat response time as optimistic lower bound.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[CALCULATED]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 6000.00 µs  [CALCULATED]
      Deadline         : 7000 µs
      Worst-case resp. : 8000.00 µs
      Overrun          : +1000.00 µs
      Call chain       : task2
      NOTE: WCET is [CALCULATED] — treat response time as optimistic lower bound.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [EDF] autosar_edf_constrained_deadline
    EDF Processor Demand Analysis: FAILED at L=7000.0µs (demand h(7000.0) > 7000.0µs).
    Fix: Use processor demand analysis (PDA) for precise EDF schedulability.

┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [CALCULATED] autosar_wcet_dominates
    Task 'tau2': WCET dominates its period.
      WCET / Period = 6000.00 / 10000 µs = 60%
      Leaves only 40% of the period for other tasks.
      Function: task2  [CALCULATED]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (2)                                               │
└──────────────────────────────────────────────────────────────────────────┘

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [EDF] autosar_edf_priority_null
    EDF tasks must have priority=null — priority field ignored for EDF cores
    Fix: Ensure tasks on EDF cores omit the priority field or set priority=null.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  tau2                        10000   6000.00   8000.00      7000    -1000.00     MISS
  tau1                         6000   2000.00   6000.00      5000    -1000.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [CALCULATED] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau2                     task2                      6000.00      [CALCULATED]     [Core 0]
  tau1                     task1                      2000.00      [CALCULATED]     [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (2 periodic tasks):
    [█████████████████████████████████████░░|░]  93.3%  EDF bound: 100.0% (constrained deadline)  →  DEADLINE MISS (demand analysis: h(t) > t)

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0   EDF       6000   2000.00    0.00   CALCULATED   6000.00         5000   -1000.00
  tau2                       0   EDF      10000   6000.00    0.00   CALCULATED   8000.00         7000   -1000.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 30000 µs  (scale: 468.8 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] █████░░░░░░░█████░░░░░░░░█████░░░░░░░░█████░░░░░░░░█████░░░░░░░░
  tau2             [B] ░░░░█████████>[91m|[0m░[91m█[0m[91m█[0m[91m█[0m[91m█[0m░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░[91m█[0m[91m█[0m[91m|[0m░░░░░░
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2

  DEADLINE MISSES (3 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 7000 µs,  finished @ 9104.88 µs  (+2104.88 µs late)
    [MISS]  tau2                 released @ 10000 µs,  deadline @ 17000 µs,  finished @ 17369.44 µs  (+369.44 µs late)
    [MISS]  tau2                 released @ 20000 µs,  deadline @ 27000 µs,  finished @ 27045.78 µs  (+45.78 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                              5           0.00            0.00  EXCELLENT  (<1% of period)
  tau2                              3        1919.80          639.93  MODERATE   (<20% of period)
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

