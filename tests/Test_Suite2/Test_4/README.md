# Test Case 4: Priority Inversion via Resource Sharing — PCP Blocking

> **Status:** `FAIL` (Deadline Miss Detected)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic with Priority Ceiling Protocol (PCP/SRP)

---

## 1. What This Test Signifies

Test Case 4 evaluates the tool's implementation of **shared resource synchronization and priority inversion bounding** under heavy workload.

When tasks share mutual exclusion locks (mutexes), a lower-priority task holding a lock can temporarily block a higher-priority task. Without synchronization protocols, unbounded priority inversion occurs (as famously seen on the Mars Pathfinder spacecraft in 1997).

This test validates that EmbedSched:
1. Parses AUTOSAR shared resource declarations (`resources` in `schedule.json`).
2. Computes the **Priority Ceiling** of each resource ($Ceiling = \min_{t} Prio(t)$).
3. Correctly calculates the worst-case **blocking term ($B_i$)** using Sha, Rajkumar, & Lehoczky's Priority Ceiling Protocol (PCP).
4. Demonstrates that under PCP/SRP, blocking is strictly bounded to at most a single critical section ($B_i = \max CS$), rather than the naive sum of all lower-priority critical sections.
5. Accurately flags deadline misses and core overload when preemption and blocking push worst-case response times past deadlines.

---

## 2. Why It Was Performed

1. **Protocol Rigor:** Many commercial schedulability calculators either ignore mutex blocking entirely (producing unsafely optimistic response times) or naively sum critical sections.
2. **AUTOSAR OS Compliance:** AUTOSAR OS and OSEK VDMS mandate the Priority Ceiling Protocol / Stack Resource Policy (SRP) for internal resources.
3. **Traceable Blocking Terms:** Engineers need to see exactly *which* lower-priority task and *which* mutex caused blocking in the RTA table.

---

## 3. Configuration & Task Set

### Resource Definitions (`schedule.json`)
```json
"resources": [
  {
    "name": "mutex_spi",
    "type": "mutex",
    "accessed_by": ["Task_H", "Task_L"],
    "max_critical_section_ms": 3.0
  },
  {
    "name": "mutex_i2c",
    "type": "mutex",
    "accessed_by": ["Task_M", "Task_L"],
    "max_critical_section_ms": 4.5
  }
]
```

#### Computed Priority Ceilings:
- **`mutex_spi`**: Accessed by `Task_H` (Prio 1) and `Task_L` (Prio 3) $\implies \mathbf{Ceiling = 1}$.
- **`mutex_i2c`**: Accessed by `Task_M` (Prio 2) and `Task_L` (Prio 3) $\implies \mathbf{Ceiling = 2}$.

### Task Configuration (`schedule.json`)
Three tasks on Core 0:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Entry Function | Resources Accessed | Max Critical Section |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `Task_H` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | `task_h` | `mutex_spi` | 1.0 ms |
| `Task_M` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | `task_m` | `mutex_i2c` | 2.0 ms |
| `Task_L` | 40,000 µs (40 ms) | 40,000 µs (40 ms) | 3 (Lowest) | `task_l` | `mutex_spi`, `mutex_i2c` | 4.5 ms |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The analyzer extracts symbol sizes from `firmware.map`:
* `task_h`: `0x10b7f0` = **1,095,664 bytes**
* `task_m`: `0xb254e` = **730,446 bytes**
* `task_l`: `0x2c9384` = **2,921,348 bytes**

Applying IPET microarchitectural timing for Cortex-M4 at 168 MHz ($ws = 4$):

1. **`Task_H` (`task_h`):**
   $$\text{Instructions}_H = 547,832 \implies \text{Cycles}_H = 890,232 \implies C_H = \frac{890,232}{168} = \mathbf{5,299.00\text{ µs}}$$

2. **`Task_M` (`task_m`):**
   $$\text{Instructions}_M = 365,223 \implies \text{Cycles}_M = 593,544 \implies C_M = \frac{593,544}{168} = \mathbf{3,533.00\text{ µs}}$$

