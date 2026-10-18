# Buttazzo Test Suite — Test Case 8: Priority Ceiling Protocol (PCP) Blocking (Buttazzo §7.3)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 7.3 (Priority Ceiling Protocol), Example 4.1.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization:** `80.0% <= 82.8% (GUARANTEED by Liu & Layland RM Bound)`  
> **Resource Protocol:** `Priority Ceiling Protocol (PCP)`  
> **Ceiling Calculation:** `Ceiling(R1) = min(Prio(tau1), Prio(tau2)) = 1 (Highest Priority)`  
> **Blocking Term:** `tau1 blocked by tau2 on R1 for up to 4.0 ms (B1 = 4.0 ms, B2 = 0.0 ms)`  
> **Algorithm:** `Rate Monotonic (RM) with PCP Blocking Terms`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Fixed-Priority (RM)

---

## 1. What This Test Signifies

Test Case 8 in the `buttazo_test` suite reproduces **Example 4.1 from Section 7.3 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark evaluates **resource sharing, priority inversion, and blocking term calculations under the Priority Ceiling Protocol (PCP)** (Sha, Rajkumar, & Lehoczky, 1990):
1. **The Priority Inversion Problem:** When tasks share mutual exclusion resources (mutexes/locks), a low-priority task holding a lock can prevent a high-priority task from executing. Without bounded protocols, intermediate tasks can preempt the low-priority task, causing unbounded priority inversion.
2. **Priority Ceiling Protocol (PCP) Guarantees:**
   - **Deadlock-Free:** Circular wait conditions are prevented by design.
   - **Bounded Blocking:** A task can be blocked by lower-priority tasks for **at most the duration of a single critical section** ($B_i \le \max CS$).
3. **PCP Ceiling & Blocking Formulation:**
   - Each resource gets a ceiling equal to the highest priority of any task that ever accesses it:
     $$\text{Ceiling}(R_k) = \min_{j} \{ \text{prio}(\tau_j) \mid \tau_j \text{ accesses } R_k \}$$
   - The blocking duration $B_i$ experienced by task $\tau_i$ is the maximum critical section of any lower-priority task accessing any resource with ceiling higher than or equal to $\tau_i$'s priority:
     $$B_i = \max_{j > i, k} \{ c_{j,k} \mid \text{Ceiling}(R_k) \le \text{prio}(\tau_i) \}$$
4. **Integration into Exact Response Time Analysis (RTA):**
   $$R_i^{(0)} = C_i + B_i$$
   $$R_i^{(m+1)} = C_i + B_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i^{(m)}}{T_j} \right\rceil C_j$$

---

## 2. Theoretical Background & Specification (Buttazzo §7.3 Ex. 4.1)

Two periodic tasks sharing a single protected resource $R_1$:

| Task | Execution Time ($C_i$) | Period ($T_i$) | Relative Deadline ($D_i$) | Priority (1=Highest) | Resource Usage | Critical Section Duration |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $10\text{ ms}\ (10,000\ \mu\text{s})$ | $10\text{ ms}\ (10,000\ \mu\text{s})$ | **1** | Uses $R_1$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ |
| $\tau_2$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $15\text{ ms}\ (15,000\ \mu\text{s})$ | $15\text{ ms}\ (15,000\ \mu\text{s})$ | **2** | Uses $R_1$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ |

