
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
  SRAM1  : 3,725,288 / 33,554,432 bytes (11.1%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_rm_suboptimal (-10)

--------------------------------------------------
FINDINGS (6 total: 3 critical, 1 warnings, 2 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_B' MISSES its deadline.
      Function mapped  : task_b
      WCET             : 5652.00 µs  [IPET]
      Deadline         : 6000 µs
      Worst-case resp. : 10951.00 µs
      Overrun          : +4951.00 µs
      Call chain       : task_b
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_C' MISSES its deadline.
      Function mapped  : task_c
      WCET             : 7065.00 µs  [IPET]
      Deadline         : 20000 µs
      Worst-case resp. : 28967.00 µs
      Overrun          : +8967.00 µs
      Call chain       : task_c
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 126.0% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

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

  [INFO] [STATIC] autosar_rm_suboptimal
    Task 'Task_B' has deadline < period (6000 µs < 15000 µs) — RM priority assignment is suboptimal, use DM. Switching to DM may resolve this miss.
    Fix: Change core scheduling algorithm to DM (Deadline Monotonic) or EDF.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
 Priority Convention: Standard Real-Time (Lower numerical value = Higher priority)
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_A                      10000   5299.00   5299.00     10000     4701.00     PASS
  Task_B                      15000   5652.00  10951.00      6000    -4951.00     MISS
  Task_C                      20000   7065.00  28967.00     20000    -8967.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_A                   task_a                     5299.00      [IPET]           [Core 0]
  Task_B                   task_b                     5652.00      [IPET]           [Core 0]
  Task_C                   task_c                     7065.00      [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  126.0%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 126.0% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_A                     0     1      10000   5299.00    0.00         IPET   5299.00        10000    4701.00
  Task_B                     0     2      15000   5652.00    0.00         IPET  10951.00         6000   -4951.00
  Task_C                     0     3      20000   7065.00    0.00         IPET  28967.00        20000   -8967.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 60000 µs  (scale: 937.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] ██████░░░░███████░░░░██████░░░░░██████░░░░███████░░░░██████░░░░░
  Task_B           [B] ░░░░░█[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░░░░░░[91m█[0m[91m|[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m|[0m░░░[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░
  Task_C           [C] ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░███>░░░░░░░░░░░░░░░░░░░░░░░░░░░░███
                         0         10000      20000      30000     40000      50000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C

  DEADLINE MISSES (4 events):
    [MISS]  Task_B               released @ 0 µs,  deadline @ 6000 µs,  finished @ 16250.00 µs  (+10250.00 µs late)
    [MISS]  Task_B               released @ 15000 µs,  deadline @ 21000 µs,  finished @ 27201.00 µs  (+6201.00 µs late)
    [MISS]  Task_B               released @ 30000 µs,  deadline @ 36000 µs,  finished @ 46250.00 µs  (+10250.00 µs late)
    [MISS]  Task_B               released @ 45000 µs,  deadline @ 51000 µs,  finished @ 57201.00 µs  (+6201.00 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                            6           0.00            0.00  EXCELLENT (<1% of period)
  Task_B                            4        5299.00         3274.50  HIGH (>20% of period
  Task_C                            1       27201.00        27201.00  HIGH (>20% of period
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

