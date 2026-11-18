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
  SRAM1  : 4,382,652 / 33,554,432 bytes (13.1%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_wcet_dominates (-10)

--------------------------------------------------
FINDINGS (6 total: 3 critical, 2 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 7065.00 µs  [IPET]
      Deadline         : 12000 µs
      Worst-case resp. : 17663.00 µs
      Overrun          : +5663.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau3' MISSES its deadline.
      Function mapped  : task3
      WCET             : 8832.00 µs  [IPET]
      Deadline         : 20000 µs
      Worst-case resp. : 26495.00 µs
      Overrun          : +6495.00 µs
      Call chain       : task3
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 178.7% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (2) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau1': WCET dominates its period.
      WCET / Period = 5299.00 / 7000 µs = 76%
      Leaves only 24% of the period for other tasks.
      Function: task1  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau2': WCET dominates its period.
      WCET / Period = 7065.00 / 12000 µs = 59%
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
  tau1                         7000   5299.00   5299.00      7000     1701.00     PASS
  tau2                        12000   7065.00  17663.00     12000    -5663.00     MISS
  tau3                        20000   8832.00  26495.00     20000    -6495.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      5299.00      [IPET]           [Core 0]
  tau2                     task2                      7065.00      [IPET]           [Core 0]
  tau3                     task3                      8832.00      [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  178.7%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 178.7% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1       7000   5299.00    0.00         IPET   5299.00         7000    1701.00
  tau2                       0     2      12000   7065.00    0.00         IPET  17663.00        12000   -5663.00
  tau3                       0     3      20000   8832.00    0.00         IPET  26495.00        20000   -6495.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 420000 µs  (scale: 6562.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ████████████████████████████████████████████████████████████████
  tau2             [B] █[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m|[0m[91m|[0m[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m
                         0       52500   105000  157500  210000  262500  315000  367500  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2

  DEADLINE MISSES (19 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 12000 µs,  finished @ 26494.40 µs  (+14494.40 µs late)
    [MISS]  tau2                 released @ 12000 µs,  deadline @ 24000 µs,  finished @ 48599.16 µs  (+24599.16 µs late)
    [MISS]  tau2                 released @ 24000 µs,  deadline @ 36000 µs,  finished @ 69450.17 µs  (+33450.17 µs late)
    [MISS]  tau2                 released @ 36000 µs,  deadline @ 48000 µs,  finished @ 90265.41 µs  (+42265.41 µs late)
    [MISS]  tau2                 released @ 48000 µs,  deadline @ 60000 µs,  finished @ 111155.74 µs  (+51155.74 µs late)
    [MISS]  tau2                 released @ 60000 µs,  deadline @ 72000 µs,  finished @ 132571.90 µs  (+60571.90 µs late)
    [MISS]  tau2                 released @ 72000 µs,  deadline @ 84000 µs,  finished @ 152822.65 µs  (+68822.65 µs late)
    [MISS]  tau2                 released @ 84000 µs,  deadline @ 96000 µs,  finished @ 173856.04 µs  (+77856.04 µs late)
    [MISS]  tau2                 released @ 96000 µs,  deadline @ 108000 µs,  finished @ 195526.27 µs  (+87526.27 µs late)
    [MISS]  tau2                 released @ 108000 µs,  deadline @ 120000 µs,  finished @ 215870.25 µs  (+95870.25 µs late)
    ... and 9 more.

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                             60           0.00            0.00  EXCELLENT (<1% of period)
  tau2                             20      184901.70        93069.96  HIGH (>20% of period
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
