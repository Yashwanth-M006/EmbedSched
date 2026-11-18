
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
  SRAM1  : 3,652,200 / 33,554,432 bytes (10.9%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 822 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_wcet_dominates (-10), autosar_pcp_blocking (-0)

--------------------------------------------------
FINDINGS (7 total: 3 critical, 2 warnings, 2 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau1' MISSES its deadline.
      Function mapped  : task1
      WCET             : 7065.00 µs  [IPET]
      Deadline         : 10000 µs
      Worst-case resp. : 11065.00 µs
      Overrun          : +1065.00 µs
      Call chain       : task1
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 10598.00 µs  [IPET]
      Deadline         : 15000 µs
      Worst-case resp. : 24728.00 µs
      Overrun          : +9728.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 141.3% > 100%
      Tasks       : 2
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (2) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau1': WCET dominates its period.
      WCET / Period = 7065.00 / 10000 µs = 71%
      Leaves only 29% of the period for other tasks.
      Function: task1  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'tau2': WCET dominates its period.
      WCET / Period = 10598.00 / 15000 µs = 71%
      Leaves only 29% of the period for other tasks.
      Function: task2  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (2)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [CALCULATED] autosar_pcp_blocking
    tau1 blocked by tau2 on R1 for up to 4ms [CALCULATED] (PCP)
    Fix: PCP correctly bounds priority inversion to a single critical section.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
 Priority Convention: Standard Real-Time (Lower numerical value = Higher priority)
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  tau1                        10000   7065.00  11065.00     10000    -1065.00     MISS
  tau2                        15000  10598.00  24728.00     15000    -9728.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      7065.00      [IPET]           [Core 0]
  tau2                     task2                      10598.00     [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (2 periodic tasks):
    [█████████████████████████████████|███████]  141.3%  RM bound: 82.8%  →  OVERLOADED
    Duty breakdown: Tasks 141.3% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1      10000   7065.00 4000.00         IPET  11065.00        10000   -1065.00
  tau2                       0     2      15000  10598.00    0.00         IPET  24728.00        15000   -9728.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 30000 µs  (scale: 468.8 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ███████████████░░░░░░███████████████░░░░░░██████████████░░░░░░░░
  tau2             [B] ░░░░░░░░░░░░░░████████>░░░░░░░░░[91m|[0m░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░░░░░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2

  DEADLINE MISSES (1 events):
    [MISS]  tau2                 released @ 0 µs,  deadline @ 15000 µs,  finished @ 29274.72 µs  (+14274.72 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                              3           0.00            0.00  EXCELLENT (<1% of period)
  tau2                              2       14274.72        10502.39  HIGH (>20% of period
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

