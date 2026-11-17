
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts via IPET...
[AUTOSAR] Priority ordering mode: Standard (lower number = higher priority)
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 2,400 / 65,536 bytes (3.7%)
  SRAM1  : 3,286,994 / 33,554,432 bytes (9.8%)
  FLASH  : 0 / 33,554,432 bytes (0.0%)
  UNKNOWN: 924 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 25 / 100
  Deductions: explicit_stack_found (-0), autosar_deadline_miss (-30), autosar_cpu_overload (-25), autosar_concurrent_stack (-20)

--------------------------------------------------
FINDINGS (4 total: 2 critical, 1 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (2) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

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
      Utilization : 106.0% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
    Fix: Reduce WCET of dominant tasks, increase task periods, or offload tasks to another core.

+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [STATIC] autosar_concurrent_stack
    Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B) — stack overflow possible under full preemption [STATIC]
    Fix: Increase _Min_Stack_Size in linker.ld or reduce stack usage.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (1)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0960 (2400 bytes).
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
  tau1                        10000   3533.00   3533.00     10000     6467.00     PASS
  tau2                        15000   5299.00   8832.00     15000     6168.00     PASS
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
    [███████████████████████████████|█████████]  106.0%  RM bound: 78.0%  →  OVERLOADED
    Duty breakdown: Tasks 106.0% | ISRs 0.0% | Idle 0.0%

  ● VERDICT: NOT SCHEDULABLE  — deadline miss(es) detected by RTA.  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  tau1                       0     1      10000   3533.00    0.00         IPET   3533.00        10000    6467.00
  tau2                       0     2      15000   5299.00    0.00         IPET   8832.00        15000    6168.00
  tau3                       0     3      20000   7065.00    0.00         IPET  24729.00        20000   -4729.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 60000 µs  (scale: 937.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  tau1             [A] ████░░░░░░█████░░░░░░████░░░░░░░████░░░░░░█████░░░░░░████░░░░░░░
  tau2             [B] ░░░██████░░░░░░░██████░░░░░░░░░░░░░██████░░░░░░░█████░░░░░░░░░░░
  tau3             [C] ░░░░░░░░███>░░██>░░░░[91m|[0m[91m>[0m░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m>[0m░░░░░░░[91m█[0m[91m█[0m[91m|[0m[91m>[0m░░[91m█[0m[91m█[0m[91m>[0m░░░[91m█[0m[91m█[0m[91m>[0m░[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m[91m█[0m░░
                         0         10000      20000      30000     40000      50000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  tau1
    [B]  tau2
    [C]  tau3

  DEADLINE MISSES (2 events):
    [MISS]  tau3                 released @ 0 µs,  deadline @ 20000 µs,  finished @ 25677.91 µs  (+5677.91 µs late)
    [MISS]  tau3                 released @ 20000 µs,  deadline @ 40000 µs,  finished @ 44124.78 µs  (+4124.78 µs late)

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  tau1                              6           0.00            0.00  EXCELLENT (<1% of period)
  tau2                              4        3182.54         1550.02  HIGH (>20% of period
  tau3                              3        7706.49         5836.40  HIGH (>20% of period
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

