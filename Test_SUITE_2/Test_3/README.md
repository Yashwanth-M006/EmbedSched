# Test Case 3: Genuine Deadline Miss — RTA Detects It

> **Status:** `FAIL` (Deadline Miss Detected)  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 3 represents the **critical safety failure mode**: a task set that easily **passes** the classical utilization bound check ($U \le 78.0\%$), but **violates a hard real-time deadline** under preemption.

This catches simplistic analysis tools that rely solely on total CPU utilization $\sum C_i/T_i$. It demonstrates:
- Exact recurrence calculation for tasks with **constrained relative deadlines** ($D_i < T_i$).
- Detection of **Rate Monotonic sub-optimality**: when $D_i < T_i$, assigning priority strictly by period ($T$) instead of deadline ($D$) is provably suboptimal (Deadline Monotonic should be used).
- Prominent rendering of a **red deadline overrun bar** in the Response Time chart and a `CRITICAL` deduction in the safety audit.

---

## 2. Why It Was Performed

1. **Safety-Critical Verification:** In automotive powertrain and braking ECUs (ISO 26262 ASIL-D), a task missing a 6 ms deadline by even 200 µs can cause control loop divergence. The analyzer must reliably catch this at compile-time before flashing hardware.
2. **Exposing Utilization Fallacies:** A system loaded at only 71.3% can still miss deadlines if high-frequency preemption aligns maliciously with a tight deadline window.
3. **Actionable Remediation Guidance:** The tool must not merely report an error; it must advise the architect on the root cause (switching from RM to Deadline Monotonic, lowering WCET, or moving hot paths to zero-wait-state CCM/ITCM).

---

## 3. Configuration & Task Set

### Task Configuration (`schedule.json`)
Three tasks on Core 0 where `Task_B` has a tight deadline ($D_B = 6,000\text{ µs}$):

| Task Name | Period ($T$) | Deadline ($D$) | Priority (RM) | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | 3,000 µs (3.0 ms) | 30.00% |
| `Task_B` | 15,000 µs (15 ms) | **6,000 µs (6.0 ms)** | 2 | 3,200 µs (3.2 ms) | 21.33% |
| `Task_C` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 3 (Lowest) | 4,000 µs (4.0 ms) | 20.00% |
| **Total** | — | — | — | — | **71.33%** |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_3/firmware.map) to extract symbol sizes for each task located in `SRAM1` ($0\text{ wait states}$ on STM32F407):

* **Target Core:** ARM Cortex-M4 running at $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$).
* **Thumb-2 Instruction Model:** $2.5\text{ bytes/instruction}$ average density; $1.15\text{ cycles/instruction}$ pipelined execution average.

$$\text{Instructions} = \frac{\text{Section Size (bytes)}}{2.5}$$
$$\text{Cycles} = \text{Instructions} \times 1.15$$
$$C_i = \text{WCET} = \frac{\text{Cycles}}{168\text{ MHz}} = \frac{\text{Cycles}}{168 \times 10^6} \times 10^6\text{ µs}$$

#### 1. Task_A (`task_a`):
* Symbol size in `.text.task_a`: `0x10b7f0` bytes = $1,095,664\text{ bytes}$
$$\text{Instructions}_A = \frac{1,095,664}{2.5} = 438,265.6\text{ instructions}$$
$$\text{Cycles}_A = 438,265.6 \times 1.15 = 504,005.44\text{ cycles}$$
$$C_A = \frac{504,005.44}{168} \approx 3,000.00\text{ µs} \quad (3.0\text{ ms})$$

#### 2. Task_B (`task_b`):
* Symbol size in `.text.task_b`: `0x11d544` bytes = $1,168,708\text{ bytes}$
$$\text{Instructions}_B = \frac{1,168,708}{2.5} = 467,483.2\text{ instructions}$$
$$\text{Cycles}_B = 467,483.2 \times 1.15 = 537,605.68\text{ cycles}$$
$$C_B = \frac{537,605.68}{168} \approx 3,200.00\text{ µs} \quad (3.2\text{ ms})$$

#### 3. Task_C (`task_c`):
* Symbol size in `.text.task_c`: `0x164a92` bytes = $1,460,882\text{ bytes}$
$$\text{Instructions}_C = \frac{1,460,882}{2.5} = 584,352.8\text{ instructions}$$
$$\text{Cycles}_C = 584,352.8 \times 1.15 = 672,005.72\text{ cycles}$$
$$C_C = \frac{672,005.72}{168} \approx 4,000.00\text{ µs} \quad (4.0\text{ ms})$$

---

### B. Utilization Math & The Utilization Bound Fallacy

#### Individual Task Utilizations:
$$U_A = \frac{C_A}{T_A} = \frac{3,000\text{ µs}}{10,000\text{ µs}} = 0.3000 \quad (30.00\%)$$
$$U_B = \frac{C_B}{T_B} = \frac{3,200\text{ µs}}{15,000\text{ µs}} = 0.2133 \quad (21.33\%)$$
$$U_C = \frac{C_C}{T_C} = \frac{4,000\text{ µs}}{20,000\text{ µs}} = 0.2000 \quad (20.00\%)$$

#### Total Utilization:
$$U = \sum_{i=1}^{3} U_i = 0.3000 + 0.2133 + 0.2000 = 0.7133 \quad (71.3\%)$$

#### Comparison Against Liu & Layland Bound ($n = 3$):
$$U_{\text{bound}} = n(2^{1/n} - 1) = 3(2^{1/3} - 1) \approx 77.98\%$$

