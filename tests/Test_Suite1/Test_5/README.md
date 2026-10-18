# Project 5: stack_bss_overlap (STM32F407, Cortex-M4)

## What this project tests

Your analyzer's **address arithmetic and stack-BSS proximity check** —
specifically, whether it can compute the gap between `__bss_end__` and
`__stack_start` and correctly flag when that gap is zero bytes.

This is a pure arithmetic test. There is no recursion, no missing stack
section, no ITCM complication. The linker script is structurally correct:
it has `_Min_Stack_Size`, it has an explicit `.stack` section, it exports
`__stack_start` and `__stack_end`. Everything the analyzer needs exists.
The bug is that `_Min_Stack_Size = 512` while `.bss` has consumed 39.3KB
of SRAM1, leaving the `.stack` section starting at the exact same address
as `__bss_end__` — zero bytes of gap between them.

---

## The bug in one line

```
__bss_end__   = 0x20009D78
__stack_start = 0x20009D78   ← identical address — zero gap
```

Any new global variable added to this firmware grows `.bss` by its size,
making `__stack_start` either collide with the tail of `.bss` or cause
a linker overflow of SRAM1. The firmware is one buffer declaration away
from a silent link-time disaster.

---

## File listing

```
project5_stack_bss_overlap/
│
├── README.md                      ← this file
├── expected_output.txt            ← test oracle: 2 must-fire critical/warning,
│                                    2 must-fire info, 4 must-not-fire
│
├── buggy.ld                       ← THE KEY FILE: _Min_Stack_Size = 0x200 (512B)
│                                    .stack placed after .bss → zero gap guaranteed
│                                    Stack in SRAM1, not CCM (secondary finding)
│
├── src/
│   ├── startup.s                  ← Standard STM32F407 startup
│   └── main.c                     ← Signal-processing firmware
│                                    .bss: 40,292 bytes (ADC + FIR + IIR + logging buffers)
│                                    ISR: TIM3_IRQHandler → isr_log → pack_record (256B chain)
│                                    No recursion — clean DAG
│
├── build/
│   ├── firmware.elf               ← Real compiled ELF (Cortex-M4, hard-float)
│   ├── firmware.map               ← Real linker map with exact addresses
│   └── main.su                    ← Stack usage (copied to su/)
│
├── su/
│   └── main.su                    ← 13 functions, all static bounds
│                                    Deepest frame: pack_record (152B)
│
└── chips/
    └── stm32f407.yaml             ← F407 chip profile: no ITCM, CCM present
```

---

## What the analyzer must compute

The computation is entirely from `.map` symbols and `.ld` definitions:

```
Step 1: Parse buggy.ld
  _Min_Stack_Size = 0x200 = 512 bytes

Step 2: Parse firmware.map  
  __bss_end__    = 0x20009D78
  __stack_start  = 0x20009D78
  __stack_end    = 0x20009F78
  _estack        = 0x2001C000

Step 3: Compute gap
  gap = __stack_start - __bss_end__ = 0x20009D78 - 0x20009D78 = 0 bytes
  → CRITICAL: zero gap between BSS and stack section

Step 4: Compute depth ratio (from .su + call graph DFS)
  worst_depth = TIM3(16) + isr_log(88) + pack_record(152) = 256B
  ratio = 256 / 512 = 50.0%
  → WARNING: 50% usage with zero growth margin

Step 5: Combined preemption scenario
  main path deepest: main(16)+main_task(24)+signal_process(32)+apply_fir(136) = 208B
  ISR path deepest:  TIM3(16)+isr_log(88)+pack_record(152) = 256B
  Combined: 208 + 256 = 464B vs 512B budget = 90.6%
  → This is the realistic worst case: only 48B headroom under preemption
```

---

## Why gap = 0 is CRITICAL, not just WARNING

The `.stack` section in the linker script is a **declaration**, not an
enforced hardware boundary. At runtime on Cortex-M without MPU
configuration:

- The SP is loaded from `_estack` (`0x2001C000`, SRAM1 top) at reset
- It grows **downward freely** — the hardware does not know `__stack_start`
- If the SP descends past `__stack_start` into the tail of `.bss`, no
  fault fires unless an MPU guard region is configured

A zero-byte gap means the moment the actual runtime stack consumption
exceeds `_Min_Stack_Size` (512B), the SP is in `.bss`. The corruption
target is whichever global variables live at the end of `.bss` — in this
firmware, `g_proc_flags` and `g_sensor_cal`, which control signal
processing behaviour. The corruption manifests as intermittent incorrect
sensor readings, not as a clean crash — which makes it one of the hardest
bugs to trace in the field.

---

## Why this is different from Project 4

| | Project 4 | Project 5 |
|---|---|---|
| `_Min_Stack_Size` | **absent** | present (512B) |
| `.stack` section | **absent** | present |
| `__stack_start` | **absent** | present |
| Bug | no stack metadata at all | **zero gap + small size** |
| Rule triggered | `no_explicit_stack_section` (WARNING) | `stack_bss_zero_gap` (CRITICAL) |
| Tool path | fallback inference | primary arithmetic path |

