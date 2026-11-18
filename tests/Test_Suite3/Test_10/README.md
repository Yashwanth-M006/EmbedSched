# Buttazzo Test Suite — Test Case 10: Stack Overflow Exactly at Boundary (Buttazzo §5.1)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 5.1 (Shared Stack and Memory Models).  
> **Status:** `WARNING (Boundary & Overflow Detection)`  
> **Declared Stack Size:** `2,400 Bytes (_Min_Stack_Size in linker.ld)`  
> **Case 1 (Exact Boundary):** `800 + 800 + 800 = 2,400B = declared size (WARNING, 0 Margin, NOT CRITICAL)`  
> **Case 2 (Off-by-One Overflow):** `801 + 800 + 800 = 2,401B > 2,400B declared size (WARNING, Stack Overflow)`  
> **Algorithm:** `Concurrent Preemptive Stack Analysis`  
> **Confidence:** `[STATIC]`  
> **Scheduler:** Single-Core Preemptive Fixed-Priority (RM)

---

## 1. What This Test Signifies

Test Case 10 in the `buttazo_test` suite evaluates the **exact boundary and off-by-one behavior** of concurrent stack depth analysis under full preemptive execution:
1. **The Shared-Stack Preemption Model:** Under single-stack embedded OS architectures (e.g. OSEK/AUTOSAR Basic Tasks or single interrupt/main stacks), tasks execute on a shared stack area. Under worst-case preemption:
   - Lowest priority task $\tau_3$ is activated and allocates its stack ($800\text{ B}$).
   - $\tau_3$ is preempted by medium priority task $\tau_2$, which allocates its stack ($800\text{ B}$).
   - $\tau_2$ is preempted by highest priority task $\tau_1$, which allocates its stack ($800\text{ B}$ / $801\text{ B}$).
   - Total concurrent stack depth equals the sum: $\sum_{i=1}^n \text{Stack}_i$.
2. **Boundary Testing ($2,400\text{ B} = 2,400\text{ B}$):**
   - When the cumulative stack depth exactly equals the declared stack size ($2,400\text{ B}$ declared via `_Min_Stack_Size`), the condition for overflow ($> 2,400\text{ B}$) is strictly **not met** ($2,400 > 2,400 \implies \text{FALSE}$).
   - The tool emits a **WARNING (not CRITICAL)** identifying that the stack depth reaches capacity with zero headroom.
3. **Off-by-One Overflow Testing ($2,401\text{ B} > 2,400\text{ B}$):**
   - Increasing $\tau_1$'s stack by a single byte ($801\text{ B}$) pushes total concurrent stack depth to $2,401\text{ B}$.
   - The overflow condition ($2,401 > 2,400$) evaluates to **TRUE**, triggering the warning `Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B)`.

---

## 2. Theoretical Background & Specification

Three periodic tasks on Core 0 sharing a single stack allocation declared in `linker.ld` (`_Min_Stack_Size = 2400`):

| Task | Priority | Period ($T_i$) | Deadline ($D_i$) | Stack Usage (Case 1) | Stack Usage (Case 2) | Preemption Role |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | **1 (Highest)** | $10\text{ ms}$ | $10\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{801\text{ B}}$ | Preempts $\tau_2$ and $\tau_3$ |
| $\tau_2$ | **2 (Medium)** | $15\text{ ms}$ | $15\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{800\text{ B}}$ | Preempts $\tau_3$, preempted by $\tau_1$ |
| $\tau_3$ | **3 (Lowest)** | $20\text{ ms}$ | $20\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{800\text{ B}}$ | Preempted by $\tau_2$ and $\tau_1$ |

**Declared Stack Size in Linker Script:**
$$\text{Declared Capacity} = \text{Min-Stack-Size} = 2,400\text{ Bytes}\ (0\text{x}0960)$$

---

## 3. Step-by-Step Mathematical Calculations

### Case 1: Exact Boundary ($2,400\text{ B} = 2,400\text{ B}$)

Under worst-case preemption ($\tau_3$ preempted by $\tau_2$ preempted by $\tau_1$):
$$\text{Total Stack Depth} = \text{Stack}(\tau_3) + \text{Stack}(\tau_2) + \text{Stack}(\tau_1) = 800 + 800 + 800 = \mathbf{2,400\text{ Bytes}}$$

**Comparison:**
$$\text{Total Depth} = 2,400\text{ B} \le \text{Declared Capacity} = 2,400\text{ B}$$
- Condition for overflow ($2,400 > 2,400$) is **FALSE**.
- Severity: **`WARNING` (not `CRITICAL`)** since $2,400 = 2,400$, not greater than.
- Diagnostic finding:
  ```text
  [WARNING] [STATIC] autosar_concurrent_stack
    Concurrent worst-case stack depth (2400B) reaches declared stack size (2400B) with zero margin under full preemption [STATIC]
  ```

---

### Case 2: Off-by-One Overflow ($2,401\text{ B} > 2,400\text{ B}$)