### Priority Ceiling of Resource $R_1$
$$\text{Ceiling}(R_1) = \min(\text{prio}(\tau_1), \text{prio}(\tau_2)) = \min(1, 2) = \mathbf{1}$$

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check
$$U_1 = \frac{C_1}{T_1} = \frac{4}{10} = 0.40 \quad (40.0\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{6}{15} = 0.40 \quad (40.0\%)$$
$$U = \sum_{i=1}^{2} U_i = 0.40 + 0.40 = \mathbf{0.80\ (80.0\%)}$$

**Liu & Layland Utilization Bound ($n=2$):**
$$U_{\text{bound}}(2) = 2(2^{1/2} - 1) = 2(\sqrt{2} - 1) \approx 2 \times 0.41421 = \mathbf{0.8284\ (82.84\%)}$$
$$U = 80.0\% \le U_{\text{bound}} = 82.84\% \implies \mathbf{GUARANTEED\ (below\ RM\ bound)}$$

---

### B. Blocking Term Derivations

1. **For $\tau_1$ ($\text{prio} = 1$):**
   - Lower-priority tasks: $\{\tau_2\}$ ($\text{prio} = 2 > 1$).
   - $\tau_2$ accesses $R_1$.
   - $\text{Ceiling}(R_1) = 1 \le \text{prio}(\tau_1) = 1$.
   - The critical section of $\tau_2$ on $R_1$ is $c_{2,1} = 4\text{ ms}$.
   - Under PCP, blocking is bounded to at most a single critical section:
     $$B_1 = \mathbf{4\text{ ms}\ (4,000\ \mu\text{s})}$$

2. **For $\tau_2$ ($\text{prio} = 2$):**
   - Lower-priority tasks: $\emptyset$ (no tasks lower than $\tau_2$).
   - Therefore:
     $$B_2 = \mathbf{0\text{ ms}\ (0\ \mu\text{s})}$$

---

### C. Exact Response Time Analysis (RTA) with Blocking

1. **Task $\tau_1$ (Priority 1):**
   - Higher-priority tasks: $\emptyset$.
   - Recurrence relation:
     $$R_1 = C_1 + B_1 = 4\text{ ms} + 4\text{ ms} = \mathbf{8\text{ ms}\ (8,000\ \mu\text{s})}$$
   - Deadline check:
     $$R_1 = 8\text{ ms} \le D_1 = 10\text{ ms} \implies \mathbf{PASS\ (Margin: +2\text{ ms}\ /\ +2,000\ \mu\text{s})}$$

2. **Task $\tau_2$ (Priority 2):**
   - Higher-priority tasks: $\{\tau_1\}$.
   - Initial value:
     $$R_2^{(0)} = C_2 + B_2 = 6\text{ ms} + 0\text{ ms} = 6\text{ ms}$$
   - Iteration 1:
     $$R_2^{(1)} = C_2 + B_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 6 + 0 + \left\lceil \frac{6}{10} \right\rceil \times 4 = 6 + (1 \times 4) = \mathbf{10\text{ ms}}$$
   - Iteration 2:
     $$R_2^{(2)} = C_2 + B_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 6 + 0 + \left\lceil \frac{10}{10} \right\rceil \times 4 = 6 + (1 \times 4) = \mathbf{10\text{ ms}}$$
   - Convergence reached:
     $$R_2^{(2)} = R_2^{(1)} = 10\text{ ms} \implies R_2 = \mathbf{10\text{ ms}\ (10,000\ \mu\text{s})}$$
   - Deadline check:
     $$R_2 = 10\text{ ms} \le D_2 = 15\text{ ms} \implies \mathbf{PASS\ (Margin: +5\text{ ms}\ /\ +5,000\ \mu\text{s})}$$

---

## 4. Comparison of Expected vs. Actual Tool Output

| Metric / Checkpoint | Expected Theoretical Value | Actual Tool Output (`results.md`) | Match Status |
|:---|:---:|:---:|:---:|
| **Total Utilization ($U$)** | $80.0\%$ | `80.0%` | **EXACT MATCH** |
| **RM Utilization Bound** | $82.84\%$ | `RM bound: 82.8%` | **EXACT MATCH** |
| **Utilization Status** | Below bound | `GUARANTEED (below RM bound)` | **EXACT MATCH** |
| **$\tau_1$ Blocking Term ($B_1$)** | $4\text{ ms}$ (from $\tau_2$ on $R_1$) | `Blk µs: 4000.00` | **EXACT MATCH** |
| **$\tau_1$ WCRT ($R_1$)** | $8\text{ ms}$ | `WCRT µs: 8000.00` | **EXACT MATCH** |
| **$\tau_1$ Margin** | $+2\text{ ms}$ | `Margin µs: 2000.00` | **EXACT MATCH** |
| **$\tau_2$ Blocking Term ($B_2$)** | $0\text{ ms}$ | `Blk µs: 0.00` | **EXACT MATCH** |
| **$\tau_2$ WCRT ($R_2$)** | $10\text{ ms}$ | `WCRT µs: 10000.00` | **EXACT MATCH** |
| **$\tau_2$ Margin** | $+5\text{ ms}$ | `Margin µs: 5000.00` | **EXACT MATCH** |
| **PCP Diagnostic Finding** | $\tau_1$ blocked by $\tau_2$ on $R_1$ for $4\text{ms}$ | `[INFO] tau1 blocked by tau2 on R1 for up to 4ms [CALCULATED] (PCP)` | **EXACT MATCH** |
| **Overall Schedulability Verdict** | `SCHEDULABLE` | `● VERDICT: SCHEDULABLE — all tasks meet their deadlines (per RTA).` | **EXACT MATCH** |

---

## 5. Firmware Implementation Details

- **Target Architecture:** STM32F407VG ARM Cortex-M4 @ 168 MHz
- **Memory Footprint:**
  - Code section (`.text`): 3,652,200 bytes in SRAM1
  - Execution fills:
    - $\tau_1$ (`task1`): fill 1,460,858 bytes $\to 672,000\text{ cycles} \to \mathbf{4,000.0\ \mu\text{s}}$
    - $\tau_2$ (`task2`): fill 2,191,292 bytes $\to 1,008,000\text{ cycles} \to \mathbf{6,000.0\ \mu\text{s}}$
  - Stack allocation: 1,024 bytes (`_Min_Stack_Size = 0x400`) in DTCM RAM
- **Resource Specification:**
  - Resource: $R_1$ (mutex with PCP protocol)
  - Critical section of $\tau_1$: $2.0\text{ ms}$
  - Critical section of $\tau_2$: $4.0\text{ ms}$

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
   - Full diagnostic report: [`results.md`](file:///e:/firmware_analyzer/buttazo_test/Test_8/results.md)
   - Configuration: [`schedule.json`](file:///e:/firmware_analyzer/buttazo_test/Test_8/schedule.json)
   - Charts: [`charts/schedulability_dashboard.png`](file:///e:/firmware_analyzer/buttazo_test/Test_8/charts/schedulability_dashboard.png), [`charts/gantt_chart.png`](file:///e:/firmware_analyzer/buttazo_test/Test_8/charts/gantt_chart.png)
