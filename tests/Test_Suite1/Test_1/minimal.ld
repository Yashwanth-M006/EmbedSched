/* minimal.ld — STM32F407 linker script
 *
 * PROJECT 4: NO_STACK_SECTION
 * ============================
 * This linker script deliberately omits:
 *   - _Min_Stack_Size definition
 *   - _Min_Heap_Size definition
 *   - Any explicit STACK or HEAP section
 *   - __stack_start / __stack_end symbols
 *
 * The stack exists only implicitly: ARM Cortex-M loads SP from
 * the first vector table entry (_estack) at reset. Here _estack
 * is set to SRAM top. The actual usable stack = SRAM_top - __bss_end__.
 * This quantity is INVISIBLE to the linker and to static analysis
 * unless the analyzer explicitly infers it.
 *
 * BUG THIS EXPOSES:
 *   If a naive analyzer assumes "no stack section = no stack problem",
 *   it will silently miss stack overflow risk when .bss grows large.
 *   The correct behavior is to warn: "stack size unverifiable — no
 *   explicit STACK section; inferred headroom = SRAM_top - __bss_end__"
 */

/* ── Memory Map: STM32F407VG ── */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/*
 * _estack: top of SRAM, used as initial SP value in vector table.
 * No stack SIZE is communicated to the linker — only the top address.
 * Contrast with the "good" linker script pattern:
 *   _Min_Stack_Size = 0x400;
 *   .stack : { . += _Min_Stack_Size; } >SRAM
 */
_estack = ORIGIN(SRAM) + LENGTH(SRAM);   /* = 0x20020000 */

/* ── Sections ── */
SECTIONS
{
    /* ── .isr_vector: vector table must be first in flash ── */
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    /* ── .text: all code and read-only data ── */
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

    /* ── .rodata: const data stays in flash ── */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } >FLASH

    /* ── ARM exception unwind tables ── */
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

    /* ── .data: initialized globals — loaded from flash, run in SRAM ── */
    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >SRAM AT>FLASH

    /* ── .bss: zero-initialized globals in SRAM ── */
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
    } >SRAM

    /*
     * NOTHING AFTER .bss.
     *
     * Stack grows DOWN from _estack (0x20020000) toward __bss_end__.
     * The analyzer must detect:
     *   1. No _Min_Stack_Size symbol anywhere in this file.
     *   2. No explicit STACK section.
     *   3. Implicit headroom = _estack - __bss_end__
     *      (only computable after seeing .data and .bss sizes)
     *
     * A correct analyzer output:
     *   [WARNING] [STATIC] no_explicit_stack_section
     *     No _Min_Stack_Size or STACK section found in linker script.
     *     Stack size is unverifiable at link time.
     *     Inferred headroom: _estack(0x20020000) - __bss_end__(0x20002xxx)
     *     = ~Nxx bytes. Verify manually against worst-case call depth.
     */

    /* Discard unwanted sections */
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
