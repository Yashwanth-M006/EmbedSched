/* stm32f407_recursive.ld — STM32F407 linker script
 *
 * PROJECT 3: RECURSIVE_ISR
 * ========================
 * This linker script is structurally normal — no exotic sections,
 * no ITCM, standard F407 layout. The bug being tested is entirely
 * in the C source: a recursive function reachable from an ISR.
 *
 * DELIBERATE CHOICES:
 *
 * [1] _Min_Stack_Size = 0x400 (1KB)
 *     Small stack makes the overflow risk concrete. At runtime the
 *     recursive chain will consume stack unboundedly until HardFault.
 *     The analyzer must flag this even though it cannot compute the
 *     actual depth (recursion is statically unbounded).
 *
 * [2] Stack in SRAM1 (not CCM)
 *     F407 has CCM at 0x10000000. Using SRAM1 for the stack is
 *     a secondary finding: analyzer should note CCM is available
 *     and would give better isolation. This is INFO level only —
 *     the CRITICAL finding is the recursion.
 *
 * [3] Normal .bss placement
 *     .bss uses ~200 bytes. Stack headroom after .bss:
 *     0x20020000 - (0x200000xx + 0xC8) ≈ 130KB. Plenty of room
 *     for static analysis — the danger is DYNAMIC recursion depth,
 *     not static BSS pressure. Analyzer must distinguish these cases.
 *
 * WHAT THE ANALYZER MUST PRODUCE:
 *   [CRITICAL] [STATIC] recursion_detected
 *     Call chain: USART1_IRQHandler → parse_packet → parse_packet
 *     Stack depth: UNBOUNDED (recursion detected)
 *     _Min_Stack_Size = 1024 bytes — cannot bound worst-case usage.
 *
 *   [WARNING]  [STATIC] isr_in_flash
 *     USART1_IRQHandler at 0x0800xxxx (Flash, no ITCM on F407).
 *     Recommend ART accelerator.
 *
 *   [INFO]     [STATIC] stack_not_in_ccm
 *     Stack top is SRAM1. CCM available at 0x10000000 for isolation.
 */

_Min_Stack_Size = 0x400;   /* 1024 bytes — deliberately small */
_Min_Heap_Size  = 0x200;

MEMORY
{
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    SRAM1  (rwx) : ORIGIN = 0x20000000, LENGTH = 112K
    SRAM2  (rw)  : ORIGIN = 0x2001C000, LENGTH = 16K
    CCM    (rw)  : ORIGIN = 0x10000000, LENGTH = 64K
}

/* Stack top = SRAM1 top — NOT CCM (intentional suboptimal choice) */
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

    /* Explicit stack section so the analyzer can find _Min_Stack_Size */
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
