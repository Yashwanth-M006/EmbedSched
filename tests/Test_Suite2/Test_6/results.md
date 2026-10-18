
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
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

┌──────────────────────────────────────────────────────────────────────────┐
│ CRITICAL FINDINGS (0) - None Detected                                    │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ WARNING FINDINGS (1) - REVIEW RECOMMENDED                                │
└──────────────────────────────────────────────────────────────────────────┘

  [WARNING] [CALCULATED] autosar_isr_flash_wcet
    adc_dma_isr in FLASH, 4 wait states inflating WCET. Recovery: 19.2µs → becomes ~1.1µs with ITCM (but STM32F407 has no ITCM, so ART accelerator suggestion instead). [CALCULATED]
    Fix: Set FLASH->ACR |= FLASH_ACR_ARTEN | FLASH_ACR_PRFTEN in SystemInit() to mitigate wait states.

┌──────────────────────────────────────────────────────────────────────────┐
│ INFORMATIONAL FINDINGS (3)                                               │
└──────────────────────────────────────────────────────────────────────────┘

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
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_CANTransmit           100000     20.00    141.33    100000    99858.67     PASS
  Task_SensorAgg              20000     40.00    121.33     20000    19878.67     PASS
  Task_MotorControl            1000     80.00     81.33      1000      918.67     PASS
  Task_ISR_ADC                 1000      1.33      1.33      1000      998.67     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [CALCULATED] — all tasks meet deadlines


1. TASK → FUNCTION MAPPING
  ──────────────────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source           Core
  ──────────────────────────────────────────────────────────────────────────────────────
  Task_CANTransmit         can_transmit_handler       20.00        [CALCULATED]     [Core 0]
  Task_SensorAgg           sensor_aggregate           40.00        [CALCULATED]     [Core 0]
  Task_MotorControl        motor_control_loop         80.00        [CALCULATED]     [Core 0]
  Task_ISR_ADC             adc_dma_isr                1.33         [CALCULATED]     [ISR]
  ──────────────────────────────────────────────────────────────────────────────────────

2. SCHEDULABILITY DASHBOARD

  Core 0  (4 periodic tasks):
    [███░░░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░░░░]  8.4%  RM bound: 75.7%  →  GUARANTEED (below RM bound)

  ● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [CALCULATED]

3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_CANTransmit           0     3     100000     20.00    0.00   CALCULATED    141.33       100000   99858.67
  Task_SensorAgg             0     2      20000     40.00    0.00   CALCULATED    121.33        20000   19878.67
  Task_MotorControl          0     1       1000     80.00    0.00   CALCULATED     81.33         1000     918.67
  Task_ISR_ADC               0     0       1000      1.33    0.00   CALCULATED      1.33         1000     998.67
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
  Task_CANTransmit                  1         108.63          108.63  EXCELLENT  (<1% of period)
  Task_ISR_ADC                    100           0.00            0.00  EXCELLENT  (<1% of period)
  Task_MotorControl               100           1.33            1.23  EXCELLENT  (<1% of period)
  Task_SensorAgg                    5          81.19           75.09  EXCELLENT  (<1% of period)
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

