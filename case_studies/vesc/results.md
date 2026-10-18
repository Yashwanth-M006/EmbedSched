
[AUTOSAR] Loading task configuration...
[AUTOSAR] Extracting WCETs from firmware artifacts...
[AUTOSAR] Running Response Time Analysis (RTA)...
[AUTOSAR] Running discrete-event scheduler simulation...
[AUTOSAR] Generating matplotlib charts in case_studies/vesc/charts/...
====================================================
 MEMORY MAP SUMMARY [STATIC]
====================================================
  CCM    : 65,260 / 65,536 bytes (99.6%)
  SRAM1  : 106,138 / 114,688 bytes (92.5%)
  SRAM2  : 0 / 16,384 bytes (0.0%)
  FLASH  : 424,585 / 1,048,576 bytes (40.5%)
  UNKNOWN: 3,537,155 bytes

====================================================
 FIRMWARE EFFICIENCY REPORT
====================================================

OVERALL SCORE: 0 / 100
  Deductions: dma_bus_contention (-20), dma_bus_contention (-20), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), dma_buffers_correctly_placed (-0), dma_buffers_correctly_placed (-0), unaligned_dma_buffer (-10), unaligned_dma_buffer (-10), no_explicit_stack_section (-10), autosar_heuristic_wcet (-10), autosar_heuristic_wcet (-10)

--------------------------------------------------
FINDINGS (36 total: 0 critical, 5 warnings, 31 info)
--------------------------------------------------

ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé CRITICAL FINDINGS (0) - None Detected                                    Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé WARNING FINDINGS (5) - REVIEW RECOMMENDED                                Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ

  [WARNING] [HEURISTIC] dma_bus_contention
    Buffer 'dma_isr_redir' is in SRAM1 (port AHB_S1).
      This bus is shared between CPU and DMA (CPU, DMA1, DMA2).
      Risk of ~30-35% CPU bandwidth degradation during active DMA transfers.
    Fix: Move buffer to a memory region with a dedicated DMA port (e.g. SRAM2).

  [WARNING] [HEURISTIC] dma_bus_contention
    Buffer 'dma_streams_mask' is in SRAM1 (port AHB_S1).
      This bus is shared between CPU and DMA (CPU, DMA1, DMA2).
      Risk of ~30-35% CPU bandwidth degradation during active DMA transfers.
    Fix: Move buffer to a memory region with a dedicated DMA port (e.g. SRAM2).

  [WARNING] [STATIC] no_explicit_stack_section
    No _Min_Stack_Size or explicit STACK section found in linker script.
      Stack size is unverifiable at link time.
      The stack exists implicitly: SP is loaded from _estack at reset,
      growing down toward __bss_end__.
    Fix: Add to linker script: _Min_Stack_Size = 0x400; and a STACK section.

  [WARNING] [HEURISTIC] autosar_heuristic_wcet
    Task 'Task_MCInterface' WCET is heuristic ΓÇö stack usage file missing or function 'stat_thread' not found in ELF symbols or Renode trace. Recompile with -fstack-usage for higher confidence. [HEURISTIC]
      Current WCET estimate: 2.10 ┬╡s [HEURISTIC] ΓÇö treat as unreliable.
    Fix: Verify 'entry_function' in schedule.json matches the C function name exactly. Recompile with -ffunction-sections and -fstack-usage. For higher confidence, profile on hardware with Segger SystemView or TRACE32.

  [WARNING] [HEURISTIC] autosar_heuristic_wcet
    Task 'Task_Periodic' WCET is heuristic ΓÇö stack usage file missing or function 'periodic_thread' not found in ELF symbols or Renode trace. Recompile with -fstack-usage for higher confidence. [HEURISTIC]
      Current WCET estimate: 1.95 ┬╡s [HEURISTIC] ΓÇö treat as unreliable.
    Fix: Verify 'entry_function' in schedule.json matches the C function name exactly. Recompile with -ffunction-sections and -fstack-usage. For higher confidence, profile on hardware with Segger SystemView or TRACE32.

ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé INFORMATIONAL FINDINGS (31)                                              Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_StructInit / DMA_StructInit: Unknown at 0x00000000, 34 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_PeriphIncOffsetSizeConfig / DMA_PeriphIncOffsetSizeConfig: Unknown at 0x00000000, 18 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_FlowControllerConfig / DMA_FlowControllerConfig: Unknown at 0x00000000, 18 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_SetCurrDataCounter / DMA_SetCurrDataCounter: Unknown at 0x00000000, 4 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetCurrDataCounter / DMA_GetCurrDataCounter: Unknown at 0x00000000, 6 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_DoubleBufferModeConfig / DMA_DoubleBufferModeConfig: Unknown at 0x00000000, 20 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_DoubleBufferModeCmd / DMA_DoubleBufferModeCmd: Unknown at 0x00000000, 18 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_MemoryTargetConfig / DMA_MemoryTargetConfig: Unknown at 0x00000000, 10 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetCurrentMemoryTarget / DMA_GetCurrentMemoryTarget: Unknown at 0x00000000, 8 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetCmdStatus / DMA_GetCmdStatus: Unknown at 0x00000000, 8 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetFIFOStatus / DMA_GetFIFOStatus: Unknown at 0x00000000, 8 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetFlagStatus / DMA_GetFlagStatus: Unknown at 0x00000000, 52 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_ClearFlag / DMA_ClearFlag: Unknown at 0x00000000, 44 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_GetITStatus / DMA_GetITStatus: Unknown at 0x00000000, 88 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.DMA_ClearITPendingBit / DMA_ClearITPendingBit: Unknown at 0x00000000, 4 bytes.
      DMA-accessible: UNKNOWN
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_DeInit at 0x805db38 - 24-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_DeInit at 0x805db38 - 24-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_Init at 0x805dc48 - 8-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_Init at 0x805dc48 - 8-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_Cmd at 0x805dc9c - 28-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_Cmd at 0x805dc9c - 28-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_ITConfig at 0x805dcae - 14-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    DMA_ITConfig at 0x805dcae - 14-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.dmaInit / dmaInit: FLASH at 0x08060020, 76 bytes.
      DMA-accessible: NO
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.dmaInit / dmaInit: FLASH at 0x08060020, 4 bytes.
      DMA-accessible: NO
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] unaligned_dma_buffer
    dmaStreamAllocate at 0x8060070 - 16-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    dmaStreamAllocate at 0x8060070 - 16-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.dmaStreamRelease / dmaStreamRelease: FLASH at 0x08060100, 68 bytes.
      DMA-accessible: NO
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] dma_buffers_correctly_placed
    DMA buffer section .text.dmaStreamRelease / dmaStreamRelease: FLASH at 0x08060100, 4 bytes.
      DMA-accessible: NO
      Alignment: 32-byte aligned ΓÇö correct for D-cache maintenance.
      Note: STM32F407 M4 has no D-cache; alignment is forward-compatible.
    Fix: No action needed.

  [INFO] [STATIC] unaligned_dma_buffer
    dma_isr_redir at 0x20019084 - 4-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))

  [INFO] [STATIC] unaligned_dma_buffer
    dma_streams_mask at 0x20019104 - 4-byte aligned, requires 32-byte.
      D-cache maintenance will affect adjacent memory.
    Fix: __attribute__((aligned(32)))


