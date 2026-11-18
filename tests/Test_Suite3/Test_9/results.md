
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
  SRAM1  : 3,286,994 / 33,554,432 bytes (9.8%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 923 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 15 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_pcp_blocking (-0), autosar_pcp_blocking (-0)

--------------------------------------------------
FINDINGS (6 total: 3 critical, 0 warnings, 3 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (3) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau2' MISSES its deadline.
      Function mapped  : task2
      WCET             : 5299.00 µs  [IPET]
      Deadline         : 12000 µs
      Worst-case resp. : 15365.00 µs
      Overrun          : +3365.00 µs
      Call chain       : task2
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [RTA/[IPET]] autosar_deadline_miss
    Task 'tau3' MISSES its deadline.
      Function mapped  : task3
      WCET             : 7065.00 µs  [IPET]
      Deadline         : 20000 µs
      Worst-case resp. : 24729.00 µs
      Overrun          : +4729.00 µs
      Call chain       : task3
      NOTE: WCET is [IPET] — treat response time as functional estimate.
    Fix: Raise priority, shorten period, reduce WCET by moving hot functions to ITCM, or offload work to a lower-priority task.

  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 123.6% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (0) - None Detected                                     |
+--------------------------------------------------------------------------+
+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (3)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [CALCULATED] autosar_pcp_blocking
    tau1 blocked by tau3 on R1 for up to 3ms [CALCULATED] (PCP)
    Fix: PCP correctly bounds priority inversion to a single critical section.

  [INFO] [CALCULATED] autosar_pcp_blocking
    tau2 blocked by tau3 on R1 for up to 3ms [CALCULATED] (PCP)
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
  tau1                         8000   3533.00   6533.00      8000     1467.00     PASS
  tau2                        12000   5299.00  15365.00     12000    -3365.00     MISS
  tau3                        20000   7065.00  24729.00     20000    -4729.00     MISS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: FAIL [IPET] — deadline miss detected


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  tau1                     task1                      3533.00      [IPET]           [Core 0]
  tau2                     task2                      5299.00      [IPET]           [Core 0]
  tau3                     task3                      7065.00      [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [███████████████████████████████|█████████]  123.6%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 123.6% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1       8000   3533.00 3000.00         IPET   6533.00         8000    1467.00
  tau2                       0     2      12000   5299.00 3000.00         IPET  15365.00        12000   -3365.00
  tau3                       0     3      20000   7065.00    0.00         IPET  24729.00        20000   -4729.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 120000 µs  (scale: 1875.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ██░░███░███░███░░██░░██░░███░███░░██░░███░███░███░░██░░███░███░░
  tau2             [B] ░████>███>█░░░████░█████░░░███>██████░░░███>███>██░░████░███>██░
  tau3             [C] ░░░░░░█>░░[91m|[0m[91m█[0m[91m█[0m[91m>[0m░░░[91m█[0m[91m█[0m[91m█[0m[91m>[0m[91m|[0m░[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░[91m█[0m[91m|[0m░░░[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░[91m█[0m[91m>[0m░░░[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░[91m█[0m[91m>[0m[91m█[0m[91m>[0m░░░[91m█[0m[91m█[0m
                         0       15000   30000   45000   60000   75000   90000   105000  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2
    [C]  tau3

  DEADLINE MISSES (3 events):
    [MISS]  tau3                 released @ 0 µs,  deadline @ 20000 µs,  finished @ 45772.76 µs  (+25772.76 µs late)
    [MISS]  tau3                 released @ 20000 µs,  deadline @ 40000 µs,  finished @ 83869.11 µs  (+43869.11 µs late)
    [MISS]  tau3                 released @ 40000 µs,  deadline @ 60000 µs,  finished @ 117610.44 µs  (+57610.44 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                             15           0.00            0.00  EXCELLENT (<1% of period)
  tau2                             10        3484.31         1650.74  HIGH (>20% of period
  tau3                              4       57610.44        34738.21  HIGH (>20% of period
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

