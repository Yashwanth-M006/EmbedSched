# Test Case 2: Rate Monotonic High Load & Processor Overload Stress

> **Status:** `FAIL` (Deadline Misses & CPU Overload Detected)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 2 subjects the scheduler analysis engine to a **severe multi-task high-load workload**. In hard real-time systems literature:
- If processor utilization exceeds 100%, no priority assignment can satisfy all task deadlines without missing.
- When lower-priority tasks run with high cumulative preemption frequency, exact Response Time Analysis (RTA) must detect the exact convergence boundary or deadline overflow without hanging in infinite loops.
- Static microarchitectural IPET analysis provides cycle-exact execution bounds on multi-task firmware, enabling the tool to identify CPU overload conditions ($U > 100\%$) and pinpoint which tasks overrun their timing constraints.

---

## 2. Why It Was Performed

1. **Adversarial Stress Testing:** Validates that the tool correctly identifies unschedulable systems when cumulative task demand exceeds available core processing capacity.
2. **Exact Overrun Measurement:** Confirms that Joseph & Pandya's iterative recurrence calculates the precise worst-case response times for all tasks, quantifying the negative slack margin on failing tasks.
3. **Automated Defect Diagnostics:** Proves that EmbedSched emits actionable critical findings (`autosar_deadline_miss` and `autosar_cpu_overload`) with specific mitigation recommendations.

---

## 3. Configuration & Task Set

### Task Configuration (`schedule.json`)
Five harmonic tasks running on Core 0 under Rate Monotonic (RM) priority assignment:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Memory Placement |
|:---|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | SRAM1 |
| `Task_B` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | SRAM1 |
| `Task_C` | 40,000 µs (40 ms) | 40,000 µs (40 ms) | 3 | SRAM1 |
| `Task_D` | 80,000 µs (80 ms) | 80,000 µs (80 ms) | 4 | SRAM1 |
| `Task_E` | 160,000 µs (160 ms) | 160,000 µs (160 ms) | 5 (Lowest) | SRAM1 |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The analyzer inspects `firmware.map` to extract symbol sizes for each task in `SRAM1`:
* `task_a`: `0xb254e` = **730,446 bytes**
* `task_b`: `0x10b7f0` = **1,095,664 bytes**
* `task_c`: `0x216fd4` = **2,191,316 bytes**
* `task_d`: `0x42df9c` = **4,382,620 bytes**
* `task_e`: `0x6aff5a` = **7,012,186 bytes**

Under IPET microarchitectural timing for ARM Cortex-M4 at 168 MHz ($ws = 4$):

1. **`Task_A` (`task_a`):**
   $$\text{Instructions}_A = 365,223 \implies \text{Cycles}_A = 593,544 \implies C_A = \frac{593,544}{168} = \mathbf{3,533.00\text{ µs}}$$

2. **`Task_B` (`task_b`):**
   $$\text{Instructions}_B = 547,832 \implies \text{Cycles}_B = 890,232 \implies C_B = \frac{890,232}{168} = \mathbf{5,299.00\text{ µs}}$$

3. **`Task_C` (`task_c`):**
   $$\text{Instructions}_C = 1,095,658 \implies \text{Cycles}_C = 1,780,464 \implies C_C = \frac{1,780,464}{168} = \mathbf{10,598.00\text{ µs}}$$

4. **`Task_D` (`task_d`):**
   $$\text{Instructions}_D = 2,191,310 \implies \text{Cycles}_D = 3,560,928 \implies C_D = \frac{3,560,928}{168} = \mathbf{21,196.00\text{ µs}}$$

5. **`Task_E` (`task_e`):**
   $$\text{Instructions}_E = 3,506,093 \implies \text{Cycles}_E = 5,697,384 \implies C_E = \frac{5,697,384}{168} = \mathbf{33,913.00\text{ µs}}$$

---

### B. Utilization Math & CPU Overload Analysis

#### Individual Task Utilizations:
$$U_A = \frac{3,533\text{ µs}}{10,000\text{ µs}} = 35.33\%$$
$$U_B = \frac{5,299\text{ µs}}{20,000\text{ µs}} = 26.50\%$$
$$U_C = \frac{10,598\text{ µs}}{40,000\text{ µs}} = 26.50\%$$
$$U_D = \frac{21,196\text{ µs}}{80,000\text{ µs}} = 26.50\%$$
$$U_E = \frac{33,913\text{ µs}}{160,000\text{ µs}} = 21.20\%$$

