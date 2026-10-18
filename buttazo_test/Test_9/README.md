# Buttazzo Test Suite — Test Case 9: Three Tasks with Bounded Priority Inversion & Ceiling Filtering (Buttazzo §7.3)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 7.3 (Priority Ceiling Protocol), Example 4.2.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization:** `70.0% <= 78.0% (GUARANTEED by Liu & Layland RM Bound)`  
> **Resource Protocol:** `Priority Ceiling Protocol (PCP)`  
> **Ceiling Calculation:** `Ceiling(R1) = min(Prio(tau1), Prio(tau3)) = 1 (Highest Priority)`  
> **Blocking Discrimination:**  
> - `tau1 (Priority 1): Blocked by tau3 on R1 for up to 3.0 ms (B1 = 3.0 ms)`  
> - `tau2 (Priority 2): Unblocked by R1 because Ceiling(R1) = 1 < Prio(tau2) = 2 (B2 = 0.0 ms)`  
> - `tau3 (Priority 3): No lower priority tasks (B3 = 0.0 ms)`  
> **Algorithm:** `Rate Monotonic (RM) with Selective PCP Blocking Terms`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Fixed-Priority (RM)

---

## 1. What This Test Signifies

Test Case 9 in the `buttazo_test` suite reproduces **Example 4.2 from Section 7.3 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark specifically evaluates **PCP Priority Ceiling Filtering and Directional Correctness**:
1. **The Core Question:** Under PCP, does an intermediate-priority task ($\tau_2$) that does not use a resource suffer blocking from a lower-priority task ($\tau_3$) holding a resource with a higher priority ceiling ($R_1$, ceiling = 1)?
2. **PCP Ceiling Blocking Condition:**
   - In fixed-priority scheduling with PCP, a task $\tau_i$ can be blocked by a lower-priority task $\tau_k$ holding resource $R$ **only if** the resource ceiling is high enough to block $\tau_i$.
   - In numerical priority notation where $\tau_1 = 1$ (highest), $\tau_2 = 2$, $\tau_3 = 3$ (lowest), resource $R_1$ has priority ceiling:
     $$\text{Ceiling}(R_1) = \min(\text{prio}(\tau_1), \text{prio}(\tau_3)) = 1$$
   - For $\tau_2$ ($\text{priority} = 2$), the condition $\text{Ceiling}(R_1) \ge \text{prio}(\tau_2)$ evaluates to:
     $$1 \ge 2 \implies \mathbf{FALSE}$$
   - Therefore, $\tau_2$ **cannot** be blocked by $R_1$. A lower-priority task holding $R_1$ cannot sneak in to block $\tau_2$, so $B_2 = 0\text{ ms}$.
3. **Preventing False Blocking Terms:** A naive or bug-ridden tool might incorrectly apply $R_1$'s 3 ms critical section to $\tau_2$ simply because $R_1$ has a high ceiling. This benchmark verifies that the engine accurately isolates intermediate tasks from unnecessary blocking terms.

---

## 2. Theoretical Background & Specification (Buttazzo §7.3 Ex. 4.2)

Three periodic tasks scheduled under preemptive Rate Monotonic priority assignment with shared resource $R_1$:

| Task | Execution Time ($C_i$) | Period ($T_i$) | Relative Deadline ($D_i$) | Priority (1=Highest) | Resource Usage | Critical Section Duration |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $8\text{ ms}\ (8,000\ \mu\text{s})$ | $8\text{ ms}\ (8,000\ \mu\text{s})$ | **1** | Uses $R_1$ | $1\text{ ms}\ (1,000\ \mu\text{s})$ |
| $\tau_2$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | **2** | **None** | $0\text{ ms}$ |
| $\tau_3$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | **3** | Uses $R_1$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ |

