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
  SRAM1  : 51,336 / 1,048,576 bytes (4.9%)
  FLASH  : 0 / 1,048,576 bytes (0.0%)
  UNKNOWN: 143 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 95 / 100
  Deductions: explicit_stack_found (-0), isr_always_in_flash (-0), autosar_reset_handler_excluded (-0), autosar_isr_flash_wcet (-5)

--------------------------------------------------
FINDINGS (4 total: 0 critical, 1 warnings, 3 info)
--------------------------------------------------

+--------------------------------------------------------------------------+
| CRITICAL FINDINGS (0) - None Detected                                    |
+--------------------------------------------------------------------------+
+--------------------------------------------------------------------------+
| WARNING FINDINGS (1) - REVIEW RECOMMENDED                                |
+--------------------------------------------------------------------------+

  [WARNING] [CALCULATED] autosar_isr_flash_wcet
    adc_dma_isr in FLASH, 4 wait states inflating WCET. Recovery: 19.2µs → becomes ~1.1µs with ITCM (but STM32F407 has no ITCM, so ART accelerator suggestion instead). [CALCULATED]
    Fix: Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit() to mitigate wait states.

+--------------------------------------------------------------------------+
| INFORMATIONAL FINDINGS (3)                                               |
+--------------------------------------------------------------------------+

  [INFO] [STATIC] explicit_stack_found
    Explicit stack reservation found.
      _Min_Stack_Size = 0x0400 (1024 bytes).
    Fix: No action needed.

  [INFO] [STATIC] isr_always_in_flash
    Chip 'STM32F407' (cortex-m4) has no ITCM.
      ISRs (Reset_Handler, adc_dma_isr) always execute from Flash on this chip.
      This is not a bug - it is a hardware constraint.
      To minimize ISR latency on this chip:
        - Verify ART Accelerator is enabled: FLASH_ACR bit 9 (ARTEN)
        - Verify Prefetch Buffer enabled: FLASH_ACR bit 8 (PRFTEN)
        - ART eliminates wait states for sequential Flash fetches,
          but does NOT eliminate cold-entry jitter on random vector fetch.
    Fix: Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit().

  [INFO] [STATIC] autosar_reset_handler_excluded
    Reset_Handler excluded — not a periodic ISR
    Fix: Startup handlers execute once at boot and are not schedulable entities.


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
 Priority Convention: Standard Real-Time (Lower numerical value = Higher priority)
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_ISR_ADC                 1000      0.74      0.74      1000      999.26     PASS
  Task_MotorControl            1000    141.00    141.74      1000      858.26     PASS
  Task_SensorAgg              20000     71.00    212.74     20000    19787.26     PASS
  Task_CANTransmit           100000     35.00    247.74    100000    99752.26     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [IPET] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_ISR_ADC             adc_dma_isr                0.74         [IPET]           [ISR]
  Task_MotorControl        motor_control_loop         141.00       [IPET]           [Core 0]
  Task_SensorAgg           sensor_aggregate           71.00        [IPET]           [Core 0]
  Task_CANTransmit         can_transmit_handler       35.00        [IPET]           [Core 0]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (4 periodic tasks):
    [█████░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░░░░]  14.6%  RM bound: 75.7%  →  GUARANTEED (below RM bound)
    Duty breakdown: Tasks 14.5% | ISRs 0.1% | Idle 85.4%

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [IPET]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_ISR_ADC               0     0       1000      0.74    0.00         IPET      0.74         1000     999.26
  Task_MotorControl          0     1       1000    141.00    0.00         IPET    141.74         1000     858.26
  Task_SensorAgg             0     2      20000     71.00    0.00         IPET    212.74        20000   19787.26
  Task_CANTransmit           0     3     100000     35.00    0.00         IPET    247.74       100000   99752.26
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 100000 µs  (scale: 1562.5 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_ISR_ADC     [A] ████████████████████████████████████████████████████████████████
  Task_MotorContro [B] ████████████████████████████████████████████████████████████████
  Task_SensorAgg   [C] █░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░
  Task_CANTransmit [D] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0       12500   25000   37500   50000   62500   75000   87500   

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  Task_ISR_ADC
    [B]  Task_MotorControl
    [C]  Task_SensorAgg
    [D]  Task_CANTransmit

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────────
  Task_CANTransmit                  1         203.96          203.96  EXCELLENT (<1% of period)
  Task_ISR_ADC                    100           0.00            0.00  EXCELLENT (<1% of period)
  Task_MotorControl               100           0.74            0.68  EXCELLENT (<1% of period)
  Task_SensorAgg                    5         139.84          131.16  EXCELLENT (<1% of period)
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
