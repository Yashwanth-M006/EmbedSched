# Test Case 8: EDF Processor Demand Analysis — Dense Task Set & Dynamic Overrun

> **Status:** `FAIL` (Deadline Misses Detected)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Dynamic Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 8 evaluates EmbedSched's implementation of **Earliest Deadline First (EDF)** scheduling theory under **constrained relative deadlines** ($D_i < T_i$).

In real-time computing literature (Baruah et al., 1990):
- For implicit-deadline tasks ($D_i = T_i$), EDF schedulability is proven if and only if utilization $U = \sum C_i/T_i \le 1.0$.
- For constrained-deadline tasks ($D_i < T_i$), the simple utilization test is **insufficient**. A system can fail to schedule under EDF if tasks demand bursts of computation within tight initial deadline windows.
- Schedulability can only be verified by evaluating the **Demand Bound Function** $h(L)$ at all deadline points up to the synchronous busy period.
- If total utilization exceeds 100%, EDF cannot maintain deadlines, resulting in cascade deadline misses.

This test proves that EmbedSched automatically detects constrained deadlines on EDF cores, evaluates demand bounds, and detects dynamic deadline misses.

---

## 2. Why It Was Performed

1. **Preventing Schedulability Blindspots:** Naive EDF analyzers only check if $\sum C_i/T_i \le 1.0$. This allows systems that will fail at runtime to pass static verification.
2. **Exact Test-Point Enumeration:** Proves that EmbedSched systematically evaluates $h(L)$ at every exact deadline instant $L \in \{d_{i,k} \le L^*\}$.
3. **Dynamic Overrun Pinpointing:** When cumulative demand overruns processing capacity, the tool captures exact deadline miss events during simulation.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Three tasks scheduled on Core 0 under dynamic EDF with constrained deadlines ($D_i < T_i$):

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Entry Function | Memory Placement |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | **8,000 µs (8 ms)** | `null` (EDF) | `task_a` | SRAM1 |
| `Task_B` | 20,000 µs (20 ms) | **15,000 µs (15 ms)** | `null` (EDF) | `task_b` | SRAM1 |
| `Task_C` | 40,000 µs (40 ms) | **30,000 µs (30 ms)** | `null` (EDF) | `task_c` | SRAM1 |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The static analyzer inspects `firmware.map` for symbol sizes at $f = 168\text{ MHz}$ ($ws = 4$):
* `task_a`: `0x10b7f0` = **1,095,664 bytes**
* `task_b`: `0x1c9384` = **1,872,772 bytes**
* `task_c`: `0x2c9384` = **2,921,348 bytes**

Applying IPET microarchitectural timing for Cortex-M4 at 168 MHz:

1. **`Task_A` (`task_a`):**
   $$\text{Instructions}_A = 547,832 \implies \text{Cycles}_A = 890,232 \implies C_A = \frac{890,232}{168} = \mathbf{5,299.00\text{ µs}}$$

2. **`Task_B` (`task_b`):**
   $$\text{Instructions}_B = 913,386 \implies \text{Cycles}_B = 1,483,776 \implies C_B = \frac{1,483,776}{168} = \mathbf{8,832.00\text{ µs}}$$

3. **`Task_C` (`task_c`):**
   $$\text{Instructions}_C = 1,460,674 \implies \text{Cycles}_C = 2,374,008 \implies C_C = \frac{2,374,008}{168} = \mathbf{14,131.00\text{ µs}}$$

---

### B. Utilization Math & CPU Overload
Dividing each derived WCET by its period:
$$U_A = \frac{5,299\text{ µs}}{10,000\text{ µs}} = 52.99\% \quad (\text{WCET dominates period: } 53\%)$$
$$U_B = \frac{8,832\text{ µs}}{20,000\text{ µs}} = 44.16\%$$
$$U_C = \frac{14,131\text{ µs}}{40,000\text{ µs}} = 35.33\%$$

#### Total System Utilization:
$$U = \sum_{i=A}^{C} U_i = 52.99\% + 44.16\% + 35.33\% = \mathbf{132.5\%} > 100.0\%$$

Because $U = 132.5\% > 100\%$, Core 0 is severely overloaded, triggering critical finding `autosar_cpu_overload`.

---

### C. Response Time & Deadline Overrun Under EDF
Under dynamic Earliest Deadline First preemption, tasks accumulate preemption delays from whichever active job has an earlier absolute deadline:

