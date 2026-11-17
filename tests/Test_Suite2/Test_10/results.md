
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
  SRAM1  : 172 / 114,688 bytes (0.1%)
  FLASH  : 0 / 1,048,576 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 70 / 100
  Deductions: explicit_stack_found (-0), autosar_deadlock_risk (-30)

--------------------------------------------------
FINDINGS (2 total: 1 critical, 0 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (1) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [STATIC] autosar_deadlock_risk
    Deadlock risk detected — inconsistent lock acquisition order across tasks.
      Lock cycle: mutex_A → mutex_B → mutex_A
      Task_Core0_Alpha acquires: mutex_A → mutex_B
      Task_Core1_Beta acquires: mutex_B → mutex_A
      Enforce a consistent global lock ordering to eliminate the cycle. [STATIC]
    Fix: Impose a global total order on all locks (e.g., alphabetical or by ID). Every task must acquire locks in that order. Never acquire lock B while holding lock A if any other task acquires A after B.

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

  ⚠  DEADLOCK_RISK  ⚠
  ────────────────────────────────────────
  Deadlock risk detected — inconsistent lock acquisition order across tasks.
    Lock cycle: mutex_A → mutex_B → mutex_A
    Task_Core0_Alpha acquires: mutex_A → mutex_B
    Task_Core1_Beta acquires: mutex_B → mutex_A
    Enforce a consistent global lock ordering to eliminate the cycle. [STATIC]

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha            10000    114.00    114.00     10000     9886.00     PASS
  Task_Core1_Beta             20000    114.00    114.00     20000    19886.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [IPET-CONSERVATIVE] — all tasks meet timing deadlines  ⚠ DEADLOCK_RISK DETECTED


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha         task_core0_alpha           114.00       [IPET-CONSERVATIVE] [Core 0]
  Task_Core1_Beta          task_core1_beta            114.00       [IPET-CONSERVATIVE] [Core 1]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (1 periodic tasks):
    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░]  1.1%  RM bound: 100.0%  →  GUARANTEED (below RM bound)
    Duty breakdown: Tasks 1.1% | ISRs 0.0% | Idle 98.9%

  Core 1  (1 periodic tasks):
    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░]  0.6%  RM bound: 100.0%  →  GUARANTEED (below RM bound)
    Duty breakdown: Tasks 0.6% | ISRs 0.0% | Idle 99.4%

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [IPET-CONSERVATIVE]
    ⚠ WARNING: DEADLOCK_RISK detected — system may freeze at runtime despite
      meeting timing deadlines. See findings for details.

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha           0     1      10000    114.00    0.00 IPET-CONSERVATIVE    114.00        10000    9886.00
  Task_Core1_Beta            1     1      20000    114.00    0.00 IPET-CONSERVATIVE    114.00        20000   19886.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 20000 µs  (scale: 312.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha [A] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0               5000            10000           15000           

  CORE 1  |  Hyperperiod: 20000 µs  (scale: 312.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_Core1_Beta  [B] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0               5000            10000           15000           

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_Core0_Alpha
    [B]  Task_Core1_Beta

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha                  2           0.00            0.00  EXCELLENT (<1% of period)
  Task_Core1_Beta                   1           0.00            0.00  EXCELLENT (<1% of period)
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

  CONFIDENCE: [IPET-CONSERVATIVE]
  Tasks with conservative loop bounds: Task_Core0_Alpha, Task_Core1_Beta
  Microarchitectural pipeline & prefetch timing is modeled, but one or more loop bounds
  fell back to conservative limit (--max-loop-bound). Supply bounds via schedule.json or GCC -fopt-info.

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

