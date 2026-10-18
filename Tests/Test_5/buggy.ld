/* buggy.ld — STM32F407 linker script with real stack-BSS overlap
 *
 * PROJECT 5: STACK_BSS_OVERLAP
 * ============================
 * This linker script has a correctly-written STACK section, but
 * the declared _Min_Stack_Size is far too small for the actual .bss
 * footprint. The result: __stack_end overlaps into the .bss region.
 *
 * THE BUG IN NUMBERS:
 *   SRAM1 total       : 112KB = 114,688 bytes (0x1C000)
 *   SRAM1 base        : 0x20000000
 *   SRAM1 top         : 0x2001C000
 *
 *   _estack           : 0x2001C000  (SRAM1 top — initial SP)
 *   _Min_Stack_Size   : 0x00000200  (512 bytes — far too small)
 *
 *   The .stack section is placed AFTER .bss in SRAM1.
 *   .data occupies ~80 bytes starting at 0x20000000.
 *   .bss  occupies ~63,744 bytes starting after .data.
 *
 *   __bss_end__  ≈ 0x20000050 + 0x0000F980 = 0x2000F9D0
 *   __stack_start is placed immediately after __bss_end__:
 *   __stack_start = 0x2000F9D0  (approximately)
 *   __stack_end   = __stack_start + 0x200 = 0x2000FBD0
 *
 *   Stack top (_estack) = 0x2001C000
 *   Stack grows DOWN from _estack toward __stack_start.
 *   When stack grows below __stack_start, it silently overwrites .bss.
 *
 * WHAT THE ANALYZER MUST COMPUTE:
 *   1. Read _Min_Stack_Size = 0x200 from linker script
 *   2. Read __bss_end__ from .map
 *   3. Read _estack from .map
 *   4. Actual usable stack = _estack - __bss_end__ - .stack_explicit
 *      (since .stack section was placed after .bss, stack starts at
 *       __stack_start which is right after __bss_end__)
 *   5. Worst-case call depth from .su = computed by analyzer
 *   6. Compare: if worst_depth > (_estack - __stack_start), CRITICAL
 *
 *   The key question: does the declared _Min_Stack_Size leave enough
 *   room between __bss_end__ and what the runtime stack actually needs?
 *
 *   Answer: 512 bytes declared, but the worst-case call chain needs
 *   more than that (see main.c — signal_process chain alone is 424B).
 *   The declared size is insufficient for safe operation.
 *
 * SECONDARY FINDING:
 *   Stack is in SRAM1, not CCM. Same INFO-level finding as Project 3.
 *
 * WHY THIS IS A DIFFERENT BUG FROM PROJECT 4:
 *   Project 4: no stack section at all — tool can't compute anything
 *   Project 5: stack section EXISTS, _Min_Stack_Size EXISTS, but the
 *              declared size is dangerously small relative to actual
 *              call depth. The tool can compute this precisely.
 */

_Min_Stack_Size = 0x200;   /* 512 bytes — DELIBERATELY TOO SMALL */
_Min_Heap_Size  = 0x200;

MEMORY
{
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    SRAM1  (rwx) : ORIGIN = 0x20000000, LENGTH = 112K
    SRAM2  (rw)  : ORIGIN = 0x2001C000, LENGTH = 16K
    CCM    (rw)  : ORIGIN = 0x10000000, LENGTH = 64K
}

_estack = ORIGIN(SRAM1) + LENGTH(SRAM1);   /* = 0x2001C000 */

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

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
    .ARM :
    {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } >FLASH

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

    /* ── .bss: large buffers fill most of SRAM ── */
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

    /* ── .stack: placed AFTER .bss in SRAM1 ──
     *
     * This is the structurally correct pattern — the tool can see
     * _Min_Stack_Size and __stack_start / __stack_end.
     *
     * The BUG is the VALUE: 512 bytes is insufficient.
     * After .bss fills most of SRAM1, the 512-byte stack region
     * that follows is eroded by actual call-chain depth at runtime.
     *
     * The analyzer computes:
     *   Declared budget: _Min_Stack_Size = 512B
     *   Worst-case depth (from .su + call graph): 424B
     *   Headroom: 512 - 424 = 88B  (only 17%)
     *   → WARNING: stack margin dangerously thin (< 20% headroom)
     *
     * Additionally:
     *   If .bss had grown by another 512 bytes (easy as projects scale):
     *   __stack_start would collide with the end of .bss section
     *   the linker would either silently pack them adjacent (no gap)
     *   or the runtime SP could descend into .bss globals
     */
    .stack (NOLOAD) :
    {
        . = ALIGN(8);
        __stack_start = .;
        . += _Min_Stack_Size;
        . = ALIGN(8);
        __stack_end = .;
    } >SRAM1

    .heap (NOLOAD) :
    {
        . = ALIGN(8);
        __heap_start = .;
        . += _Min_Heap_Size;
        . = ALIGN(8);
        __heap_end = .;
    } >SRAM1

    /DISCARD/ : { libc.a (*) libm.a (*) libgcc.a (*) }
    .ARM.attributes 0 : { *(.ARM.attributes) }
}
