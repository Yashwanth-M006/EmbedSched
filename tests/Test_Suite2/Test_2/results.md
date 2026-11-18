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
  SRAM1  : 15,412,282 / 33,554,432 bytes (45.9%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 15 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25)

--------------------------------------------------
FINDINGS (4 total: 3 critical, 0 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_D' MISSES its deadline.
      Function mapped  : task_d
      WCET             : 21196.00 µs  [IPET]
      Deadline         : 80000 µs
      Worst-case resp. : 91852.00 µs
      Overrun          : +11852.00 µs
      Call chain       : task_d
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'Task_E' MISSES its deadline.
      Function mapped  : task_e
      WCET             : 33913.00 µs  [IPET]
      Deadline         : 160000 µs
      Worst-case resp. : 169924.00 µs
      Overrun          : +9924.00 µs
      Call chain       : task_e
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 136.0% > 100%
      Tasks       : 5
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (0) - None Detected                                     |
+--------------------------------------------------------------------------+
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
  Task_A                      10000   3533.00   3533.00     10000     6467.00     PASS
  Task_B                      20000   5299.00   8832.00     20000    11168.00     PASS
  Task_C                      40000  10598.00  35328.00     40000     4672.00     PASS
  Task_D                      80000  21196.00  91852.00     80000   -11852.00     MISS
  Task_E                     160000  33913.00 169924.00    160000    -9924.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_A                   task_a                     3533.00      [IPET]           [Core 0]
  Task_B                   task_b                     5299.00      [IPET]           [Core 0]
  Task_C                   task_c                     10598.00     [IPET]           [Core 0]
  Task_D                   task_d                     21196.00     [IPET]           [Core 0]
  Task_E                   task_e                     33913.00     [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (5 periodic tasks):
    [█████████████████████████████|███████████]  136.0%  RM bound: 74.3%  →  OVERLOADED
    Duty breakdown: Tasks 136.0% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_A                     0     1      10000   3533.00    0.00         IPET   3533.00        10000    6467.00
  Task_B                     0     2      20000   5299.00    0.00         IPET   8832.00        20000   11168.00
  Task_C                     0     3      40000  10598.00    0.00         IPET  35328.00        40000    4672.00
  Task_D                     0     4      80000  21196.00    0.00         IPET  91852.00        80000  -11852.00
  Task_E                     0     5     160000  33913.00    0.00         IPET 169924.00       160000   -9924.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 160000 µs  (scale: 2500.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] ██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░██░░
  Task_B           [B] ░███░░░░░███░░░░░███░░░░░███░░░░░███░░░░░███░░░░░███░░░░░███░░░░
  Task_C           [C] ░░░█>███>░░█>██░░░░█>███>░░█>██░░░░█>███>░░█>██░░░░█>███>░░█>██░
  Task_D           [D] ░░░░░░░░░░░░░░██>░░░░░░░░░░░░░██>░░░░░░░░░░░░░██>░░░░░░░░░░░░░██
                         0       20000   40000   60000   80000   100000  120000  140000  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C
    [D]  Task_D

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                           16           0.00            0.00  EXCELLENT (<1% of period)
  Task_B                            8        3533.00         3533.00  MODERATE (<20% of period)
  Task_C                            4        8832.00         8832.00  HIGH (>20% of period
  Task_D                            1       35328.00        35328.00  HIGH (>20% of period
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
