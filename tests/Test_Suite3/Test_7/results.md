e:\firmware_analyzer\report\matplotlib_charts.py:208: UserWarning: Tight layout not applied. The left and right margins cannot be made large enough to accommodate all Axes decorations.
  plt.tight_layout()

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
  SRAM1  : 2,921,772 / 33,554,432 bytes (8.7%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_wcet_dominates (-10), autosar_edf_priority_null (-0), autosar_edf_constrained_deadline (-0)

--------------------------------------------------
FINDINGS (8 total: 4 critical, 2 warnings, 2 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (4) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau1' MISSES its deadline.
      Function mapped  : task1
      WCET             : 3533.00 µs  [IPET]
      Deadline         : 5000 µs
      Worst-case resp. : 19795.00 µs
      Overrun          : +14795.00 µs
      Call chain       : task1
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 10598.00 µs  [IPET]
      Deadline         : 7000 µs
      Worst-case resp. : 41254.00 µs
      Overrun          : +34254.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 164.9% > 100%
      Tasks       : 2
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

  [CRITICAL] [EDF] autosar_edf_constrained_deadline
    EDF Processor Demand Analysis: FAILED at L=7000.0µs (demand h(7000.0) > 7000.0µs).
    Fix: Use processor demand analysis (PDA) for precise EDF schedulability.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (2) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau1': WCET dominates its period.
      WCET / Period = 3533.00 / 6000 µs = 59%
      Leaves only 41% of the period for other tasks.
      Function: task1  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau2': WCET dominates its period.
      WCET / Period = 10598.00 / 10000 µs = 106%
      Leaves only -6% of the period for other tasks.
      Function: task2  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (2)                                               |
+--------------------------------------------------------------------------+

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
 Priority Convention: Standard Real-Time (Lower numerical value = Higher priority)
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  tau1                         6000   3533.00  19795.00      5000   -14795.00     MISS
  tau2                        10000  10598.00  41254.00      7000   -34254.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      3533.00      [IPET]           [Core 0]
  tau2                     task2                      10598.00     [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (2 periodic tasks):
    [███████████████████████████████████████|█]  164.9%  EDF bound: 100.0% (constrained deadline)  →  DEADLINE MISS (demand analysis: h(t) > t)
    Duty breakdown: Tasks 164.9% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0   EDF       6000   3533.00    0.00         IPET  19795.00         5000  -14795.00
  tau2                       0   EDF      10000  10598.00    0.00         IPET  41254.00         7000  -34254.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 30000 µs  (scale: 468.8 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ███████░░░░░░░░░░░░░░░░[91m|[0m░░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░░░░░░░░░░░░░░░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m
  tau2             [B] ░░░░░░████████[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2

  DEADLINE MISSES (3 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 7000 µs,  finished @ 13634.67 µs  (+6634.67 µs late)
    [MISS]  tau1                 released @ 6000 µs,  deadline @ 11000 µs,  finished @ 16849.47 µs  (+5849.47 µs late)
    [MISS]  tau2                 released @ 10000 µs,  deadline @ 17000 µs,  finished @ 27325.85 µs  (+10325.85 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                              3       15325.85         7653.51  HIGH (>20% of period
  tau2                              2        6849.47         4954.45  HIGH (>20% of period
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