====================================================

==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task                    Period ┬╡s   WCET ┬╡s      R ┬╡s      D ┬╡s   Margin ┬╡s  Verdict
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task_Commands               10000      1.54     10.04     10000     9989.96     PASS
  Task_Timeout                10000      2.88      8.50     10000     9991.50     PASS
  Task_Periodic               10000      1.95      5.62     10000     9994.38     PASS
  Task_MCInterface            10000      2.10      3.67     10000     9996.33     PASS
  Task_FOC_ISR                   50      1.57      1.57        50       48.43     PASS
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Overall: PASS [HEURISTIC] ΓÇö all tasks meet deadlines


1. TASK ΓåÆ FUNCTION MAPPING
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  AUTOSAR Task             Entry Function             WCET (┬╡s)    Source           Core
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task_Commands            packet_process_thread      1.54         [CALCULATED]     [Core 0]
  Task_Timeout             timeout_thread             2.88         [CALCULATED]     [Core 0]
  Task_Periodic            periodic_thread            1.95         [HEURISTIC]      [Core 0]
  Task_MCInterface         stat_thread                2.10         [HEURISTIC]      [Core 0]
  Task_FOC_ISR             mcpwm_foc_adc_int_handler  1.57         [CALCULATED]     [ISR]
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

2. SCHEDULABILITY DASHBOARD

  Core 0  (5 periodic tasks):
    [ΓûêΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ|ΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ]  3.2%  RM bound: 74.3%  ΓåÆ  GUARANTEED (below RM bound)

  ΓùÅ VERDICT: SCHEDULABLE  ΓÇö all tasks meet their deadlines (per RTA).  [HEURISTIC]