#### Core 0 Total Utilization:
$$U = \sum_{i=A}^{E} U_i = 35.33\% + 26.50\% + 26.50\% + 26.50\% + 21.20\% = \mathbf{136.0\%} > 100.0\%$$

Since $U = 136.0\% > 100\%$, the CPU is mathematically overloaded, triggering critical finding `autosar_cpu_overload`.

---

### C. Exact Response Time Analysis (Joseph & Pandya Recurrence)

Recurrence relation: $R_i^{(k+1)} = C_i + \sum_{j \in hp(i)} \lceil R_i^{(k)}/T_j \rceil C_j$

1. **`Task_A` (Priority 1):**
   * $R_A = C_A = \mathbf{3,533.00\text{ µs}} \le 10,000\text{ µs}$
   * Slack Margin: $10,000 - 3,533 = \mathbf{+6,467.00\text{ µs}}$ (`PASS`)

2. **`Task_B` (Priority 2):**
   * $R_B^{(0)} = 5,299.00\text{ µs}$
   * $R_B^{(1)} = 5,299 + \left\lceil \frac{5,299}{10,000} \right\rceil \times 3,533 = 5,299 + 3,533 = \mathbf{8,832.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $20,000 - 8,832 = \mathbf{+11,168.00\text{ µs}}$ (`PASS`)

3. **`Task_C` (Priority 3):**
   * $R_C^{(0)} = 10,598.00\text{ µs}$
   * $R_C^{(1)} = 10,598 + \left\lceil \frac{10,598}{10,000} \right\rceil \times 3,533 + \left\lceil \frac{10,598}{20,000} \right\rceil \times 5,299 = 10,598 + 7,066 + 5,299 = 22,963.00\text{ µs}$
   * $R_C^{(2)} = 10,598 + \left\lceil \frac{22,963}{10,000} \right\rceil \times 3,533 + \left\lceil \frac{22,963}{20,000} \right\rceil \times 5,299 = 10,598 + 10,599 + 10,598 = 31,795.00\text{ µs}$
   * $R_C^{(3)} = 10,598 + \left\lceil \frac{31,795}{10,000} \right\rceil \times 3,533 + \left\lceil \frac{31,795}{20,000} \right\rceil \times 5,299 = 10,598 + 14,132 + 10,598 = \mathbf{35,328.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $40,000 - 35,328 = \mathbf{+4,672.00\text{ µs}}$ (`PASS`)

4. **`Task_D` (Priority 4):**
   * Solving recurrence under preemption from $A, B, C$:
   * Worst-Case Response Time: $R_D = \mathbf{91,852.00\text{ µs}} > 80,000\text{ µs}$
   * Slack Margin: $80,000 - 91,852 = \mathbf{-11,852.00\text{ µs}}$
   * **Verdict:** `MISS` (Deadline Overrun: $+11,852.00\text{ µs}$)

5. **`Task_E` (Priority 5):**
   * Solving recurrence under preemption from $A, B, C, D$:
   * Worst-Case Response Time: $R_E = \mathbf{169,924.00\text{ µs}} > 160,000\text{ µs}$
   * Slack Margin: $160,000 - 169,924 = \mathbf{-9,924.00\text{ µs}}$
   * **Verdict:** `MISS` (Deadline Overrun: $+9,924.00\text{ µs}$)

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0     1      10000   3533.00    0.00         IPET   3533.00        10000    6467.00
Task_B                     0     2      20000   5299.00    0.00         IPET   8832.00        20000   11168.00
Task_C                     0     3      40000  10598.00    0.00         IPET  35328.00        40000    4672.00
Task_D                     0     4      80000  21196.00    0.00         IPET  91852.00        80000  -11852.00
Task_E                     0     5     160000  33913.00    0.00         IPET 169924.00       160000   -9924.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [IPET] — deadline miss detected
```

- **Health Score:** 15 / 100
- **Detected Deductions:** `autosar_deadline_miss (-30)`, `autosar_deadline_miss (-30)`, `autosar_cpu_overload (-25)`
- **Overall Verdict:** `FAIL [IPET]`

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_2/firmware.elf \
  --map tests/Test_Suite2/Test_2/firmware.map \
  --ld  tests/Test_Suite2/Test_2/linker.ld \
  --chip tests/Test_Suite2/Test_2/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_2/schedule.json \
  --charts-dir tests/Test_Suite2/Test_2/charts/
```
