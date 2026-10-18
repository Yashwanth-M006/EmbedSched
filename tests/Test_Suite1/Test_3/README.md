# Test_3: isr_in_itcm (STM32F746, Cortex-M7)

## What this project tests

Your analyzer's **address-range discrimination for Rule 1 (ISR placement)**.

Three ISR handlers and three hot-path functions are explicitly placed in
ITCM (Instruction Tightly Coupled Memory) at addresses in the range
`[0x00000000, 0x00004000)`. Your analyzer must:

- Recognise that these addresses fall in the ITCM region, **not Flash**
- **Not fire** the "isr_in_flash" warning for any of them
- Fire the isr_in_flash warning **only** when an ISR address is in `[0x08000000, 0x08100000)`

A tool that fails this test will flood every well-written STM32F7 project
with false warnings, making it useless in production.

**Secondary test (Rule 2):** One DMA buffer (`spi_rx_buf`) is deliberately
placed in SRAM1 (AHB_S1) while the other two buffers are correctly in SRAM2
(AHB_S2). The bus contention warning must fire for `spi_rx_buf` only.

---

## File listing

```
project2_isr_in_itcm/
│
├── README.md                    ← this file
├── expected_output.txt          ← test oracle: precise pass/fail criteria
│
├── stm32f746_itcm.ld            ← STM32F746 linker script
│                                   ITCM section with AT>FLASH (copy pattern)
│                                   DTCM stack, SRAM1 misplaced buf, SRAM2 correct bufs
│
├── src/
│   ├── startup.s                ← STM32F746 vector table + THREE-PHASE Reset_Handler
│   │                              Phase 1: copy .itcm_text flash→ITCM (CRITICAL)
│   │                              Phase 2: copy .data flash→DTCM
│   │                              Phase 3: zero .bss in DTCM
│   └── main.c                   ← Cortex-M7 firmware
│                                   ISRs: TIM2, DMA2_Stream0, SPI1  → ITCM (ITCM_FUNC)
│                                   Hot functions: filter_sample, pid_update, control_loop → ITCM
│                                   DMA bufs: uart_tx_dma_buf, adc_dma_buf → SRAM2 (correct)
│                                             spi_rx_buf → SRAM1 (deliberately wrong)
│
├── build/
│   ├── firmware.elf             ← Real compiled ELF (Cortex-M7, hard-float ABI)
│   ├── firmware.map             ← Real linker map
│   └── main.su                  ← Stack usage (copied to su/)
│
├── su/
│   └── main.su                  ← 9 functions, all static bounds
│
└── chips/
    └── stm32f746.yaml           ← F746 chip profile
                                    ITCM present at 0x00000000
                                    DTCM present at 0x20000000
                                    SRAM1 (AHB_S1) and SRAM2 (AHB_S2) separate ports
                                    I-cache + D-cache both present (16KB, 32B lines)
```

---

## The core test: address discrimination

This is the single most important thing Project 2 verifies.

```
Region    | Address range               | Rule 1 behavior
----------|-----------------------------|-----------------
Flash     | [0x08000000, 0x08100000)    | ISR here → FIRE warning
ITCM      | [0x00000000, 0x00004000)    | ISR here → NO warning (correct)
DTCM      | [0x20000000, 0x20010000)    | ISR here → FIRE suspicious warning
SRAM1     | [0x20010000, 0x2004C000)    | ISR here → FIRE suspicious warning
SRAM2     | [0x2004C000, 0x20050000)    | ISR here → FIRE suspicious warning
```

The three ISRs in this project:

| Handler | Address | Region | Rule 1 |
|---|---|---|---|
| `TIM2_IRQHandler` | `0x00000000` | ITCM | MUST NOT fire |
| `DMA2_Stream0_IRQHandler` | `0x0000003C` | ITCM | MUST NOT fire |
| `SPI1_IRQHandler` | `0x00000090` | ITCM | MUST NOT fire |

If your tool fires "isr_in_flash" for any of these → bug in
`rules/isr_placement.py`. The fix: check if ISR address falls in the chip
profile's ITCM range **before** checking if it's in Flash.

---

## The veneer trap

When a function in ITCM is called from code in Flash, and the branch
distance exceeds the 24-bit BL instruction range, the linker emits a
**veneer stub** — a small trampoline in Flash that performs an indirect jump.

In this project:

```
__control_loop_veneer   0x08000358   Flash (linker-generated)
control_loop            0x00000204   ITCM  (user code)
```

The veneer lives in Flash. Your analyzer must **filter it out**:

```python
# In region_classifier.py or map_parser.py
if symbol.name.endswith('_veneer'):
    continue   # skip — linker artifact, not user code
```

If the veneer is not filtered, the tool will fire a false "function in
Flash that should be in ITCM" warning for `__control_loop_veneer`, which
is both wrong and misleading.

---

## The separate Rule 2 test (bus contention)

Three DMA buffers, two different sections, two different findings:

| Buffer | Section | Region | AHB Port | Contention? | Rule 2 |
|---|---|---|---|---|---|
| `uart_tx_dma_buf` | `.dma_buffers_s2` | SRAM2 | AHB_S2 | NO (CPU on AHB_S1) | MUST NOT fire |
| `adc_dma_buf` | `.dma_buffers_s2` | SRAM2 | AHB_S2 | NO | MUST NOT fire |
| `spi_rx_buf` | `.dma_buffers_s1` | SRAM1 | AHB_S1 | YES (CPU also AHB_S1) | MUST fire |

The distinction between F4 and F7 here is critical:
- On **STM32F407** (Project 1): SRAM1 and SRAM2 share AHB_S0 → no isolation benefit from moving between them
- On **STM32F746** (Project 2): SRAM1 on AHB_S1, SRAM2 on AHB_S2 → genuine isolation possible