3. RESPONSE TIME ANALYSIS TABLE
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task                    Core  Prio  Period ┬╡s   WCET ┬╡s  Blk ┬╡s       Source   WCRT ┬╡s  Deadline ┬╡s  Margin ┬╡s
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task_Commands              0     4      10000      1.54    0.00   CALCULATED     10.04        10000    9989.96
  Task_Timeout               0     3      10000      2.88    0.00   CALCULATED      8.50        10000    9991.50
  Task_Periodic              0     2      10000      1.95    0.00    HEURISTIC      5.62        10000    9994.38
  Task_MCInterface           0     1      10000      2.10    0.00    HEURISTIC      3.67        10000    9996.33
  Task_FOC_ISR               0     0         50      1.57    0.00   CALCULATED      1.57           50      48.43
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

4. SIMULATED EXECUTION TIMELINE (Gantt Chart)


  CORE 0  |  Hyperperiod: 10000 ┬╡s  (scale: 156.2 ┬╡s/char)
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task_FOC_ISR     [A] ΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûêΓûê
  Task_MCInterface [B] ΓûêΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ
  Task_Periodic    [C] ΓûêΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ
  Task_Timeout     [D] ΓûêΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ
  Task_Commands    [E] ΓûêΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæΓûæ
                         0           2000         4000         6000         8000         

  Legend:  Γûê = executing   Γûæ = idle   > = preemption point

  Task symbols:
    [A]  Task_FOC_ISR
    [B]  Task_MCInterface
    [C]  Task_Periodic
    [D]  Task_Timeout
    [E]  Task_Commands

5. JITTER ANALYSIS


  JITTER ANALYSIS  (start-time variation from ideal periodic release)
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task                    Activations  Max Jitter ┬╡s  Mean Jitter ┬╡s Assessment
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Task_Commands                     1           8.50            8.50  EXCELLENT  (<1% of period)
  Task_FOC_ISR                    200           0.00            0.00  EXCELLENT  (<1% of period)
  Task_MCInterface                  1           1.57            1.57  EXCELLENT  (<1% of period)
  Task_Periodic                     1           3.67            3.67  EXCELLENT  (<1% of period)
  Task_Timeout                      1           5.62            5.62  EXCELLENT  (<1% of period)
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  NOTE: Jitter is measured against the ideal periodic release time.
  Non-zero jitter is caused by higher-priority task preemption.
  For sensor/control loops, high jitter degrades control stability.
  Jitter on single-task cores reflects simulation granularity/drift, not real-world preemption delay.

6. VISUAL ARTIFACTS GENERATED (MATPLOTLIB CHARTS)
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Output     Description                      Artifact File
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  Output 1   Schedulability Dashboard         case_studies/vesc/charts//schedulability_dashboard.png
  Output 2   Gantt Schedule Timeline          case_studies/vesc/charts//gantt_chart.png
  Output 3   Response Time vs Deadline        case_studies/vesc/charts//response_time_chart.png
  Output 4   Start-Time Jitter Plot           case_studies/vesc/charts//jitter_chart.png
  ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

7. CONFIDENCE NOTES

  LOWEST CONFIDENCE: [HEURISTIC]
  Tasks with heuristic WCET: Task_MCInterface, Task_Periodic
  These functions were not found in the ELF symbol table, .su files, or Renode trace.
  The 10-cycle placeholder is NOT a measured value ΓÇö schedulability verdict is UNRELIABLE.
  Fix: verify entry_function names and recompile with -ffunction-sections -fstack-usage.

  WCET Derivation Method:
    [CALCULATED]  Code-size heuristic: size_bytes / 2.5 bytes_per_insn ├ù 1.15 penalty
                  Source: Thumb-2 ISA encoding statistics + ARMv7-M pipeline model.
                  Treat response times as OPTIMISTIC LOWER BOUNDS.

    [SIMULATED]   Instruction counts from Renode functional trace.
                  Renode does NOT model cache effects or bus arbitration.
                  Timing is functional only ΓÇö treat as APPROXIMATE.

  RTA Assumptions:
    - Single-core analysis uses configured scheduling algorithm (RM/DM/EDF).
    - Tasks are strictly periodic with synchronous release at t=0.
    - Inter-core communication modeled as priority ceiling blocking term.
    - Resource dependencies utilize Priority Ceiling Protocol (PCP/SRP).
    - ISRs treated as highest-priority periodic tasks.

  For production use: measure actual WCET with on-hardware profiling
  (e.g. Segger SystemView, TRACE32) to validate these estimates.

========================================================================

