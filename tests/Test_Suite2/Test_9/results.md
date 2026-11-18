
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
  SRAM1  : 108,810 / 114,688 bytes (94.9%)
  FLASH  : 0 / 1,048,576 bytes (0.0%)
  UNKNOWN: 115 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 100 / 100
  Deductions: explicit_stack_found (-0), autosar_hyperperiod_explosion (-0)

--------------------------------------------------
FINDINGS (2 total: 0 critical, 1 warnings, 1 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (0) - None Detected                                    |
+--------------------------------------------------------------------------+
+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [CALCULATED] autosar_hyperperiod_explosion
    Hyperperiod = 323,323ms — full simulation disabled.
    Showing representative 30ms window only. RTA used for schedulability verdict. [CALCULATED]
    Fix: Harmonize task periods (e.g., make them multiples of a common base) to reduce hyperperiod.

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
  Task_A                       7000    105.00    105.00      7000     6895.00     PASS
  Task_B                      11000    105.00    210.00     11000    10790.00     PASS
  Task_C                      13000    105.00    315.00     13000    12685.00     PASS
  Task_D                      17000    105.00    420.00     17000    16580.00     PASS
  Task_E                      19000    105.00    525.00     19000    18475.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [IPET] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_A                   task_a                     105.00       [IPET]           [Core 0]
  Task_B                   task_b                     105.00       [IPET]           [Core 0]
  Task_C                   task_c                     105.00       [IPET]           [Core 0]
  Task_D                   task_d                     105.00       [IPET]           [Core 0]
  Task_E                   task_e                     105.00       [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (5 periodic tasks):
    [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░░░░░]  4.4%  RM bound: 74.3%  →  GUARANTEED (below RM bound)
    Duty breakdown: Tasks 4.4% | ISRs 0.0% | Idle 95.6%

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_A                     0     1       7000    105.00    0.00         IPET    105.00         7000    6895.00
  Task_B                     0     2      11000    105.00    0.00         IPET    210.00        11000   10790.00
  Task_C                     0     3      13000    105.00    0.00         IPET    315.00        13000   12685.00
  Task_D                     0     4      17000    105.00    0.00         IPET    420.00        17000   16580.00
  Task_E                     0     5      19000    105.00    0.00         IPET    525.00        19000   18475.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Representative Window (First 30ms)  (scale: 468.8 µs/char)
  NOTE: Full simulation disabled due to hyperperiod explosion (323,323ms). Showing representative 30ms window only.
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_A           [A] █░░░░░░░░░░░░░██░░░░░░░░░░░░░██░░░░░░░░░░░░░██░░░░░░░░░░░░░█░░░░
  Task_B           [B] █░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░
  Task_C           [C] █░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░
  Task_D           [D] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░░░░░░
  Task_E           [E] ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░░░░░
                         0         5000       10000      15000     20000      25000      

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_A
    [B]  Task_B
    [C]  Task_C
    [D]  Task_D
    [E]  Task_E

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_A                            5           0.00            0.00  EXCELLENT (<1% of period)
  Task_B                            3          95.36           31.79  EXCELLENT (<1% of period)
  Task_C                            3         194.80           64.93  GOOD (<5% of period)
  Task_D                            2         294.13          147.06  GOOD (<5% of period)
  Task_E                            2         394.06          197.03  GOOD (<5% of period)
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