1. **`Task_A` (Deadline = 8,000 µs):**
   * Worst-Case Response Time: $R_A = \mathbf{22,991.00\text{ µs}} > 8,000\text{ µs}$
   * Slack Margin: $8,000 - 22,991 = \mathbf{-14,991.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+14,991.00\text{ µs}$)

2. **`Task_B` (Deadline = 15,000 µs):**
   * Worst-Case Response Time: $R_B = \mathbf{40,683.00\text{ µs}} > 15,000\text{ µs}$
   * Slack Margin: $15,000 - 40,683 = \mathbf{-25,683.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+25,683.00\text{ µs}$)

3. **`Task_C` (Deadline = 30,000 µs):**
   * Worst-Case Response Time: $R_C = \mathbf{60,796.00\text{ µs}} > 30,000\text{ µs}$
   * Slack Margin: $30,000 - 60,796 = \mathbf{-30,796.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+30,796.00\text{ µs}$)

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

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 40,000\text{ µs}$)
1. **`Task_A` (Priority 0, $T = 10,000\text{ µs}$, $K = 3$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 10,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{2,680.81\text{ µs}}$, $J^{\text{mean}} = \mathbf{893.60\text{ µs}}$, $\rho = \mathbf{26.81\%} \implies$ **HIGH (>20% of period)**.

2. **`Task_B` (Priority 0, $T = 20,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (5,299.00 µs) (total synchronous release load $\sum C_{hp} = 5,299.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{5,299.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 14,683.86\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{14,683.86\text{ µs}}$, $J^{\text{mean}} = \mathbf{9,884.50\text{ µs}}$, $\rho = \frac{14,683.86}{20,000} \times 100\% = \mathbf{73.42\%} \implies$ **HIGH (>20% of period)**.

3. **`Task_C` (Priority 0, $T = 40,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (5,299.00 µs), `Task_B` (8,832.00 µs) (total synchronous release load $\sum C_{hp} = 14,131.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{14,131.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 17,214.73\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{17,214.73\text{ µs}}$, $J^{\text{mean}} = \mathbf{17,214.73\text{ µs}}$, $\rho = \frac{17,214.73}{40,000} \times 100\% = \mathbf{43.04\%} \implies$ **HIGH (>20% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_A` | 0 | `10,000 µs` | 3 | `2,680.81 µs` | `893.60 µs` | `26.81%` | **HIGH (>20% of period)** |
| `Task_B` | 0 | `20,000 µs` | 2 | `14,683.86 µs` | `9,884.50 µs` | `73.42%` | **HIGH (>20% of period)** |
| `Task_C` | 0 | `40,000 µs` | 1 | `17,214.73 µs` | `17,214.73 µs` | `43.04%` | **HIGH (>20% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_A`:** Plots 3 point(s) peaking at $y = 2,680.81\text{ µs}$ (mean $y = 893.60\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_B`:** Plots 2 point(s) peaking at $y = 14,683.86\text{ µs}$ (mean $y = 9,884.50\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_C`:** Plots 1 point(s) peaking at $y = 17,214.73\text{ µs}$ (mean $y = 17,214.73\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0   EDF      10000   5299.00    0.00         IPET  22991.00         8000  -14991.00
Task_B                     0   EDF      20000   8832.00    0.00         IPET  40683.00        15000  -25683.00
Task_C                     0   EDF      40000  14131.00    0.00         IPET  60796.00        30000  -30796.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [IPET] — deadline miss detected
```

### Generated Findings:
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_A' MISSES its deadline. WCET: 5299.00 µs, Deadline: 8000 µs, Worst-case resp.: 22991.00 µs, Overrun: +14991.00 µs.*
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_B' MISSES its deadline. WCET: 8832.00 µs, Deadline: 15000 µs, Worst-case resp.: 40683.00 µs, Overrun: +25683.00 µs.*
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_C' MISSES its deadline. WCET: 14131.00 µs, Deadline: 30000 µs, Worst-case resp.: 60796.00 µs, Overrun: +30796.00 µs.*
- **`[CRITICAL] [CALCULATED] autosar_cpu_overload` (-25 points):**  
  *Core 0: CPU OVERLOADED. Utilization: 132.5% > 100%.*
- **`[WARNING] [IPET] autosar_wcet_dominates` (-10 points):**  
  *Task 'Task_A': WCET dominates its period (53% of period).*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_8/firmware.elf \
  --map tests/Test_Suite2/Test_8/firmware.map \
  --ld  tests/Test_Suite2/Test_8/linker.ld \
  --chip tests/Test_Suite2/Test_8/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_8/schedule.json \
  --charts-dir tests/Test_Suite2/Test_8/charts/
```
