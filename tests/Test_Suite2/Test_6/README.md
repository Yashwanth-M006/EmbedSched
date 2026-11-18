# Test Case 6: Hardware-Aware ISR Integration — Implicit Interrupt Interference

> **Status:** `PASS` (with Hardware Flash Placement Info)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic with Hardware ISR Injection

---

## 1. What This Test Signifies

Test Case 6 tests the bridge between **low-level microcontroller hardware architecture** and **high-level real-time scheduling**. 

In physical microcontrollers, **Hardware Interrupt Handlers (ISRs)** execute at a higher hardware priority than any software thread. Whenever an ADC conversion finishes or a timer ticks, the CPU hardware automatically stacks registers and jumps to the vector table, stealing cycles from running tasks.

This test demonstrates that EmbedSched:
1. **Auto-Detects Hardware Interrupts:** Discovers `adc_dma_isr` from the startup vector table (`startup_stm32f407xx.s`) and the `.map` file.
2. **Filters Startup Vectors:** Excludes `Reset_Handler` since boot routines are non-periodic initialization sequences.
3. **Models Hardware Exception Overhead:** Adds the mandatory hardware context-switching penalty (exception entry + unstacking per ARMv7-M Architecture Reference Manual).
4. **Calculates Memory Wait-State Inflation:** Models `adc_dma_isr` execution from Flash (4 wait states at 168 MHz on STM32F407).
5. **Injects ISR into Task Schedulability:** Models the ISR as an implicit highest-priority periodic task ($T = 1\text{ ms}$, Priority 0).
6. **Integrates Hardware Preemption into RTA:** Accurately accounts for interrupt preemption in the response times of all software threads (`motor_control_loop`, `sensor_aggregate`, and `can_transmit_handler`).

---

## 2. Why It Was Performed

1. **Eliminating the "Works in Simulator, Dies on Hardware" Trap:** Engineers frequently experience systems that pass theoretical real-time verification but crash on real silicon due to unaccounted interrupt theft.
2. **Hardware Placement Impact:** Evaluates the concrete scheduling consequences of memory placement: placing an ISR in Flash rather than ITCM/CCM incurs wait states.
3. **Automated Discovery:** Eliminates human error by extracting ISR names directly from assembly startup vectors rather than relying on manual documentation.

---

## 3. Configuration & Task Set

### Hardware Profile (`stm32f407.yaml`)
- **Clock:** 168 MHz ($t_{\text{cycle}} \approx 5.952\text{ ns}$)
- **Exception Overhead:** 12 cycles entry + 12 cycles return = 24 hardware cycles
- **Flash Wait States:** 4 wait states @ 168 MHz

### Task & ISR Configuration (`schedule.json` + Firmware Vectors):

