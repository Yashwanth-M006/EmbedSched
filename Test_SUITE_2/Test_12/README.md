# Test Case 12: Firmware vs Schedule Mismatch — Levenshtein Typo Detection

> **Status:** `CRITICAL ERROR` (Entry Function Typo Detected)  
> **Confidence:** `[STATIC]`  
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
- Exits with a non-zero exit code to block broken configurations from merging in CI/CD pipelines.

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

### B. Binary Artifact Inspection & WCET of Valid Tasks
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_12/firmware.map) at $168\text{ MHz}$ for the remaining valid tasks:

#### 1. Task_SensorAgg (`sensor_aggregate`):
* Symbol size in `.text.sensor_aggregate`: `0x391c` bytes = $14,620\text{ bytes}$
$$\text{Instructions} = \frac{14,620}{2.5} = 5,848.0\text{ instructions}$$
$$\text{Cycles} = 5,848.0 \times 1.15 = 6,725.2\text{ cycles}$$
$$C_{\text{Sensor}} = \frac{6,725.2}{168\text{ MHz}} \approx 40.00\text{ µs}$$

#### 2. Task_CANTransmit (`can_transmit_handler`):
* Symbol size in `.text.can_transmit_handler`: `0x1c94` bytes = $7,316\text{ bytes}$
$$\text{Instructions} = \frac{7,316}{2.5} = 2,926.4\text{ instructions}$$
$$\text{Cycles} = 2,926.4 \times 1.15 = 3,365.36\text{ cycles}$$
$$C_{\text{CAN}} = \frac{3,365.36}{168\text{ MHz}} \approx 20.00\text{ µs}$$

---

### C. Partial Response Time Analysis (Excluded Task Impact)

Because `Task_MotorControl` is excluded, the partial system contains only `Task_SensorAgg` (Priority 2) and `Task_CANTransmit` (Priority 3):

#### 1. Task_SensorAgg ($T = 20,000\text{ µs}, D = 20,000\text{ µs}$):
* Without `Task_MotorControl`, $hp(\text{Sensor}) = \emptyset$.
* $R_{\text{Sensor}} = C_{\text{Sensor}} = 40.00\text{ µs} \le 20,000\text{ µs}$  
* **Margin:** $20,000 - 40.00 = +19,960.00\text{ µs}$ (`PASS`)

#### 2. Task_CANTransmit ($T = 100,000\text{ µs}, D = 100,000\text{ µs}$):
* $hp(\text{CAN}) = \{\text{Task\_SensorAgg}\}$
* Recurrence iterations:
  $$R_{\text{CAN}}^{(0)} = C_{\text{CAN}} = 20.00\text{ µs}$$
  $$R_{\text{CAN}}^{(1)} = 20.00 + \left\lceil \frac{20.00}{20,000} \right\rceil \times 40.00 = 20.00 + (1 \times 40.00) = 60.00\text{ µs}$$
  $$R_{\text{CAN}}^{(2)} = 20.00 + \left\lceil \frac{60.00}{20,000} \right\rceil \times 40.00 = 60.00\text{ µs} \quad (\text{Converged})$$
* **Margin:** $100,000 - 60.00 = +99,940.00\text{ µs}$ (`PASS`)

#### Contrast with Full System Schedulability:
If `Task_MotorControl` ($C = 80.00\text{ µs}, T = 1,000\text{ µs}$) were correctly named and included:
* $R_{\text{Sensor}} = 40 + \lceil 40/1000 \rceil \times 80 = 120.00\text{ µs}$ (3x higher latency!)
* $R_{\text{CAN}} = 20 + \lceil 20/1000 \rceil \times 80 + \lceil 20/20000 \rceil \times 40 = 140.00\text{ µs}$ (2.3x higher latency!)

This contrast proves why EmbedSched treats symbol mismatches as a `CRITICAL` finding (-25 pts) and forces non-zero exit codes: omitting a task invalidates the entire real-time schedule.

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
CONFIG DIAGNOSTIC ERROR
====================================================================================
Error: Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols
Did you mean 'motor_control_loop'? (Levenshtein distance: 1)

[CRITICAL] [STATIC] autosar_entry_function_mismatch
  Error: Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols.
    Did you mean 'motor_control_loop'? (Levenshtein distance: 1)
    Task 'Task_MotorControl' is excluded from schedulability analysis.
  Fix: Update schedule.json: change entry_function from 'motor_controll_loop' to 'motor_control_loop'.

====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_CANTransmit           0     3     100000     20.00    0.00   CALCULATED     60.00       100000   99940.00      PASS
Task_SensorAgg             0     2      20000     40.00    0.00   CALCULATED     40.00        20000   19960.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet deadlines
```

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_12/firmware.elf \
  --map Test_SUITE_2/Test_12/firmware.map \
  --ld  Test_SUITE_2/Test_12/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_12/schedule.json \
  --charts-dir Test_SUITE_2/Test_12/charts/
```
