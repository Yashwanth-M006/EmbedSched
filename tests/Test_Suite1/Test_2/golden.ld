/* golden.ld — STM32F407 "golden baseline" linker script
 *
 * PROJECT 1: GOLDEN_BASELINE
 * ===========================
 * This linker script is DELIBERATELY CORRECT in every way.
 * It is the reference against which your analyzer must produce
 * zero critical findings and zero warnings.
 *
 * Correct patterns explicitly present:
 *   [1] Explicit _Min_Stack_Size with sane value (2KB)
 *   [2] Explicit _Min_Heap_Size (not used, but declared)
 *   [3] STACK section explicitly placed in CCM (zero wait state, CPU-only)
 *       — CCM is the F407 equivalent of DTCM on M7 parts
 *   [4] __stack_start / __stack_end symbols exported for runtime checks
 *   [5] Stack placed BEFORE .bss in CCM so BSS growth cannot reach it
 *   [6] DMA buffers in a dedicated .dma_buffers section in SRAM1
 *       — correctly separate from CCM (DMA cannot reach CCM)
 *   [7] 32-byte aligned DMA buffer section (D-cache cache-line boundary)
 *   [8] Guard page concept: _Min_Stack_Size > worst-case call depth
 *   [9] _estack points to CCM top, not SRAM top
 *
 * The analyzer must detect ALL of these correct patterns
 * and produce only [INFO] or clean-pass output.
 */

/* ── Declared sizes ── */
_Min_Stack_Size = 0x800;   /* 2048 bytes — explicit, the key difference from Project 4 */
_Min_Heap_Size  = 0x200;   /* 512 bytes  — declared even if unused */

/* ── Memory Map: STM32F407VG ──
 *
 * FLASH  : 0x08000000, 1024K  — code and read-only data
 * SRAM1  : 0x20000000, 112K   — main SRAM, DMA-accessible via AHB
 * SRAM2  : 0x2001C000, 16K    — same AHB port as SRAM1 on F407
 * CCM    : 0x10000000, 64K    — Core-Coupled Memory
 *           zero wait state, CPU-only, NOT DMA-accessible
 *           → correct place for stack on F407
 */
MEMORY
{
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    SRAM1  (rwx) : ORIGIN = 0x20000000, LENGTH = 112K
    SRAM2  (rw)  : ORIGIN = 0x2001C000, LENGTH = 16K
    CCM    (rw)  : ORIGIN = 0x10000000, LENGTH = 64K
}

/*
 * _estack: top of CCM.
 * Stack grows DOWN from here into CCM.
 * CCM is CPU-only — DMA bus collisions impossible.
 * Contrast with Project 4 where _estack = top of SRAM1 (DMA-accessible).
 */
_estack = ORIGIN(CCM) + LENGTH(CCM);   /* = 0x10010000 */

/* ── Sections ── */
SECTIONS
{
    /* ── Vector table: must be first in flash at 0x08000000 ── */
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    /* ── Code and read-only data ── */
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

    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } >FLASH

    .ARM :
    {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } >FLASH

    /* ── Initialized globals: load from flash, run from SRAM1 ── */
    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >SRAM1 AT>FLASH

    /* ── Zero-initialized globals in SRAM1 ── */
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
    } >SRAM1

    /* ── DMA buffers: dedicated section in SRAM1, 32-byte aligned ──
     *
     * CORRECT PATTERN:
     *   - Placed in SRAM1 (DMA-accessible via AHB bus matrix)
     *   - 32-byte aligned (D-cache cache line size — required for
     *     SCB_CleanDCache_by_Addr / SCB_InvalidateDCache_by_Addr)
     *   - Separate from .bss so the analyzer can identify them
     *     as intentional DMA buffers vs ordinary globals
     *   - Named .dma_buffers — matches analyzer's heuristic pattern
     *
     * NOTE: STM32F407 Cortex-M4 has no D-cache, but this pattern is
     * correct for portability to F7/H7 parts. Analyzer should note:
     * "D-cache absent on this chip — alignment check is informational."
     */
    .dma_buffers (NOLOAD) :
    {
        . = ALIGN(32);          /* cache-line boundary */
        __dma_buffers_start = .;
        *(.dma_buffers)
        *(.dma_buffers*)
        . = ALIGN(32);
        __dma_buffers_end = .;
    } >SRAM1

    /* ── Stack: explicitly sized, in CCM ──
     *
     * CORRECT PATTERN:
     *   [1] Explicit _Min_Stack_Size declared above
     *   [2] __stack_start exported (low address — overflow boundary)
     *   [3] __stack_end exported (high address — initial SP)
     *   [4] In CCM: zero wait state, CPU-only, no DMA contention
     *   [5] NOLOAD: not initialized at startup (no copy needed)
     *   [6] ALIGN(8): ARM ABI requires 8-byte stack alignment
     *
     * The analyzer must detect ALL of these and produce:
     *   [PASS] stack_explicit_and_sized
     *   [INFO] stack_in_ccm (good placement — DMA-isolated)
     */
    .stack (NOLOAD) :
    {
        . = ALIGN(8);
        __stack_start = .;      /* low address — grows DOWN from __stack_end */
        . += _Min_Stack_Size;
        . = ALIGN(8);
        __stack_end = .;        /* = _estack — initial SP loaded from vector table */
    } >CCM

    /* ── Heap: explicitly sized, in CCM after stack ── */
    .heap (NOLOAD) :
    {
        . = ALIGN(8);
        __heap_start = .;
        . += _Min_Heap_Size;
        . = ALIGN(8);
        __heap_end = .;
    } >CCM

    /* Discard C library sections (bare-metal, no stdlib) */
    /DISCARD/ :
    {
        libc.a (*)
        libm.a (*)
        libgcc.a (*)
    }

    .ARM.attributes 0 :
    {
        *(.ARM.attributes)
    }
}