Changing $\tau_1$'s stack usage from $800\text{ B}$ to $801\text{ B}$:
$$\text{Total Stack Depth} = \text{Stack}(\tau_3) + \text{Stack}(\tau_2) + \text{Stack}(\tau_1) = 800 + 800 + 801 = \mathbf{2,401\text{ Bytes}}$$

**Comparison:**
$$\text{Total Depth} = 2,401\text{ B} > \text{Declared Capacity} = 2,400\text{ B} \implies \mathbf{TRUE\ (+1\text{ Byte Overflow})}$$
- Condition for overflow ($2,401 > 2,400$) is **TRUE**.
- Severity: **`WARNING`**
- Diagnostic finding:
  ```text
  [WARNING] [STATIC] autosar_concurrent_stack
    Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B) — stack overflow possible under full preemption [STATIC]
  ```

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

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 60,000\text{ µs}$)
1. **`tau1` (Priority 1, $T = 10,000\text{ µs}$, $K = 6$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 10,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`tau2` (Priority 2, $T = 15,000\text{ µs}$, $K = 4$ activations):**
   * **Interference:** Preempted by higher-priority workload: `tau1` (3,533.00 µs) (total synchronous release load $\sum C_{hp} = 3,533.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{3,533.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 3,391.19\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{3,391.19\text{ µs}}$, $J^{\text{mean}} = \mathbf{1,633.30\text{ µs}}$, $\rho = \frac{3,391.19}{15,000} \times 100\% = \mathbf{22.61\%} \implies$ **HIGH (>20% of period)**.

3. **`tau3` (Priority 3, $T = 20,000\text{ µs}$, $K = 3$ activations):**
   * **Interference:** Preempted by higher-priority workload: `tau1` (3,533.00 µs), `tau2` (5,299.00 µs) (total synchronous release load $\sum C_{hp} = 8,832.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{8,832.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 8,208.98\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{8,208.98\text{ µs}}$, $J^{\text{mean}} = \mathbf{6,363.72\text{ µs}}$, $\rho = \frac{8,208.98}{20,000} \times 100\% = \mathbf{41.04\%} \implies$ **HIGH (>20% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `tau1` | 1 | `10,000 µs` | 6 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `tau2` | 2 | `15,000 µs` | 4 | `3,391.19 µs` | `1,633.30 µs` | `22.61%` | **HIGH (>20% of period)** |
| `tau3` | 3 | `20,000 µs` | 3 | `8,208.98 µs` | `6,363.72 µs` | `41.04%` | **HIGH (>20% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`tau1`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 6 activation(s), visually proving zero start-time preemption.
  - **`tau2`:** Plots 4 point(s) peaking at $y = 3,391.19\text{ µs}$ (mean $y = 1,633.30\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`tau3`:** Plots 3 point(s) peaking at $y = 8,208.98\text{ µs}$ (mean $y = 6,363.72\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 4. Comparison of Expected vs. Actual Tool Output

| Test Scenario | Evaluated Stack Expression | Expected Tool Output | Actual Tool Output (`results.md`) | Match Status |
|:---|:---:|:---:|:---:|:---:|
| **Case 1: Exact Boundary** | $800 + 800 + 800 = 2,400\text{B} = 2,400\text{B}$ | `WARNING (not CRITICAL)` | `[WARNING] Concurrent worst-case stack depth (2400B) reaches declared stack size (2400B) with zero margin` | **EXACT MATCH** |
| **Case 2: Off-by-One** | $801 + 800 + 800 = 2,401\text{B} > 2,400\text{B}$ | `WARNING fires` | `[WARNING] Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B) — stack overflow possible` | **EXACT MATCH** |

---

## 5. Firmware Implementation Details

- **Hardware Architecture:** STM32F407 Cortex-M4
- **Linker Configuration (`linker.ld`):**
  - Declared stack symbol: `_Min_Stack_Size = 2400;` ($0\text{x}0960$)
  - Placed in DTCM RAM: `.stack : { . = . + _Min_Stack_Size; } >DTCM`
- **Firmware Functions:**
  - `task1`: Entry for $\tau_1$
  - `task2`: Entry for $\tau_2$
  - `task3`: Entry for $\tau_3$

---

## 6. How to Reproduce

1. **Compile ARM Firmware:**
   ```powershell
   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O0 -g -ffunction-sections -T linker.ld "-Wl,-Map=firmware.map" -nostartfiles -o firmware.elf main.c
   ```
2. **Execute Boundary Analysis (Case 1: 2,400B):**
   - Ensure `schedule.json` has `tau1` `stack_bytes: 800`.
   ```powershell
   python run.py
   ```
3. **Execute Off-by-One Overflow Analysis (Case 2: 2,401B):**
   - Update `schedule.json` to set `tau1` `stack_bytes: 801`.
   ```powershell
   python run.py
   ```
4. **Inspect Generated Reports:**
   - Case 1 Report: [`results_boundary_2400.md`](file:///e:/firmware_analyzer/buttazo_test/Test_10/results_boundary_2400.md)
   - Case 2 Report: [`results.md`](file:///e:/firmware_analyzer/buttazo_test/Test_10/results.md)