3. **`Task_L` (`task_l`):**
   $$\text{Instructions}_L = 1,460,674 \implies \text{Cycles}_L = 2,374,008 \implies C_L = \frac{2,374,008}{168} = \mathbf{14,131.00\text{ µs}}$$

---

### B. Priority Ceiling Protocol (PCP) Blocking Terms ($B_i$)
Under PCP, a task $\tau_i$ can be blocked by at most one critical section belonging to any lower-priority task holding a mutex whose priority ceiling is greater than or equal to $Prio(\tau_i)$:
$$B_i = \max_{j \in \text{lp}(i)} \max_{R \in \text{Res}(j), \text{Ceiling}(R) \le Prio(i)} CS(j, R)$$

1. **Blocking for `Task_H` ($\tau_H$, $Prio = 1$):**
   * Lower-priority tasks: $\text{lp}(\tau_H) = \{\tau_M, \tau_L\}$
   * Mutexes with $\text{Ceiling} \le 1$: `mutex_spi` ($R_{\text{spi}}$, $\text{Ceiling} = 1$).
   * Blocking duration:
     $$B_H = CS(\tau_L, R_{\text{spi}}) = \mathbf{3,000.00\text{ µs}}$$

2. **Blocking for `Task_M` ($\tau_M$, $Prio = 2$):**
   * Lower-priority tasks: $\text{lp}(\tau_M) = \{\tau_L\}$
   * Mutexes with $\text{Ceiling} \le 2$: `mutex_spi` ($R_{\text{spi}}$) and `mutex_i2c` ($R_{\text{i2c}}$).
   * Blocking duration:
     $$B_M = \max\left(CS(\tau_L, R_{\text{spi}}),\, CS(\tau_L, R_{\text{i2c}})\right) = \max(3.0\text{ ms}, 4.5\text{ ms}) = \mathbf{4,500.00\text{ µs}}$$

3. **Blocking for `Task_L` ($\tau_L$, $Prio = 3$, Lowest):**
   * Lower-priority tasks: $\text{lp}(\tau_L) = \emptyset$
   * Blocking duration:
     $$B_L = \mathbf{0.00\text{ µs}}$$

---

### C. Extended Response Time Analysis with Blocking
Extended RTA recurrence:
$$R_i^{(0)} = C_i + B_i$$
$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### Task H (Priority 1, $T_H = 10,000\text{ µs}, D_H = 10,000\text{ µs}$):
* $\text{hp}(\tau_H) = \emptyset$
* $R_H = C_H + B_H = 5,299.00 + 3,000.00 = \mathbf{8,299.00\text{ µs}} \le 10,000\text{ µs}$
* **Slack Margin:** $10,000 - 8,299 = \mathbf{+1,701.00\text{ µs}}$ (`PASS`)

#### Task M (Priority 2, $T_M = 20,000\text{ µs}, D_M = 20,000\text{ µs}$):
* $\text{hp}(\tau_M) = \{\tau_H\}$
* $R_M^{(0)} = C_M + B_M = 3,533.00 + 4,500.00 = 8,033.00\text{ µs}$
* $R_M^{(1)} = 3,533 + 4,500 + \left\lceil \frac{8,033}{10,000} \right\rceil \times 5,299 = 8,033 + 5,299 = 13,332.00\text{ µs}$
* $R_M^{(2)} = 3,533 + 4,500 + \left\lceil \frac{13,332}{10,000} \right\rceil \times 5,299 = 8,033 + (2 \times 5,299) = 18,631.00\text{ µs}$
* $R_M^{(3)} = 3,533 + 4,500 + \left\lceil \frac{18,631}{10,000} \right\rceil \times 5,299 = 8,033 + (2 \times 5,299) = \mathbf{18,631.00\text{ µs}}\quad (\text{Converged})$
* **Slack Margin:** $20,000 - 18,631 = \mathbf{+1,369.00\text{ µs}}$ (`PASS`)

