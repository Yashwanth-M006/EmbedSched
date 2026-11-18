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
  SRAM1  : 4,747,898 / 33,554,432 bytes (14.1%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 35 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_wcet_dominates (-10), autosar_pcp_blocking (-0), autosar_pcp_blocking (-0)

--------------------------------------------------
FINDINGS (6 total: 2 critical, 1 warnings, 3 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (2) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_L' MISSES its deadline.
      Function mapped  : task_l
      WCET             : 14131.00 µs  [IPET]
      Deadline         : 40000 µs
      Worst-case resp. : 42393.00 µs
      Overrun          : +2393.00 µs
      Call chain       : task_l
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 106.0% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [IPET] autosar_wcet_dominates
    Task 'Task_H': WCET dominates its period.
      WCET / Period = 5299.00 / 10000 µs = 53%
      Leaves only 47% of the period for other tasks.
      Function: task_h  [IPET]
    Fix: Split task body into pre-emption points, move expensive computation to a lower-priority helper task, or increase the period.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (3)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [CALCULATED] autosar_pcp_blocking
    Task_H blocked by Task_L on mutex_spi for up to 3ms [CALCULATED] (PCP)
    Fix: PCP correctly bounds priority inversion to a single critical section.

  [INFO] [CALCULATED] autosar_pcp_blocking
    Task_M blocked by Task_L on mutex_i2c for up to 4.5ms [CALCULATED] (PCP)
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
  Task_H                      10000   5299.00   8299.00     10000     1701.00     PASS
  Task_M                      20000   3533.00  18631.00     20000     1369.00     PASS
  Task_L                      40000  14131.00  42393.00     40000    -2393.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_H                   task_h                     5299.00      [IPET]           [Core 0]
  Task_M                   task_m                     3533.00      [IPET]           [Core 0]
  Task_L                   task_l                     14131.00     [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  106.0%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 106.0% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_H                     0     1      10000   5299.00 3000.00         IPET   8299.00        10000    1701.00
  Task_M                     0     2      20000   3533.00 4500.00         IPET  18631.00        20000    1369.00
  Task_L                     0     3      40000  14131.00    0.00         IPET  42393.00        40000   -2393.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 40000 µs  (scale: 625.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_H           [A] █████████░░░░░░░█████████░░░░░░░█████████░░░░░░░█████████░░░░░░░
  Task_M           [B] ░░░░░░░░███████░░░░░░░░░░░░░░░░░░░░░░░░░███████░░░░░░░░░░░░░░░░░
  Task_L           [C] ░░░░░░░░░░░░░░██>░░░░░░░████████>░░░░░░░░░░░░░██>░░░░░░░████████
                         0       5000    10000   15000   20000   25000   30000   35000   

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_H
    [B]  Task_M
    [C]  Task_L

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_H                            4           0.00            0.00  EXCELLENT (<1% of period)
  Task_L                            1        8832.00         8832.00  HIGH (>20% of period
  Task_M                            2        5299.00         5299.00  HIGH (>20% of period
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
