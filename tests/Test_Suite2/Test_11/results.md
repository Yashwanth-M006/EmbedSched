
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 2,450 / 114,688 bytes (2.1%)
  FLASH  : 0 / 1,048,576 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 90 / 100
  Deductions: explicit_stack_found (-0), autosar_heuristic_wcet (-10)

--------------------------------------------------
FINDINGS (2 total: 0 critical, 1 warnings, 1 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (0) - None Detected                                    │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [HEURISTIC] autosar_heuristic_wcet
    Task 'Task_C' WCET is heuristic — stack usage file missing or function 'task_c_missing' not found in ELF symbols or Renode trace. Recompile with -fstack-usage for higher confidence. [HEURISTIC]
      Current WCET estimate: 0.06 µs [HEURISTIC] — treat as unreliable.
    Fix: Verify 'entry_function' in schedule.json matches the C function name exactly. Recompile with -ffunction-sections and -fstack-usage. For higher confidence, profile on hardware with Segger SystemView or TRACE32.

┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (1)                                               │
└──────────────────────────────────────────────────────────────────────────┘

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.


--------------------------------------------------
DYNAMIC PROFILE [SIMULATED - Renode, functional only]
--------------------------------------------------
  task_a_body         : 1,176 instrs - 100.0% of total (HOT)

  NOTE: Simulated execution (Renode) provides accurate control flow but
  does NOT model cache effects or bus arbitration. Timing is functional only.

====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_C                     200000      0.06      9.28    200000   199990.72     PASS
  Task_B                     100000      2.22      9.22    100000    99990.78     PASS
  Task_A                      50000      7.00      7.00     50000    49993.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [HEURISTIC] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_C                   task_c_missing             0.06         [HEURISTIC]      [Core 0]
  Task_B                   task_b_body                2.22         [CALCULATED]     [Core 0]
  Task_A                   task_a_body                7.00         [SIMULATED]      [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (3 periodic tasks):
    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░░░]  0.0%  RM bound: 78.0%  →  GUARANTEED (below RM bound)

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [HEURISTIC]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_C                     0     3     200000      0.06    0.00    HEURISTIC      9.28       200000  199990.72
  Task_B                     0     2     100000      2.22    0.00   CALCULATED      9.22       100000   99990.78
  Task_A                     0     1      50000      7.00    0.00    SIMULATED      7.00        50000   49993.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 200000 µs  (scale: 3125.0 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] █░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░
  Task_B           [B] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  Task_C           [C] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0       25000   50000   75000   100000  125000  150000  175000  

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                            4           0.00            0.00  EXCELLENT  (<1% of period)
  Task_B                            2           6.65            6.39  EXCELLENT  (<1% of period)
  Task_C                            1           8.76            8.76  EXCELLENT  (<1% of period)
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

  LOWEST CONFIDENCE: [HEURISTIC]
  Tasks with heuristic WCET: Task_C
  These functions were not found in the ELF symbol table, .su files, or Renode trace.
  The 10-cycle placeholder is NOT a measured value — schedulability verdict is UNRELIABLE.
  Fix: verify entry_function names and recompile with -ffunction-sections -fstack-usage.

  WCET Derivation Method:
    [CALCULATED]  Code-size heuristic: size_bytes / 2.5 bytes_per_insn × 1.15 penalty
                  Source: Thumb-2 ISA encoding statistics + ARMv7-M pipeline model.
                  Treat response times as OPTIMISTIC LOWER BOUNDS.

    [SIMULATED]   Instruction counts from Renode functional trace.
                  Renode does NOT model cache effects or bus arbitration.
                  Timing is functional only — treat as APPROXIMATE.

  RTA Assumptions:
    - Single-core analysis uses configured scheduling algorithm (RM/DM/EDF).
    - Tasks are strictly periodic with synchronous release at t=0.
    - Inter-core communication modeled as priority ceiling blocking term.
    - Resource dependencies utilize Priority Ceiling Protocol (PCP/SRP).
    - ISRs treated as highest-priority periodic tasks.

  For production use: measure actual WCET with on-hardware profiling
  (e.g. Segger SystemView, TRACE32) to validate these estimates.

========================================================================

