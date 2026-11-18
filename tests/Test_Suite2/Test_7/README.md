# Test Case 7: Stack Overflow Under Preemption — Cross-Domain Analysis

> **Status:** `WARNING` (Concurrent Stack Overflow Risk)  
> **Confidence:** `[IPET]` / `[STATIC]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 7 demonstrates a critical capability of EmbedSched: **cross-domain synthesis** between **static memory/stack analysis** and **runtime preemption scheduling**.

In embedded systems with a shared execution stack (standard in RTOS ISR handling, bare-metal loops, or OSEK Basic Tasks BCC1 sharing an execution stack):
- Looking at each task's stack usage individually indicates that all tasks fit comfortably within the declared stack size.
- However, when scheduled under preemptive priority, **higher-priority tasks preempt lower-priority tasks at their deepest call frames**, causing their activation records to co-exist simultaneously in physical memory.

Test Case 7 proves that EmbedSched calculates the cumulative concurrent stack pressure across the preemption chain and flags potential stack overflows that neither a pure static stack analyzer nor a pure RTOS timing tool could detect alone.

---

## 2. Why It Was Performed

1. **The Most Feared Silent Embedded Bug:** Stack overflow into adjacent `.bss` or data structures causes non-deterministic system resets, memory corruption, and erratic behavior that is nearly impossible to reproduce in a lab.
2. **Exposing Single-Task Stack Fallacies:** A compiler tool that only reports individual task stack depths (e.g. GCC `-fstack-usage` reporting `max = 1808B`) provides a false sense of security when the declared stack is 4096B.
3. **Automated Linker Validation:** Cross-references the calculated concurrent stack pressure against `_Min_Stack_Size` parsed from `linker.ld`.

---

## 3. Configuration & Task Set

### Linker Script Configuration (`linker.ld`)
- **Declared Stack Size:** `_Min_Stack_Size = 0x1000` (4,096 bytes)
- **Stack Section Placement:** Placed in zero-wait-state DTCM (`0x10000000`).

### Tasks & Individual Stack Frame Allocations (`main.c`):

| Task Name | Entry Function | Priority | Period ($T$) | Buffer Allocation | Total Stack Frame (with ABI Alignment) |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_MotorControl` | `motor_control_loop` | 1 (Highest) | 1,000 µs (1 ms) | `volatile char buf[1800]` | **1,808 bytes** |
| `Task_SensorAgg` | `sensor_aggregate` | 2 | 20,000 µs (20 ms) | `volatile char buf[1400]` | **1,408 bytes** |
| `Task_CANTransmit` | `can_transmit_handler` | 3 (Lowest) | 100,000 µs (100 ms) | `volatile char buf[900]` | **912 bytes** |

---

## 4. Step-by-Step Mathematical Calculations

### A. Static Stack Analysis & Concurrent Preemption Chain

#### 1. Individual Task Frame Analysis:
Under ARM AAPCS (ARM Architecture Procedure Call Standard), stack frames must be 8-byte aligned at public interfaces, and compiler prologue instructions (`push {r4, lr}`) reserve frame space:
- `can_transmit_handler`: $900\text{ bytes (buf)} + 12\text{ bytes (frame/alignment)} = 912\text{ bytes}$
- `sensor_aggregate`: $1,400\text{ bytes (buf)} + 8\text{ bytes (frame/alignment)} = 1,408\text{ bytes}$
- `motor_control_loop`: $1,800\text{ bytes (buf)} + 8\text{ bytes (frame/alignment)} = 1,808\text{ bytes}$

Each individual task comfortably fits within the 4,096-byte stack limit:
- $\Delta_{\text{CAN}} = 4,096 - 912 = +3,184\text{ bytes free}$
- $\Delta_{\text{Sensor}} = 4,096 - 1,408 = +2,688\text{ bytes free}$
- $\Delta_{\text{Motor}} = 4,096 - 1,808 = +2,288\text{ bytes free}$

#### 2. Worst-Case Preemption Chain Math:
Because the tasks are scheduled under preemptive Rate Monotonic priority ($P_{\text{Motor}} > P_{\text{Sensor}} > P_{\text{CAN}}$):
1. Lowest-priority `Task_CANTransmit` is active at its deepest frame $\implies 912\text{ bytes}$ on stack.
2. `Task_SensorAgg` releases and preempts `Task_CANTransmit` $\implies 912 + 1,408 = 2,320\text{ bytes}$.
3. Highest-priority `Task_MotorControl` releases and preempts `Task_SensorAgg` $\implies 2,320 + 1,808 = 4,128\text{ bytes}$.

$$\text{Stack}_{\text{concurrent}} = \sum_{i=1}^{3} \text{Stack}(\tau_i) = 912 + 1,408 + 1,808 = \mathbf{4,128\text{ bytes}}$$

#### 3. Stack Overflow Margin Evaluation:
$$\text{Margin}_{\text{stack}} = \text{\_Min\_Stack\_Size} - \text{Stack}_{\text{concurrent}} = 4,096\text{ B} - 4,128\text{ B} = \mathbf{-32\text{ bytes}}$$

