```
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
  SRAM1  : 1,826,144 / 33,554,432 bytes (5.4%)
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
      WCET             : 3533.00 µs  [IPET]
      Deadline         : 5000 µs
      Worst-case resp. : 5299.00 µs
      Overrun          : +299.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau3' MISSES its deadline.
      Function mapped  : task3
      WCET             : 3533.00 µs  [IPET]
      Deadline         : 8000 µs
      Worst-case resp. : 8832.00 µs
      Overrun          : +832.00 µs
      Call chain       : task3
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 138.4% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau2': WCET dominates its period.
      WCET / Period = 3533.00 / 6000 µs = 59%
      Leaves only 41% of the period for other tasks.
      Function: task2  [IPET]
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
  tau1                         4000   1766.00   1766.00      3000     1234.00     PASS
  tau2                         6000   3533.00   5299.00      5000     -299.00     MISS
  tau3                        10000   3533.00   8832.00      8000     -832.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      1766.00      [IPET]           [Core 0]
  tau2                     task2                      3533.00      [IPET]           [Core 0]
  tau3                     task3                      3533.00      [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  138.4%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 138.4% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1       4000   1766.00    0.00         IPET   1766.00         3000    1234.00
  tau2                       0     2       6000   3533.00    0.00         IPET   5299.00         5000    -299.00
  tau3                       0     3      10000   3533.00    0.00         IPET   8832.00         8000    -832.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 60000 µs  (scale: 937.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ██░░██░░███░███░░██░░███░███░███░░██░░███░███░███░░██░░███░███░░
  tau2             [B] ░████[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m[91m█[0m[91m|[0m░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m[91m█[0m[91m|[0m░░[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m░[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m[91m█[0m[91m█[0m[91m|[0m░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m[91m█[0m[91m|[0m[91m█[0m
  tau3             [C] ░░░░░░░░░░░██>░░░░░░░░░░██>░░░░░░░░░░░█>░░░░░░░░░░██>░░░░░░░░░░█
                         0         10000      20000      30000     40000      50000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2
    [C]  tau3

  DEADLINE MISSES (10 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 5000 µs,  finished @ 6437.04 µs  (+1437.04 µs late)
    [MISS]  tau2                 released @ 6000 µs,  deadline @ 11000 µs,  finished @ 11094.86 µs  (+94.86 µs late)
    [MISS]  tau2                 released @ 12000 µs,  deadline @ 17000 µs,  finished @ 18529.97 µs  (+1529.97 µs late)
    [MISS]  tau2                 released @ 18000 µs,  deadline @ 23000 µs,  finished @ 23252.31 µs  (+252.31 µs late)
    [MISS]  tau2                 released @ 24000 µs,  deadline @ 29000 µs,  finished @ 30910.07 µs  (+1910.07 µs late)
    [MISS]  tau2                 released @ 30000 µs,  deadline @ 35000 µs,  finished @ 35630.05 µs  (+630.05 µs late)
    [MISS]  tau2                 released @ 36000 µs,  deadline @ 41000 µs,  finished @ 42576.13 µs  (+1576.13 µs late)
    [MISS]  tau2                 released @ 42000 µs,  deadline @ 47000 µs,  finished @ 47687.12 µs  (+687.12 µs late)
    [MISS]  tau2                 released @ 48000 µs,  deadline @ 53000 µs,  finished @ 54776.88 µs  (+1776.88 µs late)
    [MISS]  tau2                 released @ 54000 µs,  deadline @ 59000 µs,  finished @ 59687.64 µs  (+687.64 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                             15           0.00            0.00  EXCELLENT (<1% of period)
  tau2                             10        1765.65         1156.97  HIGH (>20% of period
  tau3                              1       11094.86        11094.86  HIGH (>20% of period
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
```
