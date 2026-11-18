# Test Case 9: Pathological Hyperperiod — LCM Explosion Protection

> **Status:** `PASS` (with Hyperperiod Warning)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 9 tests **algorithmic resilience and memory safety** against non-harmonic task configurations.

In cyclic and discrete-event schedulers, the simulation timeline spans exactly one **Hyperperiod**, which is the Least Common Multiple (LCM) of all task periods:
$$\text{Hyperperiod} = \text{LCM}(T_1, T_2, \dots, T_n)$$

When periods are prime or pairwise co-prime, the hyperperiod experiences **combinatorial explosion**:
$$\text{LCM}(7, 11, 13, 17, 19)\text{ ms} = \mathbf{323,323\text{ ms}}\ (323.323\text{ seconds / 5.39 minutes})$$

Simulating 323.3 seconds of microsecond-level execution would generate over **150,000,000 event objects**, causing naive simulators to crash with out-of-memory errors or hang CI pipelines indefinitely.

This test proves that EmbedSched:
1. Detects hyperperiod explosion before allocating simulation heaps.
2. Caps the discrete-event simulation window safely at 200 ms and renders a **representative 30 ms execution window**.
3. Relies on **purely analytical Response Time Analysis (RTA)** for the schedulability verdict, which solves Joseph & Pandya's recurrence in milliseconds regardless of hyperperiod size.
4. Emits a transparent warning explaining the capped simulation window.

---

## 2. Why It Was Performed

1. **CI Pipeline Immunity:** A build tool running in automated pipelines must be completely resilient against pathological inputs. It must never freeze, hang, or consume unbounded RAM.
2. **Separating Simulation from Analytical Proof:** Proves that in EmbedSched, the schedulability verdict is **not** dependent on simulation. RTA is an analytical proof; simulation is an illustrative visual inspection tool.
3. **Graceful Degradation:** Demonstrates that the tool provides maximum possible utility (rendering the first 30 ms so developers can still inspect initial preemption dynamics) rather than crashing.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Five tasks with co-prime prime-millisecond periods:

| Task Name | Entry Function | Period ($T$) | Deadline ($D$) | Priority (RM) | Memory Placement |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_A` | `task_a` | 7,000 µs (7 ms) | 7,000 µs (7 ms) | 1 (Highest) | SRAM1 |
| `Task_B` | `task_b` | 11,000 µs (11 ms) | 11,000 µs (11 ms) | 2 | SRAM1 |
| `Task_C` | `task_c` | 13,000 µs (13 ms) | 13,000 µs (13 ms) | 3 | SRAM1 |
| `Task_D` | `task_d` | 17,000 µs (17 ms) | 17,000 µs (17 ms) | 4 | SRAM1 |
| `Task_E` | `task_e` | 19,000 µs (19 ms) | 19,000 µs (19 ms) | 5 (Lowest) | SRAM1 |

$$\text{Hyperperiod} = \text{LCM}(7, 11, 13, 17, 19) = 323,323,000\text{ µs} = 323,323\text{ ms}$$

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The static analyzer inspects `firmware.map` and disassembles task functions at $f = 168\text{ MHz}$ ($ws = 4$):
* All five task entry functions contain identical 21,708-byte machine code loops.
* Disassembled instructions: $10,854\text{ instructions}$ per task.
* Under IPET pipeline simulation:
  $$\text{Cycles} = 17,640\text{ cycles} \implies \text{WCET} = \frac{17,640}{168\text{ MHz}} = \mathbf{105.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$$
* $C_A = C_B = C_C = C_D = C_E = \mathbf{105.00\text{ µs}}$

---

### B. Utilization Math & Liu & Layland Schedulability Bound
$$U_A = \frac{105}{7,000} = 1.50\%, \quad U_B = \frac{105}{11,000} = 0.95\%, \quad U_C = \frac{105}{13,000} = 0.81\%$$
$$U_D = \frac{105}{17,000} = 0.62\%, \quad U_E = \frac{105}{19,000} = 0.55\%$$

#### Total System Utilization:
$$U = \sum_{i=A}^{E} U_i = 1.50\% + 0.95\% + 0.81\% + 0.62\% + 0.55\% = \mathbf{4.43\%} \approx \mathbf{4.4\%}$$

Comparing against the Liu & Layland bound for $n = 5$ tasks:
$$U_{\text{bound}} = 5(2^{1/5} - 1) \approx 74.35\%$$

Since $U = 4.4\% \ll 74.35\%$, schedulability is guaranteed.

---

### C. Exact Response Time Analysis (RTA) Iterations
Solving Joseph & Pandya's recurrence: $R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \lceil R_i^{(k)} / T_j \rceil C_j$

1. **`Task_A` (Priority 1):**
   * $\text{hp}(A) = \emptyset \implies R_A = C_A = \mathbf{105.00\text{ µs}}$
   * Slack Margin: $7,000 - 105 = \mathbf{+6,895.00\text{ µs}}$ (`PASS`)

2. **`Task_B` (Priority 2):**
   * $\text{hp}(B) = \{A\}$
   * $R_B^{(0)} = 105.00\text{ µs}$
   * $R_B^{(1)} = 105.00 + \left\lceil \frac{105}{7000} \right\rceil \times 105 = 105 + 105 = \mathbf{210.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $11,000 - 210 = \mathbf{+10,790.00\text{ µs}}$ (`PASS`)

3. **`Task_C` (Priority 3):**
   * $\text{hp}(C) = \{A, B\}$
   * $R_C^{(0)} = 105.00\text{ µs}$
   * $R_C^{(1)} = 105.00 + \left\lceil \frac{105}{7000} \right\rceil \times 105 + \left\lceil \frac{105}{11000} \right\rceil \times 105 = 105 + 105 + 105 = \mathbf{315.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $13,000 - 315 = \mathbf{+12,685.00\text{ µs}}$ (`PASS`)

4. **`Task_D` (Priority 4):**
   * $\text{hp}(D) = \{A, B, C\}$
   * $R_D = 105.00 + 3 \times 105.00 = \mathbf{420.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $17,000 - 420 = \mathbf{+16,580.00\text{ µs}}$ (`PASS`)

5. **`Task_E` (Priority 5):**
   * $\text{hp}(E) = \{A, B, C, D\}$
   * $R_E = 105.00 + 4 \times 105.00 = \mathbf{525.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $19,000 - 525 = \mathbf{+18,475.00\text{ µs}}$ (`PASS`)

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0     1       7000    105.00    0.00         IPET    105.00         7000    6895.00
Task_B                     0     2      11000    105.00    0.00         IPET    210.00        11000   10790.00
Task_C                     0     3      13000    105.00    0.00         IPET    315.00        13000   12685.00
Task_D                     0     4      17000    105.00    0.00         IPET    420.00        17000   16580.00
Task_E                     0     5      19000    105.00    0.00         IPET    525.00        19000   18475.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

- **Health Score:** 100 / 100
- **Overall Verdict:** `PASS [IPET]`

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_9/firmware.elf \
  --map tests/Test_Suite2/Test_9/firmware.map \
  --ld  tests/Test_Suite2/Test_9/linker.ld \
  --chip tests/Test_Suite2/Test_9/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_9/schedule.json \
  --charts-dir tests/Test_Suite2/Test_9/charts/
```