The concurrent worst-case stack depth **exceeds declared stack capacity by 32 bytes**. Under worst-case scheduling alignment, the stack pointer decrements below the DTCM stack boundary, corrupting adjacent memory. The analyzer flags warning `autosar_concurrent_stack` (-20 points deduction).

---

### B. Timing & Schedulability Verification (IPET)
In parallel with stack analysis, the tool verifies task execution timing from the binary via IPET at $168\text{ MHz}$:
- `motor_control_loop`: $\text{WCET} = \mathbf{142.00\text{ µs}}$ ($T = 1,000\text{ µs}, U = 14.20\%$)
- `sensor_aggregate`: $\text{WCET} = \mathbf{71.00\text{ µs}}$ ($T = 20,000\text{ µs}, U = 0.355\%$)
- `can_transmit_handler`: $\text{WCET} = \mathbf{36.00\text{ µs}}$ ($T = 100,000\text{ µs}, U = 0.036\%$)

Total system utilization:
$$U = 14.20\% + 0.355\% + 0.036\% = \mathbf{14.6\%} \ll U_{\text{bound}} = 78.0\%$$

RTA recurrence:
- $R_{\text{Motor}} = \mathbf{142.00\text{ µs}} \le 1,000\text{ µs}$ (`PASS`, margin $+858.00\text{ µs}$)
- $R_{\text{Sensor}} = 71.00 + \lceil 71/1000 \rceil \times 142.00 = \mathbf{213.00\text{ µs}} \le 20,000\text{ µs}$ (`PASS`, margin $+19,787.00\text{ µs}$)
- $R_{\text{CAN}} = 36.00 + \lceil 36/1000 \rceil \times 142.00 + \lceil 36/20000 \rceil \times 71.00 = \mathbf{249.00\text{ µs}} \le 100,000\text{ µs}$ (`PASS`, margin $+99,751.00\text{ µs}$)

**Engineering Takeaway:** All tasks meet their real-time timing deadlines with massive margins (Score: 80/100), yet the firmware will fail in production due to concurrent stack overflow. Only a unified timing and memory analyzer can detect this.

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

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 100,000\text{ µs}$)
1. **`Task_MotorControl` (Priority 1, $T = 1,000\text{ µs}$, $K = 100$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 1,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_SensorAgg` (Priority 2, $T = 20,000\text{ µs}$, $K = 5$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (142.00 µs) (total synchronous release load $\sum C_{hp} = 142.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{142.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 138.62\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{138.62\text{ µs}}$, $J^{\text{mean}} = \mathbf{129.85\text{ µs}}$, $\rho = \frac{138.62}{20,000} \times 100\% = \mathbf{0.69\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_CANTransmit` (Priority 3, $T = 100,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (142.00 µs), `Task_SensorAgg` (71.00 µs) (total synchronous release load $\sum C_{hp} = 213.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{213.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 193.30\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{193.30\text{ µs}}$, $J^{\text{mean}} = \mathbf{193.30\text{ µs}}$, $\rho = \frac{193.30}{100,000} \times 100\% = \mathbf{0.19\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_MotorControl` | 1 | `1,000 µs` | 100 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_SensorAgg` | 2 | `20,000 µs` | 5 | `138.62 µs` | `129.85 µs` | `0.69%` | **EXCELLENT (<1% of period)** |
| `Task_CANTransmit` | 3 | `100,000 µs` | 1 | `193.30 µs` | `193.30 µs` | `0.19%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_MotorControl`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 100 activation(s), visually proving zero start-time preemption.
  - **`Task_SensorAgg`:** Plots 5 point(s) peaking at $y = 138.62\text{ µs}$ (mean $y = 129.85\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_CANTransmit`:** Plots 1 point(s) peaking at $y = 193.30\text{ µs}$ (mean $y = 193.30\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_MotorControl          0     1       1000    142.00    0.00         IPET    142.00         1000     858.00
Task_SensorAgg             0     2      20000     71.00    0.00         IPET    213.00        20000   19787.00
Task_CANTransmit           0     3     100000     36.00    0.00         IPET    249.00       100000   99751.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

### Generated Findings:
- **`[WARNING] [STATIC] autosar_concurrent_stack` (-20 points):**  
  *Concurrent worst-case stack depth (4128B) exceeds declared stack size (4096B) — stack overflow possible under full preemption [STATIC].*  
  *Fix: Increase `_Min_Stack_Size` in `linker.ld` to at least `0x1100` (4352 bytes) or reduce local buffer allocations.*
- **`[INFO] [STATIC] explicit_stack_found`:**  
  *Explicit stack reservation found. `_Min_Stack_Size` = 0x1000 (4096 bytes).*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_7/firmware.elf \
  --map tests/Test_Suite2/Test_7/firmware.map \
  --ld  tests/Test_Suite2/Test_7/linker.ld \
  --chip tests/Test_Suite2/Test_7/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_7/schedule.json \
  --charts-dir tests/Test_Suite2/Test_7/charts/
```
