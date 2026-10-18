# Test_2: golden_baseline

## What this project tests

Your analyzer's **false-positive rate**. Every design decision in
this firmware is correct. The tool must produce zero critical findings,
zero warnings, and zero spurious flags.

This is harder to build than a bug-riddled project. To correctly
pass this test, your rules must be:

- **Chip-aware** — must not recommend ITCM on a chip that has none
- **Threshold-aware** — must not flag 7% stack usage as overflow risk
- **Alignment-aware** — must not flag a 32-byte aligned buffer as misaligned
- **Instruction-aware** — must distinguish `bl` (function call) from `b` (branch)
- **Region-aware** — must not flag CCM-based stack as a DMA bus contention risk

**If any WARNING or CRITICAL fires against this project, you have a bug.**

---

## What "golden" means — the correct patterns

| Pattern | Where | Why correct |
|---|---|---|
| `_Min_Stack_Size = 0x800` | `golden.ld` | Explicit, verifiable, 2KB |
| `.stack` section in CCM | `golden.ld` | Zero wait state, CPU-only, no DMA contention |
| `__stack_start` / `__stack_end` exported | `.map` | Runtime overflow detection possible |
| DMA buffers in `.dma_buffers` section | `golden.ld` | Named, separate, tool-identifiable |
| `.dma_buffers` in SRAM1 | `golden.ld` | DMA-accessible via AHB |
| `aligned(32)` on DMA buffers | `main.c` | D-cache line boundary |
| ISRs are short and non-blocking | `main.c` | No HAL calls, no busy-wait |
| No recursion anywhere | `main.c` | Strict DAG, bounded stack depth |
| Worst-case stack depth 144B vs 2048B budget | `.su` | 7.0% — far below 80% threshold |

---

## File listing

```
project1_golden_baseline/
│
├── README.md                   ← this file
├── expected_output.txt         ← test oracle: 8 must-not-fire, 4 must-fire
│
├── golden.ld                   ← THE KEY FILE: every correct linker pattern
│                                 Read the comments inside — each section
│                                 explains WHY it's done this way.
│
├── src/
│   ├── startup.s               ← STM32F407 vector table, CCM-based _estack
│   └── main.c                  ← Bare-metal firmware, all rules satisfied
│                                 Three ISR handlers (clean, non-blocking)
│                                 DMA buffers with aligned(32)
│                                 Call graph: strict DAG, no recursion
│
├── build/
│   ├── firmware.elf            ← Real compiled ELF
│   ├── firmware.map            ← Real linker map
│   └── main.su                 ← Stack usage (copied to su/ as well)
│
├── su/
│   └── main.su                 ← 12 functions, all static bounds
│
└── chips/
    └── stm32f407.yaml          ← F407 profile: no ITCM, CCM present
```

---

## The key numbers

| Symbol / Metric | Value | Where |
|---|---|---|
| `_Min_Stack_Size` | `0x800` (2048 bytes) | `golden.ld` |
| `__stack_start` | `0x10000000` (CCM base) | `firmware.map` |
| `__stack_end` | `0x10000800` | `firmware.map` |
| `_estack` | `0x10010000` (CCM top) | `firmware.map` |
| `__dma_buffers_start` | `0x20000040` | `firmware.map` |
| `0x20000040 % 32` | `0` (aligned) | Python verify |
| Worst-case stack depth | `144 bytes` | `.su` + call graph |
| Stack budget usage | `7.0%` | `144 / 2048` |
| ISR handlers | 3 (all clean, non-blocking) | `startup.s` + `main.c` |
| Recursion detected | None | `objdump` call graph |

---

## How to rebuild from source

```bash
# Compile
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -ffunction-sections -fdata-sections \
  -fstack-usage -g -Wno-unused-variable \
  -c src/main.c -o build/main.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -g \
  -c src/startup.s -o build/startup.o

# Link
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -nostdlib -T golden.ld \
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
  --elf    project1_golden_baseline/build/firmware.elf \
  --map    project1_golden_baseline/build/firmware.map \
  --ld     project1_golden_baseline/golden.ld \
  --chip   project1_golden_baseline/chips/stm32f407.yaml \
  --su-dir project1_golden_baseline/su \
  --startup project1_golden_baseline/src/startup.s \
  --freq-mhz 168
```

Expected score: **100/100**. No deductions.

---

## The critical distinction: `b` vs `bl` in `crc_compute`

`crc_compute` has a nested loop that looks, superficially, like it could
be detected as recursion by a naive call graph builder. It is not.

The inner loop compiles to:

```asm
crc_compute:
  ...
  b.n   <loop_top>     ← branch (b) — NOT a function call
  ...
```

A `b` or `b.n` instruction is a branch within the same function.
A `bl` or `blx` instruction is a function call that updates LR.

Your call graph builder in `elf_parser.py` / `call_graph.py` must
**only** follow `bl` and `blx` instructions, not `b` or `bne` or
any other branch. If it follows `b` instructions, it will:

1. Falsely detect `crc_compute` as recursive (back-edge in the loop)
2. Fire a spurious `recursion_detected` CRITICAL finding
3. Fail this test

Verify your implementation:

```bash
arm-none-eabi-objdump -d build/firmware.elf | \
  awk '/<crc_compute>:/{p=1} p && /bl /{print} p && /^$/{p=0}'
# Expected output: empty (no bl instructions inside crc_compute)
```

---

## What you learn from this project

1. **How to write a correctly false-positive-free rule engine.**
   Rules that fire on everything are useless. A rule must be constrained
   by chip profile, address range, and threshold — not just pattern match.

2. **The difference between branch and call in ARM disassembly.**
   `b`/`bne`/`beq` = control flow within a function.
   `bl`/`blx` = function call. Your call graph must only use the latter.

3. **Why CCM is the correct stack location on STM32F407.**
   Not SRAM1 (DMA bus), not SRAM2 (same AHB port as SRAM1). CCM is the
   only CPU-only zero-wait-state region on F407 — the M4 equivalent of
   DTCM on Cortex-M7 parts.

4. **Why 32-byte DMA buffer alignment matters even on chips without D-cache.**
   The F407 has no D-cache, so `SCB_CleanDCache` is a no-op. But writing
   `aligned(32)` now makes the firmware portable to F7/H7 without a
   silent cache-corruption bug appearing on porting.