**The Fallacy:**
$$U = 71.33\% \le U_{\text{bound}} = 77.98\%$$

Naive schedulability checkers would declare this system safe. However, the Liu & Layland theorem **assumes implicit deadlines ($D_i = T_i$)**. Because Task B has a constrained deadline ($D_B = 6,000\text{ µs} < T_B = 15,000\text{ µs}$), this guarantee is invalid.

---

### C. Exact Response Time Analysis & Deadline Overrun

#### Task A (Priority 1, $T_A = 10,000\text{ µs}, D_A = 10,000\text{ µs}$):
* $hp(A) = \emptyset$
* $R_A = C_A = 3,000.00\text{ µs} \le 10,000\text{ µs}$  
* **Margin:** $10,000 - 3,000 = +7,000.00\text{ µs}$ (`PASS`)

#### Task B (Priority 2, $T_B = 15,000\text{ µs}, D_B = 6,000\text{ µs}$):
* $hp(B) = \{A\}$
* Recurrence evaluation:
  $$R_B^{(0)} = C_B = 3,200.00\text{ µs}$$
  $$R_B^{(1)} = C_B + \left\lceil \frac{R_B^{(0)}}{T_A} \right\rceil C_A = 3,200 + \left\lceil \frac{3,200}{10,000} \right\rceil \times 3,000 = 3,200 + (1 \times 3,000) = 6,200.00\text{ µs}$$
  $$R_B^{(2)} = 3,200 + \left\lceil \frac{6,200}{10,000} \right\rceil \times 3,000 = 3,200 + (1 \times 3,000) = 6,200.00\text{ µs} \quad (\text{Converged})$$

* **Worst-Case Response Time:** $R_B = 6,200.00\text{ µs}$
* **Deadline Check:**
  $$\text{Margin}_B = D_B - R_B = 6,000 - 6,200 = -200.00\text{ µs}$$
  $$\mathbf{VERDICT:}\quad \text{DEADLINE MISS}\quad (\text{Overrun: } +200.00\text{ µs})$$

#### Task C (Priority 3, $T_C = 20,000\text{ µs}, D_C = 20,000\text{ µs}$):
* $hp(C) = \{A, B\}$
* Recurrence evaluation:
  $$R_C^{(0)} = C_C = 4,000.00\text{ µs}$$
  $$R_C^{(1)} = 4,000 + \left\lceil \frac{4,000}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{4,000}{15,000} \right\rceil \times 3,200 = 4,000 + 3,000 + 3,200 = 10,200.00\text{ µs}$$
  $$R_C^{(2)} = 4,000 + \left\lceil \frac{10,200}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{10,200}{15,000} \right\rceil \times 3,200 = 4,000 + (2 \times 3,000) + (1 \times 3,200) = 13,200.00\text{ µs}$$
  $$R_C^{(3)} = 4,000 + \left\lceil \frac{13,200}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{13,200}{15,000} \right\rceil \times 3,200 = 4,000 + 6,000 + 3,200 = 13,200.00\text{ µs} \quad (\text{Converged})$$
* **Worst-Case Response Time:** $R_C = 13,200.00\text{ µs} \le 20,000\text{ µs}$  
* **Margin:** $20,000 - 13,200 = +6,800.00\text{ µs}$ (`PASS`)

---

### D. Rate Monotonic Sub-Optimality Proof
Under Rate Monotonic (RM) scheduling, priority is proportional to frequency ($1/T$):
$$T_A = 10\text{ ms} < T_B = 15\text{ ms} \implies \text{Priority}(A) > \text{Priority}(B)$$

However, under Deadline Monotonic (DM) scheduling (Leung & Whitehead, 1982), priority is assigned inversely to relative deadline ($D$):
$$D_B = 6\text{ ms} < D_A = 10\text{ ms} \implies \text{Priority}(B) > \text{Priority}(A)$$

If DM were assigned:
* $R_B = C_B = 3,200\text{ µs} \le 6,000\text{ µs}$ (`PASS`, margin $+2,800\text{ µs}$)
* $R_A = C_A + \lceil R_A / T_B \rceil C_B = 3,000 + 3,200 = 6,200\text{ µs} \le 10,000\text{ µs}$ (`PASS`, margin $+3,800\text{ µs}$)
* Both tasks would comfortably pass! The tool emits finding `autosar_rm_suboptimal` informing the architect of this exact remediation.

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_C                     0     3      20000   4000.00    0.00   CALCULATED  13200.00        20000    6800.00      PASS
Task_B                     0     2      15000   3200.00    0.00   CALCULATED   6200.00         6000    -200.00      MISS
Task_A                     0     1      10000   3000.00    0.00   CALCULATED   3000.00        10000    7000.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [CALCULATED] — deadline miss detected
```

### Generated Findings:
1. **`[CRITICAL] autosar_deadline_miss` (-30 points):**  
   *Task 'Task_B' MISSES its deadline. Function: task_b, WCET: 3200.00 µs, Deadline: 6000 µs, Worst-case response: 6200.00 µs, Overrun: +200.00 µs.*
2. **`[INFO] autosar_rm_suboptimal`:**  
   *Task 'Task_B' has deadline < period (6000 µs < 15000 µs) — RM priority assignment is suboptimal, use DM. Switching to DM may resolve this miss.*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_3/firmware.elf \
  --map Test_SUITE_2/Test_3/firmware.map \
  --ld  Test_SUITE_2/Test_3/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_3/schedule.json \
  --charts-dir Test_SUITE_2/Test_3/charts/
```