#### Task L (Priority 3, $T_L = 40,000\text{ µs}, D_L = 40,000\text{ µs}$):
* $\text{hp}(\tau_L) = \{\tau_H, \tau_M\}$
* Preempted by higher-priority tasks $\tau_H$ and $\tau_M$:
* RTA converges at $R_L = \mathbf{42,393.00\text{ µs}} > 40,000\text{ µs}$
* **Slack Margin:** $40,000 - 42,393 = \mathbf{-2,393.00\text{ µs}}$
* **Verdict:** `MISS` (Deadline Overrun: $+2,393.00\text{ µs}$)

---

### D. Utilization Math
$$U_H = \frac{5,299}{10,000} = 52.99\%, \quad U_M = \frac{3,533}{20,000} = 17.67\%, \quad U_L = \frac{14,131}{40,000} = 35.33\%$$
$$U_{\text{total}} = 52.99\% + 17.67\% + 35.33\% = \mathbf{106.0\%} > 100\%$$
Triggering `autosar_cpu_overload` finding.

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
1. **`Task_H` (Priority 1, $T = 10,000\text{ µs}$, $K = 4$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 10,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_M` (Priority 2, $T = 20,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_H` (5,299.00 µs) (total synchronous release load $\sum C_{hp} = 5,299.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{5,299.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 5,299.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{5,299.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{5,299.00\text{ µs}}$, $\rho = \frac{5,299.00}{20,000} \times 100\% = \mathbf{26.50\%} \implies$ **HIGH (>20% of period)**.

3. **`Task_L` (Priority 3, $T = 40,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_H` (5,299.00 µs), `Task_M` (3,533.00 µs) (total synchronous release load $\sum C_{hp} = 8,832.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{8,832.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 8,832.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{8,832.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{8,832.00\text{ µs}}$, $\rho = \frac{8,832.00}{40,000} \times 100\% = \mathbf{22.08\%} \implies$ **HIGH (>20% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_H` | 1 | `10,000 µs` | 4 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_M` | 2 | `20,000 µs` | 2 | `5,299.00 µs` | `5,299.00 µs` | `26.50%` | **HIGH (>20% of period)** |
| `Task_L` | 3 | `40,000 µs` | 1 | `8,832.00 µs` | `8,832.00 µs` | `22.08%` | **HIGH (>20% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_H`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 4 activation(s), visually proving zero start-time preemption.
  - **`Task_M`:** Plots 2 point(s) peaking at $y = 5,299.00\text{ µs}$ (mean $y = 5,299.00\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_L`:** Plots 1 point(s) peaking at $y = 8,832.00\text{ µs}$ (mean $y = 8,832.00\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_H                     0     1      10000   5299.00 3000.00         IPET   8299.00        10000    1701.00
Task_M                     0     2      20000   3533.00 4500.00         IPET  18631.00        20000    1369.00
Task_L                     0     3      40000  14131.00    0.00         IPET  42393.00        40000   -2393.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [IPET] — deadline miss detected
```

### Generated Findings:
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_L' MISSES its deadline. Function: task_l, WCET: 14131.00 µs [IPET], Deadline: 40000 µs, Worst-case resp.: 42393.00 µs, Overrun: +2393.00 µs.*
- **`[CRITICAL] [CALCULATED] autosar_cpu_overload` (-25 points):**  
  *Core 0: CPU OVERLOADED. Utilization: 106.0% > 100%.*
- **`[WARNING] [IPET] autosar_wcet_dominates` (-10 points):**  
  *Task 'Task_H': WCET dominates its period (53% of period).*
- **`[INFO] autosar_pcp_blocking`:**  
  *Task_H blocked by Task_L on mutex_spi for up to 3ms [CALCULATED] (PCP)*
- **`[INFO] autosar_pcp_blocking`:**  
  *Task_M blocked by Task_L on mutex_i2c for up to 4.5ms [CALCULATED] (PCP)*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_4/firmware.elf \
  --map tests/Test_Suite2/Test_4/firmware.map \
  --ld  tests/Test_Suite2/Test_4/linker.ld \
  --chip tests/Test_Suite2/Test_4/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_4/schedule.json \
  --charts-dir tests/Test_Suite2/Test_4/charts/
```