Your chip profile encodes this via `bus_port` in each `memory_regions` entry.
The rule engine must look up the bus port, then check `bus_matrix.contending_pairs`.

---

## The ITCM copy pattern (what startup.s does that Project 1/4 don't)

Project 4 and Project 1 have a two-phase startup:
1. Copy `.data` from Flash → SRAM
2. Zero `.bss`

Project 2 has a **three-phase startup** — ITCM copy is Phase 1:

```asm
Reset_Handler:
    /* Phase 1: Copy .itcm_text from Flash LMA → ITCM VMA */
    ldr  r0, =_sitcm       /* ITCM destination start */
    ldr  r1, =_eitcm       /* ITCM destination end   */
    ldr  r2, =_itcm_lma    /* Flash source address   */
    ...copy loop...

    /* Phase 2: Copy .data from Flash → DTCM */
    ldr  r0, =_sdata
    ...

    /* Phase 3: Zero .bss */
    ldr  r2, =_sbss
    ...

    bl   main
```

The three linker symbols `_itcm_lma`, `_sitcm`, `_eitcm` are what your
startup parser must find to confirm ITCM content is being correctly
initialized. If any of these are missing from the `.map` file, the ITCM
content never gets copied and ISRs will HardFault on first invocation.

Your analyzer should check: do `_sitcm` and `_eitcm` exist in the map?
If `.itcm_text` is non-empty but `_sitcm`/`_eitcm` are absent from the map,
that means the linker script has the section but the startup copy loop
references are missing → silent runtime bug.

---

## Key numbers to know

| Metric | Value | Source |
|---|---|---|
| `TIM2_IRQHandler` address | `0x00000000` | `firmware.map` / `nm` |
| `DMA2_Stream0_IRQHandler` address | `0x0000003C` | `firmware.map` / `nm` |
| `SPI1_IRQHandler` address | `0x00000090` | `firmware.map` / `nm` |
| ITCM section size | `700 bytes` | `_eitcm - _sitcm = 0x2BC` |
| ITCM capacity | `16,384 bytes` | chip profile |
| ITCM usage | `4.3%` | `700 / 16384` |
| `spi_rx_buf` address | `0x20010000` | SRAM1 (AHB_S1) — misplaced |
| `uart_tx_dma_buf` address | `0x2004C000` | SRAM2 (AHB_S2) — correct |
| `adc_dma_buf` address | `0x2004C100` | SRAM2 (AHB_S2) — correct |
| `__stack_start` | `0x20000030` | DTCM — correct |
| Worst-case stack depth | `80 bytes` | `main(16)+control_loop(24)+pid_update(40)` |
| Stack budget | `2048 bytes` | `_Min_Stack_Size = 0x800` |
| Stack usage | `3.9%` | `80 / 2048` |
| ISR entry latency (ITCM, 216MHz) | `55.6 ns` | `12 cy × 4.63 ns` |
| ISR entry latency (Flash cold) | `351.9 ns` | `76 cy × 4.63 ns` |
| Veneer stub | `__control_loop_veneer @ 0x08000358` | linker artifact — ignore |

---

## How to rebuild from source

```bash
# Compile
arm-none-eabi-gcc \
  -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard \
  -O0 -ffunction-sections -fdata-sections \
  -fstack-usage -g -Wno-unused-variable \
  -c src/main.c -o build/main.o

arm-none-eabi-gcc \
  -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard \
  -O0 -g \
  -c src/startup.s -o build/startup.o

# Link
arm-none-eabi-gcc \
  -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard \
  -nostdlib \
  -T stm32f746_itcm.ld \
  -Wl,-Map=build/firmware.map \
  -o build/firmware.elf \
  build/startup.o build/main.o

# Collect stack usage
cp build/main.su su/main.su
```

---

## How to run against your analyzer

```bash
python main.py \
  --elf     project2_isr_in_itcm/build/firmware.elf \
  --map     project2_isr_in_itcm/build/firmware.map \
  --ld      project2_isr_in_itcm/stm32f746_itcm.ld \
  --chip    project2_isr_in_itcm/chips/stm32f746.yaml \
  --su-dir  project2_isr_in_itcm/su \
  --startup project2_isr_in_itcm/src/startup.s \
  --freq-mhz 216
```

Expected score: **80/100**  
One deduction: `dma_bus_contention` (-20) for `spi_rx_buf` in SRAM1.

---

## What you learn from this project

**1. Why `noinline` is mandatory with `section` attributes on ISRs.**
Without `__attribute__((noinline))`, GCC may inline the ISR body into
the Reset_Handler or into a caller in Flash, silently moving the code
out of ITCM. The section attribute alone is not sufficient. Always pair
them: `__attribute__((section(".itcm_text"), noinline))`.

**2. Why the ITCM copy must happen before `main` and before data init.**
If your startup copies `.data` before `.itcm_text`, any global initializer
that runs before `main` (C++ constructors, `__attribute__((constructor))`)
could call an ISR that runs from uninitialised ITCM. Order matters.

**3. Why SRAM2 isolation works on F7 but not F4.**
STM32F407 has one AHB bus matrix slave port serving both SRAM1 and SRAM2.
Moving a DMA buffer from SRAM1 to SRAM2 on F4 changes the address but
not the bus port — no contention benefit. On STM32F746 the two SRAMs are
on separate ports. This is why chip-profile YAML files are necessary —
the same firmware rule has different implications on different silicon.

**4. The veneer stub pattern.**
Any call from Flash code to ITCM code that exceeds the BL instruction's
24-bit offset range produces a linker-generated veneer. The veneer lives
in Flash, is named `__<function>_veneer`, and must be filtered from your
symbol analysis. It is not user code and not a misplaced function.