### Priority Ceiling of Resource $R_1$
$$\text{Ceiling}(R_1) = \min(\text{prio}(\tau_1), \text{prio}(\tau_3)) = \min(1, 3) = \mathbf{1}$$

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check
$$U_1 = \frac{C_1}{T_1} = \frac{2}{8} = 0.250 \quad (25.0\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{3}{12} = 0.250 \quad (25.0\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{4}{20} = 0.200 \quad (20.0\%)$$
$$U = \sum_{i=1}^{3} U_i = 0.25 + 0.25 + 0.20 = \mathbf{0.700\ (70.0\%)}$$

**Liu & Layland Utilization Bound ($n=3$):**
$$U_{\text{bound}}(3) = 3(2^{1/3} - 1) = 3(\sqrt[3]{2} - 1) \approx 3 \times 0.25992 = \mathbf{0.7798\ (77.98\%)}$$
$$U = 70.0\% \le U_{\text{bound}} = 77.98\% \implies \mathbf{GUARANTEED\ (below\ RM\ bound)}$$

---

### B. Blocking Term Derivations

1. **For $\tau_1$ ($\text{priority} = 1$):**
   - Lower-priority tasks: $\{\tau_2, \tau_3\}$ ($\text{prio} > 1$).
   - $\tau_3$ accesses $R_1$.
   - $\text{Ceiling}(R_1) = 1 \ge \text{prio}(\tau_1) = 1 \implies \mathbf{TRUE}$.
   - Critical section of $\tau_3$ on $R_1$ is $3\text{ ms}$.
   - Under PCP, blocking is bounded to one critical section:
     $$B_1 = \mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$$

2. **For $\tau_2$ ($\text{priority} = 2$):**
   - Lower-priority tasks: $\{\tau_3\}$ ($\text{prio} = 3 > 2$).
   - $\tau_3$ accesses $R_1$.
   - Check ceiling condition: $\text{Ceiling}(R_1) \ge \text{prio}(\tau_2) \implies 1 \ge 2 \implies \mathbf{FALSE}$.
   - Because $\text{Ceiling}(R_1) < \text{prio}(\tau_2)$, $\tau_2$ cannot be blocked by $\tau_3$ on $R_1$.
     $$B_2 = \mathbf{0\text{ ms}\ (0\ \mu\text{s})}$$

3. **For $\tau_3$ ($\text{priority} = 3$):**
   - No lower-priority tasks exist.
     $$B_3 = \mathbf{0\text{ ms}\ (0\ \mu\text{s})}$$

---

### C. Exact Response Time Analysis (RTA) with Blocking

1. **Task $\tau_1$ (Priority 1):**
   - Higher-priority tasks: $\emptyset$.
     $$R_1 = C_1 + B_1 = 2\text{ ms} + 3\text{ ms} = \mathbf{5\text{ ms}\ (5,000\ \mu\text{s})}$$
   - Deadline check:
     $$R_1 = 5\text{ ms} \le D_1 = 8\text{ ms} \implies \mathbf{PASS\ (Margin: +3\text{ ms}\ /\ +3,000\ \mu\text{s})}$$

2. **Task $\tau_2$ (Priority 2):**
   - Higher-priority tasks: $\{\tau_1\}$.
   - Initial value:
     $$R_2^{(0)} = C_2 + B_2 = 3\text{ ms} + 0\text{ ms} = 3\text{ ms}$$
   - Iteration 1:
     $$R_2^{(1)} = C_2 + B_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 3 + 0 + \left\lceil \frac{3}{8} \right\rceil \times 2 = 3 + (1 \times 2) = \mathbf{5\text{ ms}}$$
   - Iteration 2:
     $$R_2^{(2)} = C_2 + B_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 3 + 0 + \left\lceil \frac{5}{8} \right\rceil \times 2 = 3 + (1 \times 2) = \mathbf{5\text{ ms}}$$
   - Converged at $R_2 = \mathbf{5\text{ ms}\ (5,000\ \mu\text{s})}$.
   - Deadline check:
     $$R_2 = 5\text{ ms} \le D_2 = 12\text{ ms} \implies \mathbf{PASS\ (Margin: +7\text{ ms}\ /\ +7,000\ \mu\text{s})}$$

3. **Task $\tau_3$ (Priority 3):**
   - Higher-priority tasks: $\{\tau_1, \tau_2\}$.
   - Initial value:
     $$R_3^{(0)} = C_3 + B_3 = 4\text{ ms} + 0\text{ ms} = 4\text{ ms}$$
   - Iteration 1:
     $$R_3^{(1)} = 4 + \left\lceil \frac{4}{8} \right\rceil \times 2 + \left\lceil \frac{4}{12} \right\rceil \times 3 = 4 + (1 \times 2) + (1 \times 3) = 4 + 2 + 3 = \mathbf{9\text{ ms}}$$
   - Iteration 2:
     $$R_3^{(2)} = 4 + \left\lceil \frac{9}{8} \right\rceil \times 2 + \left\lceil \frac{9}{12} \right\rceil \times 3 = 4 + (2 \times 2) + (1 \times 3) = 4 + 4 + 3 = \mathbf{11\text{ ms}}$$
   - Iteration 3:
     $$R_3^{(3)} = 4 + \left\lceil \frac{11}{8} \right\rceil \times 2 + \left\lceil \frac{11}{12} \right\rceil \times 3 = 4 + (2 \times 2) + (1 \times 3) = 4 + 4 + 3 = \mathbf{11\text{ ms}}$$
   - Converged at $R_3 = \mathbf{11\text{ ms}\ (11,000\ \mu\text{s})}$.
   - Deadline check:
     $$R_3 = 11\text{ ms} \le D_3 = 20\text{ ms} \implies \mathbf{PASS\ (Margin: +9\text{ ms}\ /\ +9,000\ \mu\text{s})}$$

---

## 4. Comparison of Expected vs. Actual Tool Output

| Metric / Checkpoint | Expected Theoretical Value | Actual Tool Output (`results.md`) | Match Status |
|:---|:---:|:---:|:---:|
| **Total Utilization ($U$)** | $70.0\%$ | `70.0%` | **EXACT MATCH** |
| **RM Bound ($n=3$)** | $77.98\%$ | `RM bound: 78.0%` | **EXACT MATCH** |
| **Utilization Status** | Below bound | `GUARANTEED (below RM bound)` | **EXACT MATCH** |
| **$\tau_1$ Blocking Term ($B_1$)** | $3\text{ ms}$ (from $\tau_3$ on $R_1$) | `Blk µs: 3000.00` | **EXACT MATCH** |
| **$\tau_1$ WCRT / Margin** | WCRT $5\text{ ms}$, Margin $+3\text{ ms}$ | `WCRT µs: 5000.00, Margin µs: 3000.00` | **EXACT MATCH** |
| **$\tau_2$ Blocking Term ($B_2$)** | $0\text{ ms}$ (ceiling $1 < 2$, no blocking) | `Blk µs: 0.00` | **EXACT MATCH** |
| **$\tau_2$ WCRT / Margin** | WCRT $5\text{ ms}$, Margin $+7\text{ ms}$ | `WCRT µs: 5000.00, Margin µs: 7000.00` | **EXACT MATCH** |
| **$\tau_3$ Blocking Term ($B_3$)** | $0\text{ ms}$ | `Blk µs: 0.00` | **EXACT MATCH** |
| **$\tau_3$ WCRT / Margin** | WCRT $11\text{ ms}$, Margin $+9\text{ ms}$ | `WCRT µs: 11000.00, Margin µs: 9000.00` | **EXACT MATCH** |
| **PCP Diagnostic Finding** | $\tau_1$ blocked by $\tau_3$ on $R_1$ for $3\text{ ms}$ | `[INFO] tau1 blocked by tau3 on R1 for up to 3ms [CALCULATED] (PCP)` | **EXACT MATCH** |
| **Overall Schedulability Verdict** | `SCHEDULABLE` | `● VERDICT: SCHEDULABLE — all tasks meet their deadlines (per RTA).` | **EXACT MATCH** |

---

## 5. Firmware Implementation Details

- **Target Architecture:** STM32F407VG ARM Cortex-M4 @ 168 MHz
- **Memory Footprint:**
  - Code section (`.text`): 3,286,994 bytes in SRAM1
  - Execution fills:
    - $\tau_1$ (`task1`): fill 730,424 bytes $\to 336,000\text{ cycles} \to \mathbf{2,000.0\ \mu\text{s}}$
    - $\tau_2$ (`task2`): fill 1,095,642 bytes $\to 504,000\text{ cycles} \to \mathbf{3,000.0\ \mu\text{s}}$
    - $\tau_3$ (`task3`): fill 1,460,858 bytes $\to 672,000\text{ cycles} \to \mathbf{4,000.0\ \mu\text{s}}$
  - Stack allocation: 1,024 bytes (`_Min_Stack_Size = 0x400`) in DTCM RAM
- **Resource Specification:**
  - Resource: $R_1$ (mutex with PCP protocol)
  - Critical section of $\tau_1$: $1.0\text{ ms}$
  - Critical section of $\tau_3$: $3.0\text{ ms}$

---

## 6. How to Reproduce

1. **Compile ARM Firmware:**
   ```powershell
   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O0 -g -ffunction-sections -T linker.ld "-Wl,-Map=firmware.map" -nostartfiles -o firmware.elf main.c
   ```
2. **Execute Schedulability Analysis:**
   ```powershell
   python run.py
   ```
3. **Inspect Output Files:**
   - Full diagnostic report: [`results.md`](file:///e:/firmware_analyzer/buttazo_test/Test_9/results.md)
   - Configuration: [`schedule.json`](file:///e:/firmware_analyzer/buttazo_test/Test_9/schedule.json)
   - Charts: [`charts/schedulability_dashboard.png`](file:///e:/firmware_analyzer/buttazo_test/Test_9/charts/schedulability_dashboard.png), [`charts/gantt_chart.png`](file:///e:/firmware_analyzer/buttazo_test/Test_9/charts/gantt_chart.png)
