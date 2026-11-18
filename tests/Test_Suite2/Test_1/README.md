# Test Case 1: Baseline — Single Core, Rate Monotonic, No Resources

> **Status:** `PASS`  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 1 serves as the **end-to-end baseline and sanity verification** for the EmbedSched timing and schedulability pipeline. It proves that on a nominally loaded, correctly configured hard real-time firmware binary:
- Build artifacts (`firmware.elf`, `firmware.map`, `linker.ld`) are parsed without errors.
- Symbol sizes and addresses are correctly extracted from SRAM1 and DTCM memory sections.
- Static microarchitectural IPET analysis derives realistic, pipeline-accurate WCET figures (`[IPET]`).
- Response Time Analysis (RTA) confirms feasibility with generous positive slack margins.
- Discrete-event scheduler simulation executes across the hyperperiod with 0 deadline misses.
- Visual outputs (Dashboard, Gantt chart, Jitter plot, RTA table) render accurately without sub-pixel truncation.

---

## 2. Why It Was Performed

Before validating adversarial boundary conditions, failure modes, or multi-core contention, the tool must establish an uncorrupted ground truth on the **happy path**:
1. **Pipeline Completeness:** Validates that standard GCC build artifacts cleanly map to AUTOSAR task abstractions without requiring manual code instrumentations or hardware-in-the-loop (HIL) setups.
2. **False Positive Prevention:** Confirms that a safe, well-architected firmware application (utilization < 15%, no shared resources, optimal Rate Monotonic priority ordering) receives a 100/100 health score with zero false warnings.
3. **Reference Point:** Provides a baseline benchmark for execution speed, memory footprint, and chart generation aesthetics against which all subsequent adversarial stress tests are evaluated.

---

## 3. Configuration & Task Set

### Hardware Profile (`stm32f407.yaml`)
- **Core:** Single Cortex-M4 @ 168 MHz ($t_{\text{cycle}} = 1000/168 \approx 5.952\text{ ns}$)
- **Memory Layout:** DTCM (64 KB @ 0x10000000), SRAM1 (112 KB @ 0x20000000), Flash (1024 KB @ 0x08000000)
- **Wait States:** 0 wait states in DTCM and SRAM1; Flash configured with 4 wait states (5 bus cycles per access) at 168 MHz

### Task Configuration (`schedule.json`)
Three harmonic tasks operating on Core 0 under Rate Monotonic (RM) priority assignment:

| Task Name | Entry Function | Period ($T$) | Deadline ($D$) | Priority | Memory Placement |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_MotorControl` | `motor_control_loop` | 1,000 µs (1 ms) | 1,000 µs (1 ms) | 1 (Highest) | SRAM1 |
| `Task_SensorAgg` | `sensor_aggregate` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | SRAM1 |
| `Task_CANTransmit` | `can_transmit_handler` | 100,000 µs (100 ms) | 100,000 µs (100 ms) | 3 (Lowest) | SRAM1 |

---

## 4. Step-by-Step Calculations & Schedulability Math

### A. WCET Derivation from Binary Artifacts (IPET Microarchitectural Analysis)
In `main.c`, the task functions contain machine code instructions located in SRAM1:
* `motor_control_loop`: `0x722e` = **29,230 bytes** (from `firmware.map`)
* `sensor_aggregate`: `0x391c` = **14,620 bytes** (from `firmware.map`)
* `can_transmit_handler`: `0x1c94` = **7,316 bytes** (from `firmware.map`)

EmbedSched evaluates WCET via the **Implicit Path Enumeration Technique (IPET)** microarchitectural analysis engine (`analysis/ipet/`) for the ARM Cortex-M4 core at 168 MHz ($t_{\text{cycle}} \approx 5.952\text{ ns}$):
- **CFG Reconstruction:** Disassembles the ELF basic blocks via Capstone. At 2 bytes per 16-bit Thumb instruction (`movs r0, r0` sequence terminated by `bx lr`), the instruction counts are:
  - `motor_control_loop`: $29,230 / 2 = 14,615\text{ instructions}$
  - `sensor_aggregate`: $14,620 / 2 = 7,310\text{ instructions}$
  - `can_transmit_handler`: $7,316 / 2 = 3,658\text{ instructions}$
- **Microarchitectural Pipeline & Memory Modeling:**
  - Pipelined execution models instruction decode, execute, and register hazards.
  - Flash wait states ($ws = 4$) and 128-bit wide prefetch buffer line fetches ($1 + ws = 5$ cycles per 16-byte boundary crossing / cold fetch).
  - Terminal unconditional branch flush penalty ($1\text{ cycle}$ for Cortex-M4 direct branch).
- **ILP Formulation (SciPy HiGHS Solver):**
  $$\text{WCET}_{\text{cycles}} = \max \sum_{e \in E} c_e f_e \quad \text{subject to flow conservation constraints}$$

1. **`Task_MotorControl` (`motor_control_loop`):**
   $$\text{Instructions} = 14,615 \implies \text{Cycles} = 23,688\text{ cycles}$$
   $$\text{WCET} = \frac{23,688\text{ cycles}}{168\text{ MHz}} = \mathbf{141.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$$

2. **`Task_SensorAgg` (`sensor_aggregate`):**
   $$\text{Instructions} = 7,310 \implies \text{Cycles} = 11,928\text{ cycles}$$
   $$\text{WCET} = \frac{11,928\text{ cycles}}{168\text{ MHz}} = \mathbf{71.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$$

3. **`Task_CANTransmit` (`can_transmit_handler`):**
   $$\text{Instructions} = 3,658 \implies \text{Cycles} = 5,880\text{ cycles}$$
   $$\text{WCET} = \frac{5,880\text{ cycles}}{168\text{ MHz}} = \mathbf{35.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$$

---

### B. Processor Utilization Calculation
Dividing each derived WCET ($C_i$) by its configured period ($T_i$):
* $U_{\text{Motor}} = \frac{141.00\text{ µs}}{1,000\text{ µs}} = 14.10\%$
* $U_{\text{Sensor}} = \frac{71.00\text{ µs}}{20,000\text{ µs}} = 0.355\%$
* $U_{\text{CAN}} = \frac{35.00\text{ µs}}{100,000\text{ µs}} = 0.035\%$

**Total Core 0 Utilization ($U$):**
$$U = 14.10\% + 0.355\% + 0.035\% = 14.49\% \approx \mathbf{14.5\%}$$
$$\text{Duty Breakdown: Tasks } 14.5\% \mid \text{ISRs } 0.0\% \mid \text{Idle } 85.5\%$$

**Liu & Layland Bound Comparison:**
For $n = 3$ tasks:
$$U_{\text{bound}} = 3(2^{1/3} - 1) \approx 77.98\%$$
Since $U = 14.5\% \ll 78.0\%$, schedulability is mathematically guaranteed by the utilization bound alone.

---

### C. Response Time Analysis (RTA) Iterations
Solving Joseph & Pandya's recurrence relation ($R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \lceil R_i^{(k)}/T_j \rceil C_j$):

1. **`Task_MotorControl` (Priority 1):**
   * Preempting tasks: None ($\text{hp}(1) = \emptyset$)
   * Recurrence: $R_1 = C_1 = \mathbf{141.00\text{ µs}}$
   * Slack Margin: $D_1 - R_1 = 1,000\text{ µs} - 141.00\text{ µs} = \mathbf{+859.00\text{ µs}}$ (`PASS`)

2. **`Task_SensorAgg` (Priority 2):**
   * Preempting tasks: `Task_MotorControl` ($C_1 = 141.00\text{ µs}, T_1 = 1,000\text{ µs}$)
   * Iteration 0: $R_2^{(0)} = C_2 = 71.00\text{ µs}$
   * Iteration 1: $R_2^{(1)} = 71.00 + \left\lceil \frac{71.00}{1,000} \right\rceil \times 141.00 = 71.00 + (1 \times 141.00) = 212.00\text{ µs}$
   * Iteration 2: $R_2^{(2)} = 71.00 + \left\lceil \frac{212.00}{1,000} \right\rceil \times 141.00 = 71.00 + (1 \times 141.00) = \mathbf{212.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $D_2 - R_2 = 20,000\text{ µs} - 212.00\text{ µs} = \mathbf{+19,788.00\text{ µs}}$ (`PASS`)

3. **`Task_CANTransmit` (Priority 3):**
   * Preempting tasks: `Task_MotorControl` ($C_1 = 141.00\text{ µs}, T_1 = 1,000\text{ µs}$), `Task_SensorAgg` ($C_2 = 71.00\text{ µs}, T_2 = 20,000\text{ µs}$)
   * Iteration 0: $R_3^{(0)} = C_3 = 35.00\text{ µs}$
   * Iteration 1: $R_3^{(1)} = 35.00 + \left\lceil \frac{35.00}{1,000} \right\rceil \times 141.00 + \left\lceil \frac{35.00}{20,000} \right\rceil \times 71.00 = 35.00 + 141.00 + 71.00 = 247.00\text{ µs}$
   * Iteration 2: $R_3^{(2)} = 35.00 + \left\lceil \frac{247.00}{1,000} \right\rceil \times 141.00 + \left\lceil \frac{247.00}{20,000} \right\rceil \times 71.00 = 35.00 + 141.00 + 71.00 = \mathbf{247.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $D_3 - R_3 = 100,000\text{ µs} - 247.00\text{ µs} = \mathbf{+99,753.00\text{ µs}}$ (`PASS`)

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
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (141.00 µs) (total synchronous release load $\sum C_{hp} = 141.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{141.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 138.49\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{138.49\text{ µs}}$, $J^{\text{mean}} = \mathbf{132.84\text{ µs}}$, $\rho = \frac{138.49}{20,000} \times 100\% = \mathbf{0.69\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_CANTransmit` (Priority 3, $T = 100,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (141.00 µs), `Task_SensorAgg` (71.00 µs) (total synchronous release load $\sum C_{hp} = 212.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{212.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 193.02\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{193.02\text{ µs}}$, $J^{\text{mean}} = \mathbf{193.02\text{ µs}}$, $\rho = \frac{193.02}{100,000} \times 100\% = \mathbf{0.19\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_MotorControl` | 1 | `1,000 µs` | 100 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_SensorAgg` | 2 | `20,000 µs` | 5 | `138.49 µs` | `132.84 µs` | `0.69%` | **EXCELLENT (<1% of period)** |
| `Task_CANTransmit` | 3 | `100,000 µs` | 1 | `193.02 µs` | `193.02 µs` | `0.19%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_MotorControl`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 100 activation(s), visually proving zero start-time preemption.
  - **`Task_SensorAgg`:** Plots 5 point(s) peaking at $y = 138.49\text{ µs}$ (mean $y = 132.84\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_CANTransmit`:** Plots 1 point(s) peaking at $y = 193.02\text{ µs}$ (mean $y = 193.02\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_MotorControl          0     1       1000    141.00    0.00         IPET    141.00         1000     859.00
Task_SensorAgg             0     2      20000     71.00    0.00         IPET    212.00        20000   19788.00
Task_CANTransmit           0     3     100000     35.00    0.00         IPET    247.00       100000   99753.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

- **Health Score:** 100 / 100 (Grade A)
- **Memory Audit:** Stack in DTCM (zero wait states, isolated from DMA), `.text` in SRAM1.
- **Jitter Analysis:** Motor Control jitter is 0 µs; lower priority tasks show bounded release jitter caused by higher-priority task preemption.

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_1/firmware.elf \
  --map tests/Test_Suite2/Test_1/firmware.map \
  --ld  tests/Test_Suite2/Test_1/linker.ld \
  --chip tests/Test_Suite2/Test_1/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_1/schedule.json \
  --charts-dir tests/Test_Suite2/Test_1/charts/
```
