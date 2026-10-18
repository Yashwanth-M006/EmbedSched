/* stm32f746_itcm.ld — STM32F746 linker script
 *
 * PROJECT 2: ISR_IN_ITCM
 * =======================
 * This linker script correctly places ISR handlers and hot-path
 * functions into ITCM (Instruction Tightly Coupled Memory).
 *
 * ITCM on STM32F746:
 *   - Address: 0x00000000 – 0x00003FFF (16 KB)
 *   - Zero wait state, every access (no cache miss possible)
 *   - Accessed via dedicated I-bus, bypasses AXI flash and I-cache
 *   - DMA CANNOT reach ITCM (CPU-only interface)
 *   - Content must be COPIED from flash at startup (AT > FLASH)
 *
 * WHAT THE ANALYZER MUST DO WITH THIS FILE:
 *   [PASS]  ISR handlers in ITCM → must NOT fire "isr_in_flash" warning
 *   [PASS]  ITCM section 6,144B / 16,384B (37.5%) → no overflow
 *   [INFO]  Stack in DTCM → good placement, confirm it
 *   [INFO]  DMA buffers in SRAM2 on AHB_S2 → separated from CPU SRAM1
 *   [WARN]  spi_rx_buf in SRAM1 not SRAM2 → bus contention possible
 *           (deliberately introduced for rule 2 testing)
 *
 * CORRECT ITCM PLACEMENT PATTERN:
 *   In C: __attribute__((section(".itcm_text")))
 *   In LD: .itcm_text section with AT > FLASH (load from flash, run from ITCM)
 *   In startup: copy loop from _itcm_lma to _sitcm/_eitcm
 *
 * MEMORY REGIONS — STM32F746VG:
 *   FLASH  : 0x08000000, 1024K  (AXI flash, up to 7 wait states @ 216MHz)
 *   ITCM   : 0x00000000, 16K    (zero wait state, I-bus, no DMA)
 *   DTCM   : 0x20000000, 64K    (zero wait state, D-bus, no DMA, stack here)
 *   SRAM1  : 0x20010000, 240K   (AHB bus port AHB_S1, DMA-accessible)
 *   SRAM2  : 0x2004C000, 16K    (AHB bus port AHB_S2, DMA-accessible)
 */

_Min_Stack_Size = 0x800;    /* 2048 bytes */
_Min_Heap_Size  = 0x200;    /* 512 bytes  */

MEMORY
{
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    ITCM   (rwx) : ORIGIN = 0x00000000, LENGTH = 16K
    DTCM   (rw)  : ORIGIN = 0x20000000, LENGTH = 64K
    SRAM1  (rw)  : ORIGIN = 0x20010000, LENGTH = 240K
    SRAM2  (rw)  : ORIGIN = 0x2004C000, LENGTH = 16K
}

/* Stack top = DTCM top (zero wait state, CPU-only, DMA-isolated) */
_estack = ORIGIN(DTCM) + LENGTH(DTCM);   /* = 0x20010000 */

