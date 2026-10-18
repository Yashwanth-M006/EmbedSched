# Test Case 1: Baseline — Single Core, Rate Monotonic, No Resources

> **Status:** `PASS`  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 1 serves as the **end-to-end baseline and sanity verification** for the EmbedSched timing and schedulability pipeline. It proves that on a nominally loaded, correctly configured hard real-time firmware binary:
- Build artifacts (`firmware.elf`, `firmware.map`, `linker.ld`) are parsed without errors.
- Symbol sizes and addresses are correctly extracted from SRAM1 and DTCM memory sections.
- Code-size heuristics derive realistic WCET figures (`[CALCULATED]`).
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
- **Core:** Single Cortex-M4 @ 168 MHz ($t_{\text{cycle}} \approx 5.95\text{ ns}$)
- **Memory Layout:** DTCM (64 KB @ 0x10000000), SRAM1 (112 KB @ 0x20000000), Flash (1024 KB @ 0x08000000)
- **Wait States:** 0 wait states in DTCM and SRAM1

### Task Configuration (`schedule.json`)
Three harmonic tasks operating on Core 0 under Rate Monotonic (RM) priority assignment:

| Task Name | Entry Function | Period ($T$) | Deadline ($D$) | Priority | Memory Placement |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_MotorControl` | `motor_control_loop` | 1,000 µs (1 ms) | 1,000 µs (1 ms) | 1 (Highest) | SRAM1 |
| `Task_SensorAgg` | `sensor_aggregate` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | SRAM1 |
| `Task_CANTransmit` | `can_transmit_handler` | 100,000 µs (100 ms) | 100,000 µs (100 ms) | 3 (Lowest) | SRAM1 |

---

---

## 4. Step-by-Step Calculations & Schedulability Math

### A. WCET Derivation from Binary Artifacts
In `main.c`, the task functions contain inline assembly `.fill` statements that define their machine code size in SRAM1:
* `motor_control_loop`: `0x722e` = **29,230 bytes** (from `firmware.map`)
* `sensor_aggregate`: `0x391c` = **14,620 bytes** (from `firmware.map`)
* `can_transmit_handler`: `0x1c94` = **7,316 bytes** (from `firmware.map`)

Applying EmbedSched's analytical timing formula (`analysis/wcet_extractor.py`) at 168 MHz ($t_{\text{cycle}} = 1000/168 \approx 5.952\text{ ns}$):

1. **`Task_MotorControl` (`motor_control_loop`):**
   $$\text{Instructions} = \frac{29,230\text{ bytes}}{2.5\text{ bytes/insn}} = 11,692\text{ instructions}$$
   $$\text{Cycles} = \text{round}(11,692 \times 1.15\text{ CPI}) = 13,445\text{ cycles}$$
   $$\text{WCET} = \frac{13,445 \times 5.952\text{ ns}}{1000} = 80.03\text{ µs} \xrightarrow{\text{round}} \mathbf{80.00\text{ µs}}$$

2. **`Task_SensorAgg` (`sensor_aggregate`):**
   $$\text{Instructions} = \frac{14,620\text{ bytes}}{2.5\text{ bytes/insn}} = 5,848\text{ instructions}$$
   $$\text{Cycles} = \text{round}(5,848 \times 1.15\text{ CPI}) = 6,725\text{ cycles}$$
   $$\text{WCET} = \frac{6,725 \times 5.952\text{ ns}}{1000} = 40.03\text{ µs} \xrightarrow{\text{round}} \mathbf{40.00\text{ µs}}$$

3. **`Task_CANTransmit` (`can_transmit_handler`):**
   $$\text{Instructions} = \frac{7,316\text{ bytes}}{2.5\text{ bytes/insn}} = 2,926\text{ instructions}$$
   $$\text{Cycles} = \text{round}(2,926 \times 1.15\text{ CPI}) = 3,365\text{ cycles}$$
   $$\text{WCET} = \frac{3,365 \times 5.952\text{ ns}}{1000} = 20.03\text{ µs} \xrightarrow{\text{round}} \mathbf{20.00\text{ µs}}$$

---

### B. Processor Utilization Calculation
Dividing each derived WCET ($C_i$) by its configured period ($T_i$):
* $U_{\text{Motor}} = \frac{80\text{ µs}}{1,000\text{ µs}} = 8.00\%$
* $U_{\text{Sensor}} = \frac{40\text{ µs}}{20,000\text{ µs}} = 0.20\%$
* $U_{\text{CAN}} = \frac{20\text{ µs}}{100,000\text{ µs}} = 0.02\%$

**Total Core 0 Utilization ($U$):**
$$U = 8.00\% + 0.20\% + 0.02\% = \mathbf{8.22\%}$$

**Liu & Layland Bound Comparison:**
For $n = 3$ tasks:
$$U_{\text{bound}} = 3(2^{1/3} - 1) \approx 77.98\%$$
Since $U = 8.22\% \ll 77.98\%$, schedulability is mathematically guaranteed by the utilization bound alone.

---

### C. Response Time Analysis (RTA) Iterations
Solving Joseph & Pandya's recurrence relation ($R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \lceil R_i^{(k)}/T_j \rceil C_j$):

1. **`Task_MotorControl` (Priority 1):**
   * Preempting tasks: None ($\text{hp}(1) = \emptyset$)
   * Recurrence: $R_1 = C_1 = \mathbf{80.00\text{ µs}}$
   * Slack Margin: $D_1 - R_1 = 1,000\text{ µs} - 80\text{ µs} = \mathbf{+920.00\text{ µs}}$

2. **`Task_SensorAgg` (Priority 2):**
   * Preempting tasks: `Task_MotorControl` ($C_1 = 80\text{ µs}, T_1 = 1,000\text{ µs}$)
   * Iteration 0: $R_2^{(0)} = C_2 = 40.00\text{ µs}$
   * Iteration 1: $R_2^{(1)} = 40 + \left\lceil \frac{40}{1,000} \right\rceil \times 80 = 40 + (1 \times 80) = 120.00\text{ µs}$
   * Iteration 2: $R_2^{(2)} = 40 + \left\lceil \frac{120}{1,000} \right\rceil \times 80 = 40 + (1 \times 80) = \mathbf{120.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $D_2 - R_2 = 20,000\text{ µs} - 120\text{ µs} = \mathbf{+19,880.00\text{ µs}}$

3. **`Task_CANTransmit` (Priority 3):**
   * Preempting tasks: `Task_MotorControl` ($C_1 = 80\text{ µs}, T_1 = 1,000\text{ µs}$), `Task_SensorAgg` ($C_2 = 40\text{ µs}, T_2 = 20,000\text{ µs}$)
   * Iteration 0: $R_3^{(0)} = C_3 = 20.00\text{ µs}$
   * Iteration 1: $R_3^{(1)} = 20 + \left\lceil \frac{20}{1,000} \right\rceil \times 80 + \left\lceil \frac{20}{20,000} \right\rceil \times 40 = 20 + 80 + 40 = 140.00\text{ µs}$
   * Iteration 2: $R_3^{(2)} = 20 + \left\lceil \frac{140}{1,000} \right\rceil \times 80 + \left\lceil \frac{140}{20,000} \right\rceil \times 40 = 20 + 80 + 40 = \mathbf{140.00\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $D_3 - R_3 = 100,000\text{ µs} - 140\text{ µs} = \mathbf{+99,860.00\text{ µs}}$

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_MotorControl          0     1       1000     80.00    0.00   CALCULATED     80.00         1000     920.00      PASS
Task_SensorAgg             0     2      20000     40.00    0.00   CALCULATED    120.00        20000   19880.00      PASS
Task_CANTransmit           0     3     100000     20.00    0.00   CALCULATED    140.00       100000   99860.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

- **Health Score:** 100 / 100 (Grade A)
- **Memory Audit:** Stack in DTCM (zero wait states, isolated from DMA), `.text` in SRAM1.
- **Jitter Analysis:** Motor Control jitter is 0 µs; lower priority tasks show bounded release jitter caused by higher-priority task preemption.

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_1/firmware.elf \
  --map Test_SUITE_2/Test_1/firmware.map \
  --ld  Test_SUITE_2/Test_1/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_1/schedule.json \
  --charts-dir Test_SUITE_2/Test_1/charts/
```