The analyzer **must not** trigger the Project 4 fallback path when it sees
a valid `.stack` section. The condition `if _Min_Stack_Size is None` must
evaluate to False here. This tests that your two code paths are correctly
separated.

---

## The three traps for the call graph builder

### Trap 1: `apply_fir` and `apply_iir` inner loops

Both functions have nested `for` loops that compile to `b` (branch)
instructions, not `bl` (call). If your regex matches `b.n`, `bne`, etc.
as function calls, it will either report false callees or — worse — detect
false recursion.

**Verify:**
```bash
arm-none-eabi-objdump -d build/firmware.elf | \
  awk '/<apply_fir>:/{p=1} p && /\tbl\t/{print} p && /^[0-9a-f]+ <[^a]/{p=0}'
# Expected: empty — apply_fir has no bl instructions
```

### Trap 2: `pack_record` inner CRC loop

Same as above — `pack_record` has a `for (i = 0; i < pos; i++)` CRC loop
that compiles to `b`. Your analyzer must see `pack_record` as a leaf
(no `bl` callees), not as recursing on itself.

### Trap 3: `isr_log` calls both `format_timestamp` AND `pack_record`

These are two parallel callees — `isr_log` calls `format_timestamp` then
`pack_record` sequentially. Only one of them is on the stack at any time.
Your DFS must take the MAX of the two branches, not the SUM.

```
isr_log(88)
  ├── format_timestamp(88)  → total 88+88 = 176B
  └── pack_record(152)      → total 88+152 = 240B  ← pick this one (MAX)
```

If your DFS sums parallel branches instead of taking MAX, you'll report
428B for `isr_log`'s subtree — wrong, and would trigger a false CRITICAL
stack overflow.

---

## Key numbers

| Symbol / Metric | Value | Source |
|---|---|---|
| `_Min_Stack_Size` | `0x200` = 512 bytes | `buggy.ld` |
| `__bss_end__` | `0x20009D78` | `firmware.map` |
| `__stack_start` | `0x20009D78` | `firmware.map` |
| `__stack_end` | `0x20009F78` | `firmware.map` |
| `_estack` | `0x2001C000` | `firmware.map` |
| BSS-to-stack gap | **0 bytes** | `__stack_start - __bss_end__` |
| `.bss` size | 40,292 bytes (39.3 KB) | `arm-none-eabi-size` |
| Worst single chain | `TIM3→isr_log→pack_record = 256B` | `.su` + call graph |
| Depth ratio | `256/512 = 50.0%` | arithmetic |
| Combined preemption | `208+256 = 464B` | main+ISR |
| Combined headroom | `512-464 = 48B` (9.4%) | arithmetic |
| Deepest frame | `pack_record: 152B` | `su/main.su` |

---

## How to rebuild

```bash
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 \
  -O0 -ffunction-sections -fdata-sections -fstack-usage -g \
  -Wno-unused-variable \
  -c src/main.c -o build/main.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 \
  -O0 -g \
  -c src/startup.s -o build/startup.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 \
  -nostdlib -T buggy.ld \
  -Wl,-Map=build/firmware.map \
  -o build/firmware.elf \
  build/startup.o build/main.o

cp build/main.su su/main.su
```

---

## How to run against your analyzer

```bash
python main.py \
  --elf     project5_stack_bss_overlap/build/firmware.elf \
  --map     project5_stack_bss_overlap/build/firmware.map \
  --ld      project5_stack_bss_overlap/buggy.ld \
  --chip    project5_stack_bss_overlap/chips/stm32f407.yaml \
  --su-dir  project5_stack_bss_overlap/su \
  --startup project5_stack_bss_overlap/src/startup.s \
  --freq-mhz 168
```

Expected score: **45/100**

---

## What you learn from this project

**1. The declared `.stack` section does not enforce a hardware boundary.**
On Cortex-M without MPU, the SP is free to travel beyond `__stack_start`.
The linker section is a documentation and link-time budget tool only.
Real enforcement requires an MPU guard region configured in firmware —
which this project deliberately omits.

**2. Zero gap is categorically worse than a small gap.**
A 64-byte gap gives you at least one indication of where something went
wrong: a single global variable write would corrupt a visible address.
Zero gap means the first byte of stack overflow overwrites the last byte
of `.bss`, with no visible boundary in the address space.

**3. The DFS for maximum call depth must take MAX of parallel branches.**
`isr_log` calls both `format_timestamp` (88B) and `pack_record` (152B),
but not simultaneously. The worst case for `isr_log`'s subtree is
`88 + max(88, 152) = 240B`, not `88 + 88 + 152 = 328B`. Getting this
wrong produces incorrect depth estimates that either miss real bugs
(if you undercount by summing incorrectly) or generate false positives
(if you overcount by summing all branches).

**4. The difference between declared budget and real SP range.**
`_Min_Stack_Size = 512B` declares a nominal budget in the linker script.
But the SP actually starts at `_estack = 0x2001C000` and can travel
74,376 bytes down to `__bss_end__` before hitting data. The linker
section is a soft floor — not a ceiling or a hardware limit. Your
analyzer must model this distinction and report the real SP range
alongside the declared budget to give the user a complete picture.
