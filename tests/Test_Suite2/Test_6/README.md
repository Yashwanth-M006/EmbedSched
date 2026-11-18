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
   * $\text{hp} = \{\text{Task\_ISR\_ADC}\}$ ($C_{\text{ISR}} = 0.74\text{ µs}, T_{\text{ISR}} = 1,000\text{ µs}$)
   * $R_1^{(0)} = 141.00\text{ µs}$
   * $R_1^{(1)} = 141.00 + \left\lceil \frac{141.00}{1,000} \right\rceil \times 0.74 = 141.00 + 0.74 = \mathbf{141.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $1,000 - 141.74 = \mathbf{+858.26\text{ µs}}$ (`PASS`)

3. **`Task_SensorAgg` (Priority 2):**
   * $\text{hp} = \{\text{Task\_ISR\_ADC}, \text{Task\_MotorControl}\}$
   * $R_2^{(0)} = 71.00\text{ µs}$
   * $R_2^{(1)} = 71.00 + \left\lceil \frac{71.00}{1,000} \right\rceil \times 0.74 + \left\lceil \frac{71.00}{1,000} \right\rceil \times 141.00 = 71.00 + 0.74 + 141.00 = \mathbf{212.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $20,000 - 212.74 = \mathbf{+19,787.26\text{ µs}}$ (`PASS`)

4. **`Task_CANTransmit` (Priority 3):**
   * $\text{hp} = \{\text{Task\_ISR\_ADC}, \text{Task\_MotorControl}, \text{Task\_SensorAgg}\}$
   * $R_3^{(0)} = 35.00\text{ µs}$
   * $R_3^{(1)} = 35.00 + \left\lceil \frac{35.00}{1,000} \right\rceil \times 0.74 + \left\lceil \frac{35.00}{1,000} \right\rceil \times 141.00 + \left\lceil \frac{35.00}{20,000} \right\rceil \times 71.00 = 35.00 + 0.74 + 141.00 + 71.00 = \mathbf{247.74\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $100,000 - 247.74 = \mathbf{+99,752.26\text{ µs}}$ (`PASS`)

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