| Entity | Symbol Name | Period ($T$) | Deadline ($D$) | Priority | Location | WCET ($C$) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_ISR_ADC` | `adc_dma_isr` | 1,000 µs (1 ms) | 1,000 µs (1 ms) | 0 (ISR Highest) | FLASH | 0.74 µs |
| `Task_MotorControl` | `motor_control_loop` | 1,000 µs (1 ms) | 1,000 µs (1 ms) | 1 | SRAM1 | 141.00 µs |
| `Task_SensorAgg` | `sensor_aggregate` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | SRAM1 | 71.00 µs |
| `Task_CANTransmit` | `can_transmit_handler` | 100,000 µs (100 ms) | 100,000 µs (100 ms) | 3 (Lowest) | SRAM1 | 35.00 µs |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
At $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$):

1. **Hardware ISR: `adc_dma_isr` (in FLASH):**
   * Disassembled body instructions with Flash wait states ($ws = 4$) plus 24-cycle hardware interrupt frame overhead:
   * $\text{WCET} = \mathbf{0.74\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

2. **Software Tasks (in SRAM1):**
   * `Task_MotorControl`: $\text{WCET} = \mathbf{141.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$
   * `Task_SensorAgg`: $\text{WCET} = \mathbf{71.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$
   * `Task_CANTransmit`: $\text{WCET} = \mathbf{35.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

---

### B. Utilization Breakdown
* $U_{\text{ISR}} = \frac{0.74\text{ µs}}{1,000\text{ µs}} = 0.074\%$
* $U_{\text{Motor}} = \frac{141.00\text{ µs}}{1,000\text{ µs}} = 14.10\%$
* $U_{\text{Sensor}} = \frac{71.00\text{ µs}}{20,000\text{ µs}} = 0.355\%$
* $U_{\text{CAN}} = \frac{35.00\text{ µs}}{100,000\text{ µs}} = 0.035\%$
* **Total Utilization:** $U = 0.074\% + 14.10\% + 0.355\% + 0.035\% = \mathbf{14.56\%} \approx \mathbf{14.6\%}$
* **Duty Breakdown:** Tasks 14.5% | ISRs 0.1% | Idle 85.4%

---

### C. Response Time Analysis with ISR Preemption
Recurrence: $R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \lceil R_i^{(k)} / T_j \rceil C_j$

1. **`Task_ISR_ADC` (Priority 0):**
   * $\text{hp} = \emptyset \implies R_{\text{ISR}} = C_{\text{ISR}} = \mathbf{0.74\text{ µs}}$
   * Slack Margin: $1,000 - 0.74 = \mathbf{+999.26\text{ µs}}$ (`PASS`)

2. **`Task_MotorControl` (Priority 1):**
   * $\text{hp} = \{\text{Task}_{\text{ISR}}\}$ ($C_{\text{ISR}} = 0.74\text{ µs}, T_{\text{ISR}} = 1,000\text{ µs}$)
   * $R_1^{(0)} = 141.00\text{ µs}$
   * $R_1^{(1)} = 141.00 + \left\lceil \frac{141.00}{1,000} \right\rceil \times 0.74 = 141.00 + 0.74 = \mathbf{141.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $1,000 - 141.74 = \mathbf{+858.26\text{ µs}}$ (`PASS`)

3. **`Task_SensorAgg` (Priority 2):**
   * $\text{hp} = \{\text{Task}_{\text{ISR}}, \text{Task}_{\text{Motor}}\}$
   * $R_2^{(0)} = 71.00\text{ µs}$
   * $R_2^{(1)} = 71.00 + \left\lceil \frac{71.00}{1,000} \right\rceil \times 0.74 + \left\lceil \frac{71.00}{1,000} \right\rceil \times 141.00 = 71.00 + 0.74 + 141.00 = \mathbf{212.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $20,000 - 212.74 = \mathbf{+19,787.26\text{ µs}}$ (`PASS`)

4. **`Task_CANTransmit` (Priority 3):**
   * $\text{hp} = \{\text{Task}_{\text{ISR}}, \text{Task}_{\text{Motor}}, \text{Task}_{\text{Sensor}}\}$
   * $R_3^{(0)} = 35.00\text{ µs}$
   * $R_3^{(1)} = 35.00 + \left\lceil \frac{35.00}{1,000} \right\rceil \times 0.74 + \left\lceil \frac{35.00}{1,000} \right\rceil \times 141.00 + \left\lceil \frac{35.00}{20,000} \right\rceil \times 71.00 = 35.00 + 0.74 + 141.00 + 71.00 = \mathbf{247.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $100,000 - 247.74 = \mathbf{+99,752.26\text{ µs}}$ (`PASS`)

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
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.74\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.68\text{ µs}}$, $\rho = \mathbf{0.07\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_SensorAgg` (Priority 2, $T = 20,000\text{ µs}$, $K = 5$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (141.00 µs) (total synchronous release load $\sum C_{hp} = 141.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{141.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 139.84\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{139.84\text{ µs}}$, $J^{\text{mean}} = \mathbf{131.16\text{ µs}}$, $\rho = \frac{139.84}{20,000} \times 100\% = \mathbf{0.70\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_CANTransmit` (Priority 3, $T = 100,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (141.00 µs), `Task_SensorAgg` (71.00 µs) (total synchronous release load $\sum C_{hp} = 212.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{212.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 203.96\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{203.96\text{ µs}}$, $J^{\text{mean}} = \mathbf{203.96\text{ µs}}$, $\rho = \frac{203.96}{100,000} \times 100\% = \mathbf{0.20\%} \implies$ **EXCELLENT (<1% of period)**.

4. **`Task_ISR_ADC` (Priority 4, $T = 1,000\text{ µs}$, $K = 100$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_MotorControl` (141.00 µs), `Task_SensorAgg` (71.00 µs), `Task_CANTransmit` (35.00 µs) (total synchronous release load $\sum C_{hp} = 247.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{247.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 0.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \frac{0.00}{1,000} \times 100\% = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_MotorControl` | 1 | `1,000 µs` | 100 | `0.74 µs` | `0.68 µs` | `0.07%` | **EXCELLENT (<1% of period)** |
| `Task_SensorAgg` | 2 | `20,000 µs` | 5 | `139.84 µs` | `131.16 µs` | `0.70%` | **EXCELLENT (<1% of period)** |
| `Task_CANTransmit` | 3 | `100,000 µs` | 1 | `203.96 µs` | `203.96 µs` | `0.20%` | **EXCELLENT (<1% of period)** |
| `Task_ISR_ADC` | 0 | `1,000 µs` | 100 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_MotorControl`:** Plots 100 point(s) peaking at $y = 0.74\text{ µs}$ (mean $y = 0.68\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_SensorAgg`:** Plots 5 point(s) peaking at $y = 139.84\text{ µs}$ (mean $y = 131.16\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_CANTransmit`:** Plots 1 point(s) peaking at $y = 203.96\text{ µs}$ (mean $y = 203.96\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_ISR_ADC`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 100 activation(s), visually proving zero start-time preemption.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_ISR_ADC               0     0       1000      0.74    0.00         IPET      0.74         1000     999.26
Task_MotorControl          0     1       1000    141.00    0.00         IPET    141.74         1000     858.26
Task_SensorAgg             0     2      20000     71.00    0.00         IPET    212.74        20000   19787.26
Task_CANTransmit           0     3     100000     35.00    0.00         IPET    247.74       100000   99752.26
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

- **Health Score:** 95 / 100
- **Deductions:** `explicit_stack_found (-0)`
- **Overall Verdict:** `PASS [IPET]`

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_6/firmware.elf \
  --map tests/Test_Suite2/Test_6/firmware.map \
  --ld  tests/Test_Suite2/Test_6/linker.ld \
  --chip tests/Test_Suite2/Test_6/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_6/schedule.json \
  --charts-dir tests/Test_Suite2/Test_6/charts/
```
