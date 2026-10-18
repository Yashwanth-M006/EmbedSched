
====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 90 / 100
  Deductions: no_explicit_stack_section (-10), stack_in_sram_not_ccm (-0)

--------------------------------------------------
FINDINGS (2 total: 0 critical, 1 warnings, 1 info)
--------------------------------------------------

[WARNING] [STATIC] no_explicit_stack_section
  No _Min_Stack_Size or explicit STACK section found in linker script.
    Stack size is unverifiable at link time.
    The stack exists implicitly: SP is loaded from _estack at reset,
    growing down toward __bss_end__.
    Inferred headroom: _estack (0x20020000) - __bss_end__ (0x20001034) = 126,924 bytes (123.9 KB)
    WARNING: BSS growth will silently reduce this headroom.
  Fix: Add to linker script: _Min_Stack_Size = 0x400; and a STACK section.

[INFO] [HEURISTIC] stack_in_sram_not_ccm
  Stack top (_estack=0x20020000) is in SRAM1 (AHB bus, DMA accessible).
    CCM RAM (0x10000000, 64 KB) is available and is CPU-only:
      - DMA cannot reach CCM -> placing stack there eliminates bus contention
        between stack push/pop and DMA transfers.
      - Zero wait states for stack operations.
      - This is the STM32F407 equivalent of DTCM stack placement on M7.
  Fix: In linker script: _estack = ORIGIN(CCM) + LENGTH(CCM); and map STACK section >CCM.

====================================================

[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...

========================================================================
[1m AUTOSAR SCHEDULABILITY ANALYSIS[0m
========================================================================

[1m1. TASK → FUNCTION MAPPING[0m
  ────────────────────────────────────────────────────────────────────────
  AUTOSAR Task             Entry Function             WCET (µs)    Source
  ────────────────────────────────────────────────────────────────────────
  USART1_IRQHandler        uart_send_byte             0.17         [96m[CALCULATED][0m  [ISR]
  Task_RxProc              process_rx                 0.92         [96m[CALCULATED][0m  [Core 0]
  Task_SysInit             system_init                0.23         [96m[CALCULATED][0m  [Core 0]
  Task_UartPoll            uart_poll                  1.26         [96m[CALCULATED][0m  [Core 1]
  ────────────────────────────────────────────────────────────────────────

[1m2. SCHEDULABILITY DASHBOARD[0m

  Core 0  (3 periodic tasks):
    [92m[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|░░░░░░░░░][0m  0.1%  RM bound: 78.0%  →  [92mGUARANTEED (below RM bound)[0m

  Core 1  (1 periodic tasks):
    [92m[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|][0m  0.0%  RM bound: 100.0%  →  [92mGUARANTEED (below RM bound)[0m

  [92m● VERDICT: SCHEDULABLE[0m  — all tasks meet their deadlines (per RTA).

[1m3. RESPONSE TIME ANALYSIS TABLE[0m
  ────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ────────────────────────────────────────────────────────────────────────
  USART1_IRQHandler          0   250       1000      0.17    0.00 [96mCALCULATED[0m      0.17         1000 [92m999.83[0m
  Task_RxProc                0     2      10000      0.92    3.50 [96mCALCULATED[0m      4.60        10000 [92m9995.40[0m
  Task_SysInit               0     1      50000      0.23    0.00 [96mCALCULATED[0m      1.32        50000 [92m49998.68[0m
  Task_UartPoll              1     1       5000      1.26    0.00 [96mCALCULATED[0m      1.26         5000 [92m4998.74[0m
  ────────────────────────────────────────────────────────────────────────

[1m4. SIMULATED EXECUTION TIMELINE (Gantt Chart)[0m


  CORE 0  |  Hyperperiod: 50000 µs  (scale: 781.2 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  USART1_IRQHandle [A] ████░████░███░████░███░████░███░████░████░███░████░███░████░███░
  Task_RxProc      [B] █░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░█░░░░░░░░░░░░
  Task_SysInit     [C] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0           10000        20000        30000        40000        

  CORE 1  |  Hyperperiod: 50000 µs  (scale: 781.2 µs/char)
  ────────────────────────────────────────────────────────────────────────────────────────
  Task_UartPoll    [D] █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                         0           10000        20000        30000        40000        

  Legend:  █ = executing   ░ = idle   > = preemption point

  Task symbols:
    [A]  USART1_IRQHandler
    [B]  Task_RxProc
    [C]  Task_SysInit
    [D]  Task_UartPoll

[1m5. JITTER ANALYSIS[0m


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ────────────────────────────────────────────────────────────────────────
  Task                    Activations  Max Jitter µs  Mean Jitter µs Assessment
  ────────────────────────────────────────────────────────────────────────
  Task_RxProc                       5           0.17            0.17  EXCELLENT  (<1% of period)
  USART1_IRQHandler                50           0.00            0.00  EXCELLENT  (<1% of period)
  ────────────────────────────────────────────────────────────────────────
  NOTE: Jitter is measured against the ideal periodic release time.
  Non-zero jitter is caused by higher-priority task preemption.
  For sensor/control loops, high jitter degrades control stability.

[1m6. CONFIDENCE NOTES[0m

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

--------------------------------------------------
MEMORY MAP SUMMARY [STATIC]
--------------------------------------------------
  FLASH  : 1,638 / 1,048,576 bytes (0.2%)
  SRAM   : 4,138 / 131,072 bytes (3.2%)
  SRAM1  : 0 / 114,688 bytes (0.0%)
  SRAM2  : 0 / 16,384 bytes (0.0%)
  CCM    : 0 / 65,536 bytes (0.0%)
  UNKNOWN: 4,266 bytes
