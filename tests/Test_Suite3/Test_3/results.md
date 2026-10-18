
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 4,382,652 / 33,554,432 bytes (13.1%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 45 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_hyperperiod_explosion (-0)

--------------------------------------------------
FINDINGS (4 total: 2 critical, 1 warnings, 1 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (2) - ACTION REQUIRED                                  │
└──────────────────────────────────────────────────────────────────────────┘

  [CRITICAL] [RTA/[CALCULATED]] autosar_deadline_miss
    Task 'tau3' MISSES its deadline.
      Function mapped  : task3
      WCET             : 5000.00 µs  [CALCULATED]
      Deadline         : 20000 µs
      Worst-case resp. : 22000.00 µs
      Overrun          : +2000.00 µs
      Call chain       : task3
      NOTE: WCET is [CALCULATED] — treat response time as optimistic lower bound.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 101.2% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [CALCULATED] autosar_hyperperiod_explosion
    Hyperperiod = 420ms — full simulation disabled.
    Showing representative 30ms window only. RTA used for schedulability verdict. [CALCULATED]
    Fix: Harmonize task periods (e.g., make them multiples of a common base) to reduce hyperperiod.

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
  tau3                        20000   5000.00  22000.00     20000    -2000.00     MISS
  tau2                        12000   4000.00   7000.00     12000     5000.00     PASS
  tau1                         7000   3000.00   3000.00      7000     4000.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [CALCULATED] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau3                     task3                      5000.00      [CALCULATED]     [Core 0]
  tau2                     task2                      4000.00      [CALCULATED]     [Core 0]
  tau1                     task1                      3000.00      [CALCULATED]     [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  101.2%  RM bound: 78.0%  →  OVERLOADED

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau3                       0     3      20000   5000.00    0.00   CALCULATED  22000.00        20000   -2000.00
  tau2                       0     2      12000   4000.00    0.00   CALCULATED   7000.00        12000    5000.00
  tau1                       0     1       7000   3000.00    0.00   CALCULATED   3000.00         7000    4000.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Representative Window (First 30ms)  (scale: 468.8 µs/char)
  NOTE: Full simulation disabled due to hyperperiod explosion (420ms). Showing representative 30ms window only.
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ███████░░░░░░░███████░░░░░░░░████████░░░░░░░████████░░░░░░░█████
  tau2             [B] ░░░░░░█████████░░░░░░░░░░█████>░░░░░████░░░░░░░░░░░████████░░░░█
  tau3             [C] ░░░░░░░░░░░░░░█>░░░░██████>░░░░░░░░░░░░███[91m|[0m[91m█[0m[91m█[0m[91m>[0m░░░░░[91m█[0m[91m>[0m░░░░░[91m█[0m[91m█[0m[91m>[0m░░[91m█[0m
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2
    [C]  tau3

  DEADLINE MISSES (2 events):
    [MISS]  tau3                 released @ 0 µs,  deadline @ 20000 µs,  finished @ 20637.97 µs  (+637.97 µs late)
    [MISS]  tau3                 released @ 60000 µs,  deadline @ 80000 µs,  finished @ 80830.59 µs  (+830.59 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                             29           0.00            0.00  EXCELLENT  (<1% of period)
  tau2                             17        2998.15          807.05  HIGH       (>20% of period — review priority assignment)
  tau3                             10        6759.23         3400.49  HIGH       (>20% of period — review priority assignment)
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

