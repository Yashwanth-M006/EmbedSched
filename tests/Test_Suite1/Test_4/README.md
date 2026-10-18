# Test_4: recursive_isr (STM32F407, Cortex-M4)

## What this project tests

Your analyzer's **call graph DFS back-edge detection** — specifically,
whether it can find a recursive call chain that originates from an ISR,
passes through an intermediate dispatcher function, and eventually reaches
a function that calls itself.

This is the hardest correctness test across all seven projects because:
- The recursion is **indirect** (not ISR → ISR, but ISR → dispatch → parse → parse)
- The recursive function contains **leaf callees** that must not be false-flagged
- A **clean ISR** (`TIM2_IRQHandler`) runs in the same firmware and must not inherit the recursion finding
- An **inner loop** in `checksum_verify` compiles to `b` (branch) instructions that must not be mistaken for recursive `bl` (call) instructions

---

## The bug — exactly

```
USART1_IRQHandler           ← ISR (vector table position 53)
  └── uart_rx_dispatch      ← dispatch bridge called when END_MARKER received
        ├── checksum_verify ← LEAF (inner for-loop = 'b' not 'bl')
        └── parse_packet    ← CALLED FROM DISPATCH
              ├── emit_token    ← LEAF
              └── parse_packet  ← SELF-CALL (bl at 0x080003BC)
                    └── ...     ← UNBOUNDED DEPTH
```

`parse_packet` calls itself when it encounters `SUBPACKET_MARKER (0xBB)`
in the input stream. There is no depth limit. A crafted input with deeply
nested sub-packets exhausts the 1KB stack and causes a HardFault after
approximately 12 recursive calls.

---

## File listing

```
project3_recursive_isr/
│
├── README.md                      ← this file
├── expected_output.txt            ← test oracle: 3 must-fire, 5 must-not-fire
│
├── stm32f407_recursive.ld         ← STM32F407 linker script
│                                    _Min_Stack_Size = 0x400 (1KB, deliberately small)
│                                    Stack in SRAM1 (not CCM — secondary finding)
│                                    Explicit .stack section so _Min_Stack_Size is visible
│
├── src/
│   ├── startup.s                  ← STM32F407 vector table
│   │                                USART1_IRQHandler at position 53
│   │                                TIM2_IRQHandler at position 44
│   └── main.c                     ← Firmware with the recursive bug
│                                    TIM2_IRQHandler    → tick_update (clean)
│                                    USART1_IRQHandler  → uart_rx_dispatch
│                                                        → checksum_verify (leaf)
│                                                        → parse_packet (RECURSIVE)
│
├── build/
│   ├── firmware.elf               ← Real compiled ELF (Cortex-M4, soft-float)
│   ├── firmware.map               ← Real linker map
│   └── main.su                    ← Stack usage file (copied to su/)
│
├── su/
│   └── main.su                    ← 11 functions, all static bounds
│                                    parse_packet: 72B static (per-frame, unbounded count)
│
└── chips/
    └── stm32f407.yaml             ← F407 chip profile: no ITCM, CCM present
```

---

## The three traps that test call graph correctness

### Trap 1: `b` vs `bl` in `checksum_verify`

`checksum_verify` contains a `for` loop over a byte buffer. GCC compiles
the loop counter increment and branch as:

```asm
checksum_verify:
    ...
    adds  r3, r3, #1     ← loop increment
    b.n   <loop_top>     ← branch back to top (b instruction, NOT bl)
    ...
```

There is **no `bl` instruction** inside `checksum_verify`. The loop is pure
control flow within the function — not a call.

Your call graph regex must match only `\tbl\t` and `\tblx\t`, never `b.n`,
`bne`, `bls`, `ble`, or any other branch mnemonic.

**Verify:**
```bash
arm-none-eabi-objdump -d build/firmware.elf | \
  awk '/<checksum_verify>:/{p=1} p && /\tbl\t/{print} p && /^$/{p=0}'
# Expected: empty output
```

If this produces any output, `checksum_verify` would be misidentified as
having callees, which could corrupt the recursion analysis.

### Trap 2: `TIM2_IRQHandler` — clean ISR in the same firmware

`TIM2_IRQHandler` is a completely clean ISR:
```
TIM2_IRQHandler → tick_update (leaf, 16B frame)
```

No recursion. No cycles. Bounded depth of 24B total.

Your DFS must be **per-root**: when analyzing `TIM2_IRQHandler`'s subtree,
the visited set must be initialised fresh. If the visited set carries over
from `USART1_IRQHandler`'s analysis, `tick_update` or `TIM2_IRQHandler`
itself might be incorrectly marked as visited (or not visited), producing
false positives.

**Correct pattern:**
```python
for isr in isr_handlers:
    visited = set()           # ← fresh set for each ISR root
    depth, path, has_recursion = dfs(isr, call_graph, stack_usage, visited)
```

**Wrong pattern:**
```python
visited = set()               # ← shared across all ISRs — BUG
for isr in isr_handlers:
    depth, path, has_recursion = dfs(isr, call_graph, stack_usage, visited)
```

### Trap 3: DFS infinite loop on back-edge

If your DFS does not correctly detect the back-edge and halt, it will
recurse infinitely when it follows the `parse_packet → parse_packet` edge.
This crashes the analyzer (Python `RecursionError` or infinite loop).

