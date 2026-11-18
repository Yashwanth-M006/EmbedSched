
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts via IPET...
[AUTOSAR] Priority ordering mode: Standard (lower number = higher priority)
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 4,017,442 / 33,554,432 bytes (12.0%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 5 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10)

--------------------------------------------------
FINDINGS (5 total: 3 critical, 1 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 5299.00 µs  [IPET]
      Deadline         : 12000 µs
      Worst-case resp. : 15897.00 µs
      Overrun          : +3897.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau3' MISSES its deadline.
      Function mapped  : task3
      WCET             : 8832.00 µs  [IPET]
      Deadline         : 20000 µs
      Worst-case resp. : 24729.00 µs
      Overrun          : +4729.00 µs
      Call chain       : task3
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 164.0% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau1': WCET dominates its period.
      WCET / Period = 5299.00 / 7000 µs = 76%
      Leaves only 24% of the period for other tasks.
      Function: task1  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (1)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
 Priority Convention: Standard Real-Time (Lower numerical value = Higher priority)
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  tau1                         7000   5299.00   5299.00      7000     1701.00     PASS
  tau2                        12000   5299.00  15897.00     12000    -3897.00     MISS
  tau3                        20000   8832.00  24729.00     20000    -4729.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      5299.00      [IPET]           [Core 0]
  tau2                     task2                      5299.00      [IPET]           [Core 0]
  tau3                     task3                      8832.00      [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  164.0%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 164.0% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1       7000   5299.00    0.00         IPET   5299.00         7000    1701.00
  tau2                       0     2      12000   5299.00    0.00         IPET  15897.00        12000   -3897.00
  tau3                       0     3      20000   8832.00    0.00         IPET  24729.00        20000   -4729.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 420000 µs  (scale: 6562.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ████████████████████████████████████████████████████████████████
  tau2             [B] █[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m
                         0       52500   105000  157500  210000  262500  315000  367500  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2

  DEADLINE MISSES (26 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 12000 µs,  finished @ 19634.72 µs  (+7634.72 µs late)
    [MISS]  tau2                 released @ 12000 µs,  deadline @ 24000 µs,  finished @ 34258.46 µs  (+10258.46 µs late)
    [MISS]  tau2                 released @ 24000 µs,  deadline @ 36000 µs,  finished @ 54227.11 µs  (+18227.11 µs late)
    [MISS]  tau2                 released @ 36000 µs,  deadline @ 48000 µs,  finished @ 69005.69 µs  (+21005.69 µs late)
    [MISS]  tau2                 released @ 48000 µs,  deadline @ 60000 µs,  finished @ 83341.29 µs  (+23341.29 µs late)
    [MISS]  tau2                 released @ 60000 µs,  deadline @ 72000 µs,  finished @ 97639.10 µs  (+25639.10 µs late)
    [MISS]  tau2                 released @ 72000 µs,  deadline @ 84000 µs,  finished @ 117078.98 µs  (+33078.98 µs late)
    [MISS]  tau2                 released @ 84000 µs,  deadline @ 96000 µs,  finished @ 131251.72 µs  (+35251.72 µs late)
    [MISS]  tau2                 released @ 96000 µs,  deadline @ 108000 µs,  finished @ 145981.10 µs  (+37981.10 µs late)
    [MISS]  tau2                 released @ 108000 µs,  deadline @ 120000 µs,  finished @ 165938.70 µs  (+45938.70 µs late)
    ... and 16 more.

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                             60           0.00            0.00  EXCELLENT (<1% of period)
  tau2                             27      100804.29        55450.93  HIGH (>20% of period
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

  HIGH CONFIDENCE: [IPET]
  All WCETs mathematically proven via Implicit Path Enumeration Technique (IPET).
  Pipeline stalls, taken branch flushes, and Flash prefetch buffer misses fully modeled.

  WCET Derivation Method:
    [IPET]              Implicit Path Enumeration Technique (microarchitecturally proven).
                        Models pipeline hazards, branch flushes, and 128-bit Flash prefetch.
    [IPET-ANNOTATED]    IPET with user-annotated loop bound overrides from schedule.json.
    [IPET-CONSERVATIVE] IPET using conservative fallback (--max-loop-bound) for unbounded loops.
    [CALCULATED]        Code-size heuristic (fallback when no disassembly or ELF available).
    [SIMULATED]         Instruction counts from Renode functional trace (approximate).

  RTA Assumptions:
    - Single-core analysis uses configured scheduling algorithm (RM/DM/EDF).
    - Tasks are strictly periodic with synchronous release at t=0.
    - Inter-core communication modeled as priority ceiling blocking term.
    - Resource dependencies utilize Priority Ceiling Protocol (PCP/SRP).
    - ISRs treated as highest-priority periodic tasks.

  For production use: measure actual WCET with on-hardware profiling
  (e.g. Segger SystemView, TRACE32) to validate these estimates.

========================================================================