SECTIONS
{
    /* ── Vector table: must be at flash origin on reset ──
     *
     * NOTE: On Cortex-M7, the vector table STAYS in flash at 0x08000000.
     * ITCM starts at 0x00000000. After reset the CPU fetches the vector
     * from 0x08000000 (flash). The VTOR register can later be set to
     * point into ITCM if the vector table is copied there — but the
     * initial reset vector MUST be in flash.
     *
     * We do NOT relocate the vector table to ITCM in this project.
     * The handlers themselves are in ITCM; the table of pointers stays
     * in flash. This is the standard production pattern.
     */
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    /* ── .text: normal code stays in flash ── */
    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.glue_7)
        *(.glue_7t)
        *(.eh_frame)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        _etext = .;
    } >FLASH

    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } >FLASH

    .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } >FLASH
    .ARM        : {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } >FLASH

    /* ── .itcm_text: ISR handlers and hot functions → ITCM ──
     *
     * CORRECT PATTERN — all three parts required:
     *
     * [1] AT > FLASH: content is stored in flash (LMA), copied to ITCM
     *     (VMA) at startup. Without AT, the section would run from flash,
     *     defeating the purpose entirely.
     *
     * [2] _itcm_lma: load address in flash (source for startup copy loop)
     *     _sitcm: start VMA in ITCM (destination)
     *     _eitcm: end VMA in ITCM
     *
     * [3] Section size must not exceed ITCM capacity (16KB).
     *     The analyzer checks this as Rule 3.
     *
     * Functions placed here via: __attribute__((section(".itcm_text")))
     *
     * WHAT THE ANALYZER MUST VERIFY:
     *   - These symbols have addresses in [0x00000000, 0x00004000)
     *   - That address range = ITCM in the chip profile
     *   - Therefore: ISR in ITCM → Rule 1 must NOT fire
     *   - Section size 6144B / 16384B = 37.5% → Rule 3 must NOT fire
     */
    _itcm_lma = LOADADDR(.itcm_text);

    .itcm_text :
    {
        . = ALIGN(4);
        _sitcm = .;
        *(.itcm_text)
        *(.itcm_text*)
        . = ALIGN(4);
        _eitcm = .;
    } >ITCM AT>FLASH

    /* ── .data: initialized globals in DTCM ──
     * Placing .data in DTCM (not SRAM1) gives zero-wait-state
     * global variable access on the D-bus. Correct for hot globals.
     */
    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >DTCM AT>FLASH

    /* ── .bss: zero-init globals in DTCM ── */
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
        __bss_end__ = _ebss;
    } >DTCM

    /* ── .dma_buffers_s2: DMA buffers on SRAM2 (separate AHB port) ──
     *
     * CORRECT PLACEMENT for DMA buffers on STM32F7:
     *   SRAM1 (AHB_S1) and SRAM2 (AHB_S2) are on SEPARATE bus matrix
     *   slave ports. CPU data accesses go through SRAM1 (AHB_S1).
     *   If DMA buffers are in SRAM2 (AHB_S2), DMA transfers run on
     *   AHB_S2 while CPU runs on AHB_S1 → zero bus contention.
     *
     * The analyzer should detect this as CORRECT and emit:
     *   [INFO] dma_buffers_in_sram2_isolated: DMA buffers on AHB_S2,
     *          CPU code/data on DTCM/SRAM1 (AHB_S1) — no bus contention.
     *
     * DELIBERATE EXCEPTION for Rule 2 testing:
     *   spi_rx_buf is placed in SRAM1 (.dma_buffers_s1 section) rather
     *   than SRAM2. This single misplaced buffer should trigger the
     *   bus contention warning. See main.c for the __attribute__ placement.
     */
    .dma_buffers_s2 (NOLOAD) :
    {
        . = ALIGN(32);
        __dma_s2_start = .;
        *(.dma_buffers_s2)
        *(.dma_buffers_s2*)
        . = ALIGN(32);
        __dma_s2_end = .;
    } >SRAM2

    /* ── .dma_buffers_s1: DELIBERATELY MISPLACED buffer in SRAM1 ──
     * spi_rx_buf ends up here. SRAM1 is AHB_S1 — same port as CPU.
     * This is the intentional bus contention finding for Rule 2.
     */
    .dma_buffers_s1 (NOLOAD) :
    {
        . = ALIGN(32);
        __dma_s1_start = .;
        *(.dma_buffers_s1)
        *(.dma_buffers_s1*)
        . = ALIGN(32);
        __dma_s1_end = .;
    } >SRAM1

    /* ── .stack: explicit size, in DTCM ──
     * DTCM on M7 = SRAM with direct D-bus connection, zero wait state.
     * DMA cannot reach DTCM → stack accesses are never contended.
     * This is the M7 equivalent of CCM on the M4 (Project 1).
     */
    .stack (NOLOAD) :
    {
        . = ALIGN(8);
        __stack_start = .;
        . += _Min_Stack_Size;
        . = ALIGN(8);
        __stack_end = .;
    } >DTCM

    .heap (NOLOAD) :
    {
        . = ALIGN(8);
        __heap_start = .;
        . += _Min_Heap_Size;
        . = ALIGN(8);
        __heap_end = .;
    } >DTCM

    /DISCARD/ : { libc.a (*) libm.a (*) libgcc.a (*) }
    .ARM.attributes 0 : { *(.ARM.attributes) }
}
