
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in charts...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  DTCM   : 1,024 / 65,536 bytes (1.6%)
  SRAM1  : 34,956,612 / 67,108,864 bytes (52.1%)
  FLASH  : 0 / 67,108,864 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 100 / 100
  Deductions: explicit_stack_found (-0), autosar_pcp_blocking (-0), autosar_edf_priority_null (-0), autosar_edf_constrained_deadline (-0), autosar_hyperperiod_explosion (-0)

--------------------------------------------------
FINDINGS (5 total: 0 critical, 1 warnings, 4 info)
--------------------------------------------------

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (0) - None Detected                                    │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [CALCULATED] autosar_hyperperiod_explosion
    Hyperperiod = 3,300ms — full simulation disabled.
    Showing representative 30ms window only. RTA used for schedulability verdict. [CALCULATED]
    Fix: Harmonize task periods (e.g., make them multiples of a common base) to reduce hyperperiod.

┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (4)                                               │
└──────────────────────────────────────────────────────────────────────────┘

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [CALCULATED] autosar_pcp_blocking
    Task CANPublish blocked by lower priority tasks on shared resource for up to 1.0000333333333333ms [CALCULATED]
    Fix: PCP correctly bounds priority inversion to a single critical section.

  [INFO] [EDF] autosar_edf_priority_null
    EDF tasks must have priority=null — priority field ignored for EDF cores
    Fix: Ensure tasks on EDF cores omit the priority field or set priority=null.

  [INFO] [EDF] autosar_edf_constrained_deadline
    Task_ObjectDetect has constrained deadline (80.0ms < 100.0ms period) — processor demand analysis used instead of simple utilization check.
      Checked all scheduling points up to hyperperiod.
      Tightest margin found at L=33000.0µs.
    Fix: Use processor demand analysis (PDA) for precise EDF schedulability.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_VisionProc             33000  10000.00  10000.00     33000    23000.00     PASS
  Task_ObjectDetect          100000  20000.00  30000.00     80000    50000.00     PASS
  Task_CANPublish             50000   5000.00   8000.03     50000    41999.97     PASS
  Task_SafetyMonitor          10000   2000.00   2000.00     10000     8000.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [CALCULATED] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_VisionProc          vision_processing          10000.00     [CALCULATED]     [Core 0]
  Task_ObjectDetect        object_detection           20000.00     [CALCULATED]     [Core 0]
  Task_CANPublish          can_publish                5000.00      [CALCULATED]     [Core 1]
  Task_SafetyMonitor       safety_monitor             2000.00      [CALCULATED]     [Core 1]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (2 periodic tasks):
    [████████████████████░░░░░░░░░░░░░░░░░░░|░]  50.3%  EDF bound: 100.0% (constrained deadline)  →  GUARANTEED (demand analysis: h(t) <= t)

  Core 1  (2 periodic tasks):
    [████████████░░░░░░░░░░░░░░░░░░░░░|░░░░░░░]  30.0%  RM bound: 82.8%  →  GUARANTEED (below RM bound)

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_VisionProc            0   EDF      33000  10000.00    0.00   CALCULATED  10000.00        33000   23000.00
  Task_ObjectDetect          0   EDF     100000  20000.00    0.00   CALCULATED  30000.00        80000   50000.00
  Task_CANPublish            1     2      50000   5000.00 1000.03   CALCULATED   8000.03        50000   41999.97
  Task_SafetyMonitor         1     1      10000   2000.00    0.00   CALCULATED   2000.00        10000    8000.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Representative Window (First 30ms)  (scale: 468.8 µs/char)
  NOTE: Full simulation disabled due to hyperperiod explosion (3,300ms). Showing representative 30ms window only.
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_VisionProc  [A] ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█
  Task_ObjectDetec [B] ░░░░░░░░░░░░░░░░░░░░░███████████████████████████████████████████
                         0         5000       10000      15000     20000      25000      

  CORE 1  |  Representative Window (First 30ms)  (scale: 468.8 µs/char)
  NOTE: Full simulation disabled due to hyperperiod explosion (3,300ms). Showing representative 30ms window only.
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_SafetyMonit [C] █████░░░░░░░░░░░░░░░░█████░░░░░░░░░░░░░░░░█████░░░░░░░░░░░░░░░░█
  Task_CANPublish  [D] ░░░░███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_VisionProc
    [B]  Task_ObjectDetect
    [C]  Task_SafetyMonitor
    [D]  Task_CANPublish

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_CANPublish                   4        2000.00         2000.00  GOOD       (<5% of period)
  Task_ObjectDetect                 2       10000.00         9500.00  MODERATE   (<20% of period)
  Task_SafetyMonitor               20           0.00            0.00  EXCELLENT  (<1% of period)
  Task_VisionProc                   7           0.00            0.00  EXCELLENT  (<1% of period)
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

  All WCETs are [CALCULATED] from code-size heuristic.
  Response times are OPTIMISTIC LOWER BOUNDS — not measured values.
  The analysis is conservative for schedulability (real silicon may be slower).

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