**Correct termination:**
```python
def dfs(func, call_graph, stack_usage, visited):
    if func in visited:
        return (0, [func], True)  # back-edge: has_recursion=True, stop here
    visited = visited | {func}    # copy — do NOT mutate the caller's set
    own = stack_usage.get(func, 0)
    callees = call_graph.get(func, set())
    ...
```

**Wrong — mutating shared visited set:**
```python
    visited.add(func)             # mutates — all sibling branches see this
```

**Wrong — not checking before recursing:**
```python
    for callee in callees:
        dfs(callee, ...)          # will infinite-loop on parse_packet → parse_packet
```

---

## The self-call proof

The recursive `bl` instruction in the real compiled ELF:

```
parse_packet:
  08000334: ...  ← function entry
  ...
  080003bc: f7ff ffba   bl  8000334 <parse_packet>   ← SELF-CALL
  ...
```

**To verify:**
```bash
arm-none-eabi-objdump -d build/firmware.elf | grep -A1 "80003bc"
```
Expected:
```
 80003bc:  f7ff ffba   bl  8000334 <parse_packet>
```

The encoding `f7ff ffba` is a 32-bit Thumb-2 BL with a signed offset
of `-0x48` from the instruction after the BL (0x80003c0) to the function
entry (0x8000334). This is the exact instruction your call graph builder
must match and identify as a self-call.

---

## Key numbers

| Symbol | Address | Frame | Notes |
|---|---|---|---|
| `TIM2_IRQHandler` | `0x080001D0` | 8B | Clean ISR — DAG |
| `USART1_IRQHandler` | `0x080001EC` | 16B | ISR with recursive chain |
| `tick_update` | `0x08000248` | 16B | Leaf — TIM2 callee |
| `checksum_verify` | `0x08000274` | 32B | Leaf — loop uses `b` not `bl` |
| `emit_token` | `0x080002D8` | 24B | Leaf — parse_packet callee |
| `parse_packet` | `0x08000334` | 72B | **RECURSIVE** — self-call at `0x080003BC` |
| `uart_rx_dispatch` | `0x0800041C` | 24B | Bridge — calls parse_packet |
| `__stack_start` | `0x20000120` | — | SRAM1 (not CCM) |
| `__stack_end` | `0x20000520` | — | |
| `_Min_Stack_Size` | `0x400` | — | 1024 bytes |
| `__bss_end__` | `0x20000120` | — | |
| Self-call `bl` address | `0x080003BC` | — | Inside `parse_packet` |

**Stack overflow math:**
```
Depth 0: ISR(16) + dispatch(24) + parse(72) = 112B
Depth N: 112B + N × 72B
Overflow (~1024B): N = (1024 - 112) / 72 ≈ 12 calls → HardFault
```

---

## How to rebuild from source

```bash
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -ffunction-sections -fdata-sections \
  -fstack-usage -g -Wno-unused-variable \
  -c src/main.c -o build/main.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -O0 -g \
  -c src/startup.s -o build/startup.o

arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=soft \
  -nostdlib -T stm32f407_recursive.ld \
  -Wl,-Map=build/firmware.map \
  -o build/firmware.elf \
  build/startup.o build/main.o

cp build/main.su su/main.su
```

---

## How to run against your analyzer

```bash
python main.py \
  --elf     project3_recursive_isr/build/firmware.elf \
  --map     project3_recursive_isr/build/firmware.map \
  --ld      project3_recursive_isr/stm32f407_recursive.ld \
  --chip    project3_recursive_isr/chips/stm32f407.yaml \
  --su-dir  project3_recursive_isr/su \
  --startup project3_recursive_isr/src/startup.s \
  --freq-mhz 168
```

Expected score: **25/100**
Deductions: recursion (-30), isr_in_flash (-15), stack_not_in_ccm (info, -0).

---

## What you learn from this project

**1. The difference between control flow and function calls in ARM disassembly.**
`b` is a branch — it changes the PC within the same function's stack frame.
`bl` is a branch-link — it saves LR and creates a new stack frame.
Only `bl` and `blx` appear in a call graph. Every other branch mnemonic
(`b.n`, `bne`, `beq`, `bls`, `bge`, `bhi`, etc.) is control flow and must
be ignored by the call graph builder. This distinction appears in every
project but is most critical here where a false positive on `b` in
`checksum_verify` would corrupt the entire analysis.

**2. Why ISR recursion is categorically different from main-path recursion.**
In a regular function, recursion is sometimes intentional and bounded
(tree traversal, backtracking). In an ISR, the stack budget is tight
(shared with all other exception handlers and the interrupted main stack),
and there is no way to know how many times the ISR will fire before the
recursive chain unwinds. A single burst of deeply nested sub-packets in
the UART stream will HardFault the system. Severity must be CRITICAL.

**3. How to write a DFS that detects cycles without infinite-looping.**
The visited set must be a copy per branch (immutable propagation), not a
shared mutable set. If you pass `visited` by reference and add to it,
sibling branches of the call graph incorrectly see nodes from other paths
as already visited. Python's `visited | {func}` creates a new set; `.add(func)`
mutates in place. This single-character difference determines whether your
DFS is correct or subtly broken in ways that only manifest on specific
call graph topologies.
