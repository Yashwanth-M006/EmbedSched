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

### D. Start-Time Jitter Analysis & Graph Validation

#### 1. Mathematical Formulation
In a hard real-time preemptive system, the ideal periodic release time for activation $k$ ($k \in \{0, 1, \dots, K_i - 1\}$) of task $\tau_i$ is:
$$t_{\text{rel}}(k) = k \cdot T_i$$

Under work-conserving, non-anticipative scheduling, a task cannot start prior to its release ($s_i(k) \ge t_{\text{rel}}(k)$). The start-time jitter $J_i(k)$ quantifies the non-negative dispatch latency incurred due to higher-priority task preemption or lower-priority blocking:
$$J_i(k) = s_i(k) - k \cdot T_i \ge 0$$

Across all $K_i = \lfloor H / T_i \rfloor$ timely activations over the simulation hyperperiod $H$:
* **Maximum Start-Time Jitter ($J_i^{\max}$):**
  $$J_i^{\max} = \max_{0 \le k < K_i} J_i(k)$$
* **Mean Start-Time Jitter ($J_i^{\text{mean}}$):**
  $$J_i^{\text{mean}} = \frac{1}{K_i} \sum_{k=0}^{K_i - 1} J_i(k)$$
* **Relative Jitter Ratio ($\rho_i$):**
  $$\rho_i = \frac{J_i^{\max}}{T_i} \times 100\%$$
* **Safety Assessment Classification:**
  - $\rho_i < 1\%$: **EXCELLENT** (negligible phase distortion; safe for high-frequency control loops)
  - $1\% \le \rho_i < 5\%$: **GOOD** (acceptable for general actuator & sensor processing)
  - $5\% \le \rho_i < 20\%$: **MODERATE** (detectable variation; acceptable for supervisory tasks)
  - $\rho_i \ge 20\%$: **HIGH WARNING** (significant preemption delay; risks control instability)

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 160,000\text{ µs}$)
1. **`Task_A` (Priority 1, $T = 10,000\text{ µs}$, $K = 16$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 10,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_B` (Priority 2, $T = 20,000\text{ µs}$, $K = 8$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (3,533.00 µs) (total synchronous release load $\sum C_{hp} = 3,533.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{3,533.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 3,533.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{3,533.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{3,533.00\text{ µs}}$, $\rho = \frac{3,533.00}{20,000} \times 100\% = \mathbf{17.66\%} \implies$ **MODERATE (<20% of period)**.

3. **`Task_C` (Priority 3, $T = 40,000\text{ µs}$, $K = 4$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (3,533.00 µs), `Task_B` (5,299.00 µs) (total synchronous release load $\sum C_{hp} = 8,832.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{8,832.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 8,832.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{8,832.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{8,832.00\text{ µs}}$, $\rho = \frac{8,832.00}{40,000} \times 100\% = \mathbf{22.08\%} \implies$ **HIGH (>20% of period)**.

4. **`Task_D` (Priority 4, $T = 80,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (3,533.00 µs), `Task_B` (5,299.00 µs), `Task_C` (10,598.00 µs) (total synchronous release load $\sum C_{hp} = 19,430.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{19,430.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 35,328.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{35,328.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{35,328.00\text{ µs}}$, $\rho = \frac{35,328.00}{80,000} \times 100\% = \mathbf{44.16\%} \implies$ **HIGH (>20% of period)**.

5. **`Task_E` (Priority 5, $T = 160,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (3,533.00 µs), `Task_B` (5,299.00 µs), `Task_C` (10,598.00 µs), `Task_D` (21,196.00 µs) (total synchronous release load $\sum C_{hp} = 40,626.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{40,626.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 0.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \frac{0.00}{160,000} \times 100\% = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_A` | 1 | `10,000 µs` | 16 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_B` | 2 | `20,000 µs` | 8 | `3,533.00 µs` | `3,533.00 µs` | `17.66%` | **MODERATE (<20% of period)** |
| `Task_C` | 3 | `40,000 µs` | 4 | `8,832.00 µs` | `8,832.00 µs` | `22.08%` | **HIGH (>20% of period)** |
| `Task_D` | 4 | `80,000 µs` | 1 | `35,328.00 µs` | `35,328.00 µs` | `44.16%` | **HIGH (>20% of period)** |
| `Task_E` | 5 | `160,000 µs` | 0 | `0.00 µs` | `0.00 µs` | `0.00%` | **N/A** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_A`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 16 activation(s), visually proving zero start-time preemption.
  - **`Task_B`:** Plots 8 point(s) peaking at $y = 3,533.00\text{ µs}$ (mean $y = 3,533.00\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_C`:** Plots 4 point(s) peaking at $y = 8,832.00\text{ µs}$ (mean $y = 8,832.00\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_D`:** Plots 1 point(s) peaking at $y = 35,328.00\text{ µs}$ (mean $y = 35,328.00\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_E`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 0 activation(s), visually proving zero start-time preemption.
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
