
[AUTOSAR] Loading task configuration...
Error: Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols
Did you mean 'motor_control_loop'? (Levenshtein distance: 1)
[AUTOSAR] Extracting WCETs from firmware artifacts via IPET...
[AUTOSAR] Priority ordering mode: Standard (lower number = higher priority)
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 51,200 / 114,688 bytes (44.6%)
  FLASH  : 0 / 1,048,576 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 75 / 100
  Deductions: explicit_stack_found (-0), autosar_entry_function_mismatch (-25)

--------------------------------------------------
FINDINGS (2 total: 1 critical, 0 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (1) - ACTION REQUIRED                                  |
+--------------------------------------------------------------------------+

  [CRITICAL] [STATIC] autosar_entry_function_mismatch
    Error: Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols.
      Did you mean 'motor_control_loop'? (Levenshtein distance: 1)
      Task 'Task_MotorControl' is excluded from schedulability analysis.
    Fix: Update schedule.json: change entry_function from 'motor_controll_loop' to 'motor_control_loop'.

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
  Task_SensorAgg              20000     71.00     71.00     20000    19929.00     PASS
  Task_CANTransmit           100000     35.00    106.00    100000    99894.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [IPET] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_SensorAgg           sensor_aggregate           71.00        [IPET]           [Core 0]
  Task_CANTransmit         can_transmit_handler       35.00        [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (2 periodic tasks):
    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░]  0.4%  RM bound: 82.8%  →  GUARANTEED (below RM bound)
    Duty breakdown: Tasks 0.4% | ISRs 0.0% | Idle 99.6%

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_SensorAgg             0     2      20000     71.00    0.00         IPET     71.00        20000   19929.00
  Task_CANTransmit           0     3     100000     35.00    0.00         IPET    106.00       100000   99894.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 100000 µs  (scale: 1562.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_SensorAgg   [A] █░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░
  Task_CANTransmit [B] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0       12500   25000   37500   50000   62500   75000   87500   

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_SensorAgg
    [B]  Task_CANTransmit

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_CANTransmit                  1          69.43           69.43  EXCELLENT (<1% of period)
  Task_SensorAgg                    5           0.00            0.00  EXCELLENT (<1% of period)
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

