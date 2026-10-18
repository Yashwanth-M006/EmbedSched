# Test_1: no_stack_section

## What this project tests

Your analyzer's **parser robustness and fallback paths** when the linker
script contains no explicit stack definition.

This is the most common real-world linker script mistake. Many STM32
projects use a minimal linker script (copied from a bare example) that
defines `_estack = ORIGIN(SRAM) + LENGTH(SRAM)` and nothing else.
The stack exists — it lives between `__bss_end__` and `_estack` — but
its size is never declared anywhere the linker or a static tool can see.

**If your analyzer silently skips stack analysis when no `_Min_Stack_Size`
exists, it produces a false sense of safety. That is the bug this test exposes.**

---

## File listing

```
project4_no_stack_section/
│
├── README.md                   ← this file
├── expected_output.txt         ← test oracle: what the tool must produce
│
├── minimal.ld                  ← THE KEY FILE: linker script with no stack section
│                                 Read the comments inside carefully.
│
├── src/
│   ├── startup.s               ← Full STM32F407 vector table + Reset_Handler
│   │                             Note: _estack is NOT defined here.
│   │                             It comes from minimal.ld as SRAM top.
│   └── main.c                  ← Bare-metal UART firmware
│                                 .bss: 4136 bytes (rx/tx/frame/sensor/log buffers)
│                                 .data: 12 bytes
│                                 Call chain depth: 112 bytes worst case
│
├── build/
│   ├── firmware.elf            ← Real compiled ELF — feed this to objdump
│   ├── firmware.map            ← Real linker map — feed this to map_parser.py
│   └── main.su                 ← COPIED here for convenience (original in su/)
│
├── su/
│   └── main.su                 ← Stack usage file from -fstack-usage
│                                 All 6 functions with real frame sizes
│
└── chips/
    └── stm32f407.yaml          ← Chip profile: no ITCM, CCM present, ART accelerator
```

---

## The deliberate bugs / missing pieces

### 1. No `_Min_Stack_Size` in `minimal.ld`

```ld
/* This does NOT exist in minimal.ld: */
_Min_Stack_Size = 0x400;

/* This does NOT exist in minimal.ld: */
.stack (NOLOAD) : {
    . = ALIGN(8);
    __stack_start = .;
    . += _Min_Stack_Size;
    __stack_end = .;
} >SRAM
```

What exists instead:
```ld
_estack = ORIGIN(SRAM) + LENGTH(SRAM);   /* = 0x20020000 */
```

That single line is all the stack definition the firmware has.

### 2. No `__stack_start` or `__stack_end` symbols

Search the `.map` file — you will find `_estack` but no `_Min_Stack_Size`,
no `__stack_start`, no `__stack_end`. The analyzer must handle this case.

### 3. Implicit stack headroom

The actual stack headroom at runtime:

```
_estack      = 0x20020000   (SRAM top, from linker script)
__bss_end__  = 0x20001034   (end of .bss, from map file)
Headroom     = 0x20020000 - 0x20001034 = 126,924 bytes
```

This is plenty of room — the firmware is not actually at risk. But the
**tool cannot verify this** without explicitly computing it from `_estack`
and `__bss_end__`. The test checks that the tool does exactly that
computation rather than silently skipping stack analysis.

---

## How to run against your analyzer

```bash
python main.py \
  --elf   project4_no_stack_section/build/firmware.elf \
  --map   project4_no_stack_section/build/firmware.map \
  --ld    project4_no_stack_section/minimal.ld \
  --chip  project4_no_stack_section/chips/stm32f407.yaml \
  --su-dir project4_no_stack_section/su \
  --startup project4_no_stack_section/src/startup.s \
  --freq-mhz 168
```

---

## What the correct output looks like

See `expected_output.txt` for the full test oracle. The key findings:

| Finding | Severity | Tag | Must fire? |
|---|---|---|---|
| `no_explicit_stack_section` | WARNING | [STATIC] | YES |
| `isr_always_in_flash` (chip-specific) | INFO | [STATIC] | YES |
| `stack_in_sram_not_ccm` | INFO | [HEURISTIC] | OPTIONAL but good |
| `stack_overflow_risk` (critical) | CRITICAL | — | MUST NOT fire |

---

## How to rebuild from source

If you want to regenerate the build artifacts:

```bash
# Compile
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -ffunction-sections -fdata-sections \
  -fstack-usage -g -Wno-unused-variable \
  -c src/main.c -o build/main.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -ffunction-sections -fdata-sections \
  -fstack-usage -g \
  -c src/startup.s -o build/startup.o

# Link (no --gc-sections — keeps all BSS buffers)
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -nostdlib \
  -T minimal.ld \
  -Wl,-Map=build/firmware.map \
  -o build/firmware.elf \
  build/startup.o build/main.o

# Copy stack usage file
cp build/main.su su/main.su
```

---

## Key numbers to memorize for interviews

| Symbol | Address | How obtained |
|---|---|---|
| `_estack` | `0x20020000` | Linker script: `ORIGIN(SRAM) + LENGTH(SRAM)` |
| `__bss_end__` | `0x20001034` | `.map` file: end of `.bss` section |
| Inferred stack headroom | `126,924 bytes` | `_estack - __bss_end__` |
| `.bss` size | `4,136 bytes` | `arm-none-eabi-size firmware.elf` |
| `.data` size | `12 bytes` | `arm-none-eabi-size firmware.elf` |
| `.text` size | `1,336 bytes` | `arm-none-eabi-size firmware.elf` |
| Worst-case stack frame | `112 bytes` | `main(16)+uart_poll(32)+process_rx(64)` |
| Stack in SRAM not CCM | yes | `_estack` is in SRAM1 range, not CCM range |

---

## What you learn from this project

1. **How the ARM Cortex-M stack actually works** — the SP is initialized
   from the first vector table entry (`_estack`), not from any linker
   section. The stack "region" is just whatever RAM is between BSS and
   the SP starting value.

2. **Why explicit stack sections matter** — without a declared size, no
   tool (including yours) can guarantee the stack won't be overrun as
   `.bss` grows with new features.

3. **How to write the fallback path** — when `_Min_Stack_Size` is absent,
   your `ld_parser.py` must activate a fallback that looks up `_estack`
   from the map file and computes headroom from `__bss_end__`.

4. **Chip-specific behavior** — STM32F407 has no ITCM. Your chip profile
   system must handle this gracefully instead of blindly recommending
   ITCM placement on hardware that doesn't have it.
