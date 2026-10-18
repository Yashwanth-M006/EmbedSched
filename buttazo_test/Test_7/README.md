# Buttazzo Test Suite — Test Case 7: EDF Constrained Deadlines Genuine Fail (Buttazzo §5.5 Modified)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 5.5 (Processor Demand Criterion under EDF), Example 3.3 modified.  
> **Status:** `FAIL (NOT SCHEDULABLE)`  
> **Utilization:** `93.3% <= 100.0% (PASSES naive utilization test alone)`  
> **Demand Bound Analysis:** `FAILED at L = 7,000 µs (h(7) = 8,000 µs > L = 7,000 µs by +1,000 µs)`  
> **Algorithm:** `EDF (Constrained Deadlines D < T)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 7 in the `buttazo_test` suite reproduces **Example 3.3 (modified) from Section 5.5 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark serves as the **definitive verification of Processor Demand Analysis (PDA)** under dynamic-priority EDF scheduling:
1. **The Classic Trap of Naive Utilization Testing:** Under implicit deadlines ($D_i = T_i$), $U \le 1.0$ is necessary and sufficient. However, for constrained deadlines ($D_i < T_i$), naive utilization is **insufficient**. In this test case, the total processor utilization is:
   $$U = \frac{2}{6} + \frac{6}{10} = 0.9333 \quad (93.33\% \le 100.0\%)$$
   A naive or improperly configured tool looking only at $U \le 1.0$ would falsely declare the system schedulable.
2. **Demand Bound Function Violation:** When evaluated using Baruah's Processor Demand Analysis:
   $$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) C_i$$
   At the second scheduling checkpoint ($L = 7\text{ ms}$), the cumulative required execution demand is:
   $$h(7) = 8\text{ ms} > L = 7\text{ ms}$$
   The workload demands $8\text{ ms}$ of computation in a window of only $7\text{ ms}$, creating an unavoidable $1\text{ ms}$ deadline overrun under any preemptive work-conserving algorithm.
3. **Automated Detection & Rejection:** EmbedSched detects $D_i < T_i$, runs full Processor Demand Analysis across all checkpoints up to hyperperiod $H = 30\text{ ms}$, flags the exact failure point at $L = 7,000\ \mu\text{s}$, and issues the CRITICAL finding `autosar_edf_constrained_deadline` with the overall verdict **NOT SCHEDULABLE**.

---

## 2. Theoretical Background & Specification

Two periodic tasks with constrained deadlines ($D_i < T_i$) scheduled under preemptive dynamic-priority EDF:

| Task | Execution Time ($C_i$) | Period ($T_i$) | Relative Deadline ($D_i$) | Constrained? | Utilization ($U_i$) | Scheduling Policy |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $\mathbf{5\text{ ms}\ (5,000\ \mu\text{s})}$ | $D_1 < T_1\ (5 < 6)$ | $33.33\%$ | **Dynamic EDF** |
| $\tau_2$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $10\text{ ms}\ (10,000\ \mu\text{s})$ | $\mathbf{7\text{ ms}\ (7,000\ \mu\text{s})}$ | $D_2 < T_2\ (7 < 10)$ | $60.00\%$ | **Dynamic EDF** |

> **Note on the intermediate variation ($C_2 = 5\text{ ms}$):**  
> If $\tau_2$ had $C_2 = 5\text{ ms}$ ($U = 83.3\%$), demand at $L=7$ would be $h(7) = 1 \times 2 + 1 \times 5 = 7 \le 7$, which remains critically schedulable with zero margin. Increasing $C_2$ to $6\text{ ms}$ ($U = 93.3\%$) produces a genuine demand bound failure at $L=7\text{ ms}$ with $h(7) = 8 > 7$.

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{2}{6} = \frac{1}{3} \approx 0.33333 \quad (33.33\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{6}{10} = \frac{3}{5} = 0.60000 \quad (60.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{2} U_i = \frac{1}{3} + \frac{3}{5} = \frac{14}{15} \approx \mathbf{0.93333\ (93.33\%)}$$

**Evaluation:**
$$U = 93.33\% \le 1.0000\ (100.0\%)$$
The processor is not statically overloaded ($U < 1$). Under implicit deadlines, this would guarantee schedulability. However, because $D_1 < T_1$ and $D_2 < T_2$, this condition is **insufficient**.

---

### B. Hyperperiod & Scheduling Checkpoint Generation

The hyperperiod is the Least Common Multiple of task periods:
$$H = \text{LCM}(T_1, T_2) = \text{LCM}(6\text{ ms}, 10\text{ ms}) = \mathbf{30\text{ ms}\ (30,000\ \mu\text{s})}$$

The set of testing checkpoints $\mathcal{D}$ comprises all absolute deadlines $k \cdot T_i + D_i \le H$:
- For $\tau_1$ ($T_1=6, D_1=5$):
  $$k=0 \implies 5\text{ ms}$$
  $$k=1 \implies 6 + 5 = 11\text{ ms}$$
  $$k=2 \implies 12 + 5 = 17\text{ ms}$$
  $$k=3 \implies 18 + 5 = 23\text{ ms}$$
  $$k=4 \implies 24 + 5 = 29\text{ ms}$$
- For $\tau_2$ ($T_2=10, D_2=7$):
  $$k=0 \implies 7\text{ ms}$$
  $$k=1 \implies 10 + 7 = 17\text{ ms}$$
  $$k=2 \implies 20 + 7 = 27\text{ ms}$$

Combining and ordering all unique checkpoints up to $H=30\text{ ms}$:
$$\mathcal{D} = \{ 5, 7, 11, 17, 23, 27, 29 \}\text{ ms}$$

---

### C. Evaluation of the Demand Bound Function $h(L)$

The demand bound function is:
$$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) C_i$$

Evaluating $h(L)$ across the checkpoints:

1. **At $L = 5\text{ ms}$:**
   $$h(5) = \left\lfloor \frac{5 + 6 - 5}{6} \right\rfloor \times 2 + \left\lfloor \frac{5 + 10 - 7}{10} \right\rfloor \times 6 = \lfloor 1 \rfloor \times 2 + \lfloor 0.8 \rfloor \times 6 = 2 + 0 = \mathbf{2\text{ ms}}$$
   $$h(5) = 2 \le L = 5 \implies \mathbf{PASS\ (Margin: +3\text{ ms})}$$

2. **At $L = 7\text{ ms}$ — DEADLINE VIOLATION:**
   $$h(7) = \left\lfloor \frac{7 + 6 - 5}{6} \right\rfloor \times 2 + \left\lfloor \frac{7 + 10 - 7}{10} \right\rfloor \times 6 = \lfloor 1.33 \rfloor \times 2 + \lfloor 1 \rfloor \times 6 = (1 \times 2) + (1 \times 6) = \mathbf{8\text{ ms}}$$
   $$h(7) = 8 > L = 7 \implies \mathbf{FAIL\ (Deficit: -1\text{ ms}\ /\ -1,000\ \mu\text{s})}$$

**Conclusion:**
At $L = 7\text{ ms}$, both $\tau_1$'s first job (deadline at $t=5\text{ ms}$, execution $2\text{ ms}$) and $\tau_2$'s first job (deadline at $t=7\text{ ms}$, execution $6\text{ ms}$) must be completed. The total demanded execution is $2 + 6 = 8\text{ ms}$. Since only $7\text{ ms}$ of CPU time has elapsed since $t=0$, at least one task is guaranteed to miss its deadline.

The system is **NOT SCHEDULABLE** under EDF.

---

## 4. Comparison of Expected vs. Actual Tool Output

| Metric / Checkpoint | Expected Theoretical Value | Actual Tool Output (`results.md`) | Match Status |
|:---|:---:|:---:|:---:|
| **Scheduling Algorithm** | Dynamic EDF (Constrained) | `EDF (constrained deadline)` | **EXACT MATCH** |
| **Total Utilization ($U$)** | $93.33\%$ | `93.3%` | **EXACT MATCH** |
| **Naive Bound Test** | Pass ($93.3\% \le 100.0\%$) | `EDF bound: 100.0% (constrained deadline)` | **EXACT MATCH** |
| **Demand Analysis at $L=7\text{ ms}$** | $h(7) = 8\text{ ms} > 7\text{ ms}$ | `FAILED at L=7000.0µs (demand h(7000.0) > 7000.0µs)` | **EXACT MATCH** |
| **Overall Verdict** | `NOT SCHEDULABLE` | `NOT SCHEDULABLE — deadline miss detected` | **EXACT MATCH** |
| **$\tau_1$ WCRT / Deadline** | WCRT $6\text{ ms} > D_1 = 5\text{ ms}$ | `WCRT: 6000.00 µs, Deadline: 5000 µs, Margin: -1000 µs` | **EXACT MATCH** |
| **$\tau_2$ WCRT / Deadline** | WCRT $8\text{ ms} > D_2 = 7\text{ ms}$ | `WCRT: 8000.00 µs, Deadline: 7000 µs, Margin: -1000 µs` | **EXACT MATCH** |
| **Targeted Finding** | Demand bound violation | `[CRITICAL] [EDF] autosar_edf_constrained_deadline` | **EXACT MATCH** |

---

## 5. Firmware Implementation Details

- **Hardware Target:** STM32F407VG ARM Cortex-M4 @ 168 MHz
- **Memory Architecture:**
  - `DTCM` (Data TCM RAM, 64 KB) at `0x20000000`
  - `SRAM1` (System RAM, 32 MB extended emulation) at `0x20010000`
- **Synthetic WCET Execution Footprint:**
  - $\tau_1$ (`task1`): Calibration fill 730,430 instructions $\to 336,003\text{ cycles} \to \mathbf{2,000.0\ \mu\text{s}}$
  - $\tau_2$ (`task2`): Calibration fill 2,191,292 instructions $\to 1,007,999\text{ cycles} \to \mathbf{6,000.0\ \mu\text{s}}$
- **Binary Footprint:**
  - Code section (`.text`): 484 bytes
  - Data / fill section (`.data`): 2,921,772 bytes (SRAM1)
  - Stack reservation: 1,024 bytes (DTCM)

---

## 6. How to Reproduce

1. **Compile the ARM Cortex-M4 Firmware:**
   ```powershell
   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O0 -g -T linker.ld -Wl,-Map=firmware.map -nostartfiles -o firmware.elf main.c
   ```
2. **Execute EmbedSched Analysis:**
   ```powershell
   python run.py
   ```
3. **Inspect Generated Artifacts:**
   - Full diagnostic report: [`results.md`](file:///e:/firmware_analyzer/buttazo_test/Test_7/results.md)
   - Schedule configuration: [`schedule.json`](file:///e:/firmware_analyzer/buttazo_test/Test_7/schedule.json)
   - Visual charts: [`charts/schedulability_dashboard.png`](file:///e:/firmware_analyzer/buttazo_test/Test_7/charts/schedulability_dashboard.png)
