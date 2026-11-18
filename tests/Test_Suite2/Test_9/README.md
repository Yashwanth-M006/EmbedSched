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

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = Hyperperiod$)
1. **`Task_A` (Priority 1, $T = 7,000\text{ µs}$, $K = 5$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 7,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_B` (Priority 2, $T = 11,000\text{ µs}$, $K = 3$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (105.00 µs) (total synchronous release load $\sum C_{hp} = 105.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{105.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 95.36\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{95.36\text{ µs}}$, $J^{\text{mean}} = \mathbf{31.79\text{ µs}}$, $\rho = \frac{95.36}{11,000} \times 100\% = \mathbf{0.87\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_C` (Priority 3, $T = 13,000\text{ µs}$, $K = 3$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (105.00 µs), `Task_B` (105.00 µs) (total synchronous release load $\sum C_{hp} = 210.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{210.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 194.80\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{194.80\text{ µs}}$, $J^{\text{mean}} = \mathbf{64.93\text{ µs}}$, $\rho = \frac{194.80}{13,000} \times 100\% = \mathbf{1.50\%} \implies$ **GOOD (<5% of period)**.

4. **`Task_D` (Priority 4, $T = 17,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (105.00 µs), `Task_B` (105.00 µs), `Task_C` (105.00 µs) (total synchronous release load $\sum C_{hp} = 315.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{315.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 294.13\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{294.13\text{ µs}}$, $J^{\text{mean}} = \mathbf{147.06\text{ µs}}$, $\rho = \frac{294.13}{17,000} \times 100\% = \mathbf{1.73\%} \implies$ **GOOD (<5% of period)**.

5. **`Task_E` (Priority 5, $T = 19,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (105.00 µs), `Task_B` (105.00 µs), `Task_C` (105.00 µs), `Task_D` (105.00 µs) (total synchronous release load $\sum C_{hp} = 420.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{420.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 394.06\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{394.06\text{ µs}}$, $J^{\text{mean}} = \mathbf{197.03\text{ µs}}$, $\rho = \frac{394.06}{19,000} \times 100\% = \mathbf{2.07\%} \implies$ **GOOD (<5% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_A` | 1 | `7,000 µs` | 5 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_B` | 2 | `11,000 µs` | 3 | `95.36 µs` | `31.79 µs` | `0.87%` | **EXCELLENT (<1% of period)** |
| `Task_C` | 3 | `13,000 µs` | 3 | `194.80 µs` | `64.93 µs` | `1.50%` | **GOOD (<5% of period)** |
| `Task_D` | 4 | `17,000 µs` | 2 | `294.13 µs` | `147.06 µs` | `1.73%` | **GOOD (<5% of period)** |
| `Task_E` | 5 | `19,000 µs` | 2 | `394.06 µs` | `197.03 µs` | `2.07%` | **GOOD (<5% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_A`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 5 activation(s), visually proving zero start-time preemption.
  - **`Task_B`:** Plots 3 point(s) peaking at $y = 95.36\text{ µs}$ (mean $y = 31.79\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_C`:** Plots 3 point(s) peaking at $y = 194.80\text{ µs}$ (mean $y = 64.93\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_D`:** Plots 2 point(s) peaking at $y = 294.13\text{ µs}$ (mean $y = 147.06\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_E`:** Plots 2 point(s) peaking at $y = 394.06\text{ µs}$ (mean $y = 197.03\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
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
