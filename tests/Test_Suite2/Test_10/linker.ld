MEMORY
{
  DTCM (xrw) : ORIGIN = 0x10000000, LENGTH = 64K
  SRAM1 (xrw) : ORIGIN = 0x20000000, LENGTH = 112K
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 1024K
}

_Min_Stack_Size = 0x400;
_estack = ORIGIN(DTCM) + LENGTH(DTCM);

SECTIONS
{
  .text :
  {
    *(.text)
    *(.text*)
  } >SRAM1

  .data :
  {
    *(.data)
  } >SRAM1

  .bss :
  {
    __bss_start__ = .;
    *(.bss)
    __bss_end__ = .;
  } >SRAM1

  .stack :
  {
    . = . + _Min_Stack_Size;
  } >DTCM
}
