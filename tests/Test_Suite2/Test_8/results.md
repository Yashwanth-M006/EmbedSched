
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
  SRAM1  : 0 / 114,688 bytes (0.0%)
  FLASH  : 5,843,548 / 16,777,216 bytes (34.8%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_edf_priority_null (-0), autosar_edf_constrained_deadline (-0)

--------------------------------------------------
FINDINGS (8 total: 5 critical, 1 warnings, 2 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (5) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_A' MISSES its deadline.
      Function mapped  : task_a
      WCET             : 5299.00 µs  [IPET]
      Deadline         : 8000 µs
      Worst-case resp. : 22991.00 µs
      Overrun          : +14991.00 µs
      Call chain       : task_a
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_B' MISSES its deadline.
      Function mapped  : task_b
      WCET             : 8832.00 µs  [IPET]
      Deadline         : 15000 µs
      Worst-case resp. : 40683.00 µs
      Overrun          : +25683.00 µs
      Call chain       : task_b
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_C' MISSES its deadline.
      Function mapped  : task_c
      WCET             : 14131.00 µs  [IPET]
      Deadline         : 30000 µs
      Worst-case resp. : 60796.00 µs
      Overrun          : +30796.00 µs
      Call chain       : task_c
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 132.5% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

  [CRITICAL] [EDF] autosar_edf_constrained_deadline
    EDF Processor Demand Analysis: FAILED at L=18000.0µs (demand h(18000.0) > 18000.0µs).
    Fix: Use processor demand analysis (PDA) for precise EDF schedulability.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'Task_A': WCET dominates its period.
      WCET / Period = 5299.00 / 10000 µs = 53%
      Leaves only 47% of the period for other tasks.
      Function: task_a  [IPET]
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
  Task_A                      10000   5299.00  22991.00      8000   -14991.00     MISS
  Task_B                      20000   8832.00  40683.00     15000   -25683.00     MISS
  Task_C                      40000  14131.00  60796.00     30000   -30796.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_A                   task_a                     5299.00      [IPET]           [Core 0]
  Task_B                   task_b                     8832.00      [IPET]           [Core 0]
  Task_C                   task_c                     14131.00     [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████████████|█]  132.5%  EDF bound: 100.0% (constrained deadline)  →  DEADLINE MISS (demand analysis: h(t) > t)
    Duty breakdown: Tasks 132.5% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_A                     0   EDF      10000   5299.00    0.00         IPET  22991.00         8000  -14991.00
  Task_B                     0   EDF      20000   8832.00    0.00         IPET  40683.00        15000  -25683.00
  Task_C                     0   EDF      40000  14131.00    0.00         IPET  60796.00        30000  -30796.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 40000 µs  (scale: 625.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] █████████░░░░░░░░░░░████████░░░░█████████░░░░░░░░░░░░░░░░░░░░░░░
  Task_B           [B] ░░░░░░░░█████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█████████
  Task_C           [C] ░░░░░░░░░░░░░░░░░░░░░░░░░░░█████>░░░░░░░████████[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░░░░
                         0       5000    10000   15000   20000   25000   30000   35000   

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C

  DEADLINE MISSES (1 events):
    [MISS]  Task_C               released @ 0 µs,  deadline @ 30000 µs,  finished @ 34683.86 µs  (+4683.86 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                            3        2680.81          893.60  HIGH (>20% of period
  Task_B                            2       14683.86         9884.50  HIGH (>20% of period
  Task_C                            1       17214.73        17214.73  HIGH (>20% of period
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

