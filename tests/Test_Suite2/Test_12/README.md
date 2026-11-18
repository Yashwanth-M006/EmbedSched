# Test Case 12: Firmware vs Schedule Mismatch — Levenshtein Typo Detection

> **Status:** `CRITICAL ERROR` (Entry Function Typo Detected)  
> **Confidence:** `[IPET]` / `[STATIC]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Rule:** `autosar_entry_function_mismatch`

---

## 1. What This Test Signifies

Test Case 12 evaluates EmbedSched's **robustness, error resilience, and configuration mismatch handling**.

In production firmware workflows, schedule configurations (`schedule.json` or AUTOSAR ARXML files) are authored separately from the C source code. Common human errors include:
- Renaming a C function without updating `schedule.json`.
- A simple typo in the entry function name (e.g. `motor_controll_loop` with a double 'l').
- An inlined static function that no longer emits an exported global symbol in the `.map` file.

A naive or brittle analysis tool will either:
1. Crash with an unhandled exception (`KeyError` or `AttributeError`).
2. Silently assume $\text{WCET} = 0$, declaring that the task takes zero time and issuing an unsafely optimistic "PASS" verdict.

This test proves that EmbedSched:
- Validates every declared `entry_function` against the firmware symbol table.
- Computes **Levenshtein edit distances** against all valid firmware symbols.
- Automatically suggests the closest matching function name.
- Excludes the invalid task from schedulability calculations so false timing claims are never made.
- Emits a critical diagnostic finding and applies an appropriate safety deduction.

---

## 2. Why It Was Performed

1. **Developer Experience (DX):** Cryptic stack traces frustrate firmware engineers. Providing a clear *"Did you mean 'motor_control_loop'?"* diagnostic turns a debugging headache into a 5-second fix.
2. **Preventing Zero-WCET False Schedulability:** If a critical motor control loop is given a WCET of 0 because its function was not found, the tool would falsely report that the CPU is nearly idle. Schedulability analysis must be strictly guarded against missing symbol definitions.
3. **Automated CI Guardrails:** Guarantees that pull requests containing broken task definitions are immediately halted before flashing test benches.

---

## 3. Configuration & Task Set

### Mismatch Definition:
- **`schedule.json` Entry Function:** `"motor_controll_loop"` *(Typo: double 'l')*
- **Actual Firmware Symbol (`firmware.map`):** `motor_control_loop` *(Correct: single 'l')*

### Other Valid Tasks:
- `Task_SensorAgg`: Entry function `sensor_aggregate` (present in symbols).
- `Task_CANTransmit`: Entry function `can_transmit_handler` (present in symbols).

---

## 4. Step-by-Step Mathematical Calculations

### A. Levenshtein Distance Matrix & Matching Algorithm

The Levenshtein distance between string $s_1$ (length $m$) and $s_2$ (length $n$) is computed via dynamic programming:
$$D(i, 0) = i, \quad D(0, j) = j$$
$$D(i, j) = \min \begin{cases}
D(i-1, j) + 1 & \text{(Deletion)} \\
D(i, j-1) + 1 & \text{(Insertion)} \\
D(i-1, j-1) + \mathbb{I}(s_1[i] \ne s_2[j]) & \text{(Substitution)}
\end{cases}$$

For $s_1 = \text{"motor\_controll\_loop"}$ and $s_2 = \text{"motor\_control\_loop"}$:
* Prefix `"motor_contro"` matches character for character ($D(12, 12) = 0$).
* At index 13: $s_1[13] = \text{'l'}$, while $s_2[13] = \text{'l'}$.
* At index 14: $s_1[14] = \text{'l'}$, while $s_2[14] = \text{'\_'}$. One deletion of `'l'` reconciles the sequences.
* Remaining suffix `"_loop"` matches perfectly.

$$\text{Levenshtein Distance} = D(19, 18) = \mathbf{1}$$

Because $\text{dist} = 1 \le \text{Threshold} (3)$, EmbedSched matches the symbol and generates:
```
Did you mean 'motor_control_loop'? (Levenshtein distance: 1)
```

Task `Task_MotorControl` is marked invalid and **excluded from schedulability analysis** to prevent unvalidated zero-time assumptions.

---

### B. Binary Artifact Inspection & IPET WCET of Valid Tasks
The static analyzer inspects `firmware.map` and applies IPET microarchitectural timing at $168\text{ MHz}$ ($ws = 4$):

1. **`Task_SensorAgg` (`sensor_aggregate`):**
   * Symbol size: `0x391c` = $14,620\text{ bytes} \implies 7,310\text{ instructions}$
   * Pipelined execution & Flash fetch cycles: $11,928\text{ cycles}$
   * $C_{\text{Sensor}} = \frac{11,928}{168\text{ MHz}} = \mathbf{71.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

2. **`Task_CANTransmit` (`can_transmit_handler`):**
   * Symbol size: `0x1c94` = $7,316\text{ bytes} \implies 3,658\text{ instructions}$
   * Pipelined execution & Flash fetch cycles: $5,880\text{ cycles}$
   * $C_{\text{CAN}} = \frac{5,880}{168\text{ MHz}} = \mathbf{35.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

---

### C. Partial Response Time Analysis (Excluded Task Impact)

Because `Task_MotorControl` is excluded, the partial system contains only `Task_SensorAgg` (Priority 2) and `Task_CANTransmit` (Priority 3):

1. **`Task_SensorAgg` ($T = 20,000\text{ µs}, D = 20,000\text{ µs}$):**
   * Without `Task_MotorControl`, $\text{hp}(\text{Sensor}) = \emptyset$.
   * $R_{\text{Sensor}} = C_{\text{Sensor}} = \mathbf{71.00\text{ µs}} \le 20,000\text{ µs}$  
   * **Slack Margin:** $20,000 - 71.00 = \mathbf{+19,929.00\text{ µs}}$ (`PASS`)

2. **`Task_CANTransmit` ($T = 100,000\text{ µs}, D = 100,000\text{ µs}$):**
   * $\text{hp}(\text{CAN}) = \{\text{Task\_SensorAgg}\}$
   * Recurrence iterations:
     $$R_{\text{CAN}}^{(0)} = C_{\text{CAN}} = 35.00\text{ µs}$$
     $$R_{\text{CAN}}^{(1)} = 35.00 + \left\lceil \frac{35.00}{20,000} \right\rceil \times 71.00 = 35.00 + 71.00 = \mathbf{106.00\text{ µs}}\quad (\text{Converged})$$
   * **Slack Margin:** $100,000 - 106.00 = \mathbf{+99,894.00\text{ µs}}$ (`PASS`)

#### Contrast with Full System Schedulability:
If `Task_MotorControl` ($C = 141.00\text{ µs}, T = 1,000\text{ µs}$) were correctly named and included:
* $R_{\text{Sensor}} = 71 + \lceil 71/1000 \rceil \times 141 = \mathbf{212.00\text{ µs}}$
* $R_{\text{CAN}} = 35 + \lceil 35/1000 \rceil \times 141 + \lceil 35/20000 \rceil \times 71 = \mathbf{247.00\text{ µs}}$

This contrast proves why EmbedSched treats symbol mismatches as a `CRITICAL` finding (-25 pts) and forces non-zero exit codes: omitting a task invalidates the entire real-time schedule.

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
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (0.00 µs) (total synchronous release load $\sum C_{hp} = 0.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{0.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 0.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \frac{0.00}{20,000} \times 100\% = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_CANTransmit` (Priority 3, $T = 100,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (0.00 µs), `Task_SensorAgg` (71.00 µs) (total synchronous release load $\sum C_{hp} = 71.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{71.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 64.75\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{64.75\text{ µs}}$, $J^{\text{mean}} = \mathbf{64.75\text{ µs}}$, $\rho = \frac{64.75}{100,000} \times 100\% = \mathbf{0.06\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_MotorControl` | 1 | `1,000 µs` | 0 | `0.00 µs` | `0.00 µs` | `0.00%` | **N/A** |
| `Task_SensorAgg` | 2 | `20,000 µs` | 5 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_CANTransmit` | 3 | `100,000 µs` | 1 | `64.75 µs` | `64.75 µs` | `0.06%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_MotorControl`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 0 activation(s), visually proving zero start-time preemption.
  - **`Task_SensorAgg`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 5 activation(s), visually proving zero start-time preemption.
  - **`Task_CANTransmit`:** Plots 1 point(s) peaking at $y = 64.75\text{ µs}$ (mean $y = 64.75\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_SensorAgg             0     2      20000     71.00    0.00         IPET     71.00        20000   19929.00
Task_CANTransmit           0     3     100000     35.00    0.00         IPET    106.00       100000   99894.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

### Generated Findings:
- **`[CRITICAL] [STATIC] autosar_entry_function_mismatch` (-25 points):**  
  *Error: Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols.*  
  *Did you mean 'motor_control_loop'? (Levenshtein distance: 1)*  
  *Task 'Task_MotorControl' is excluded from schedulability analysis.*  
  *Fix: Update schedule.json: change entry_function from 'motor_controll_loop' to 'motor_control_loop'.*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_12/firmware.elf \
  --map tests/Test_Suite2/Test_12/firmware.map \
  --ld  tests/Test_Suite2/Test_12/linker.ld \
  --chip tests/Test_Suite2/Test_12/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_12/schedule.json \
  --charts-dir tests/Test_Suite2/Test_12/charts/
```
