# Test Case 3: Genuine Deadline Miss — RTA Detects It

> **Status:** `FAIL` (Deadline Misses Detected)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 3 represents the **critical safety failure mode**: a task set where tasks violate hard real-time deadlines under preemption and heavy workload.

It demonstrates:
- Exact recurrence calculation for tasks with **constrained relative deadlines** ($D_i < T_i$).
- Detection of **Rate Monotonic sub-optimality**: when $D_i < T_i$, assigning priority strictly by period ($T$) instead of deadline ($D$) is provably suboptimal (Deadline Monotonic should be used).
- Prominent rendering of **red deadline overrun bars** in the Response Time chart, deadline miss indicators on the Gantt chart, and `CRITICAL` findings in the safety audit.

---

## 2. Why It Was Performed

1. **Safety-Critical Verification:** In automotive powertrain and braking ECUs (ISO 26262 ASIL-D), a task missing a 6 ms deadline can cause control loop divergence. The analyzer must reliably catch this at compile-time before flashing hardware.
2. **Exposing Constrained Deadline Violations:** Tasks with $D < T$ face severe preemption hazards that standard period-based utilization bounds cannot protect against.
3. **Actionable Remediation Guidance:** The tool must not merely report an error; it must advise the architect on the root cause (switching from RM to Deadline Monotonic, lowering WCET, or moving hot paths to zero-wait-state memory).

---

## 3. Configuration & Task Set

### Task Configuration (`schedule.json`)
Three tasks on Core 0 where `Task_B` has a constrained deadline ($D_B = 6,000\text{ µs} < T_B = 15,000\text{ µs}$):

| Task Name | Period ($T$) | Deadline ($D$) | Priority (RM) | Entry Function | Memory Placement |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | `task_a` | SRAM1 |
| `Task_B` | 15,000 µs (15 ms) | **6,000 µs (6.0 ms)** | 2 | `task_b` | SRAM1 |
| `Task_C` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 3 (Lowest) | `task_c` | SRAM1 |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The static analyzer inspects `firmware.map` to extract symbol sizes for each task in `SRAM1`:
* `task_a`: `0x10b7f0` = **1,095,664 bytes**
* `task_b`: `0x11d544` = **1,168,708 bytes**
* `task_c`: `0x164a92` = **1,460,882 bytes**

Under IPET microarchitectural timing for ARM Cortex-M4 at 168 MHz ($ws = 4$):

1. **`Task_A` (`task_a`):**
   $$\text{Instructions}_A = 547,832 \implies \text{Cycles}_A = 890,232 \implies C_A = \frac{890,232}{168} = \mathbf{5,299.00\text{ µs}}$$

2. **`Task_B` (`task_b`):**
   $$\text{Instructions}_B = 584,354 \implies \text{Cycles}_B = 949,536 \implies C_B = \frac{949,536}{168} = \mathbf{5,652.00\text{ µs}}$$

3. **`Task_C` (`task_c`):**
   $$\text{Instructions}_C = 730,441 \implies \text{Cycles}_C = 1,186,920 \implies C_C = \frac{1,186,920}{168} = \mathbf{7,065.00\text{ µs}}$$

---

### B. Utilization Math & CPU Overload

#### Individual Task Utilizations:
$$U_A = \frac{C_A}{T_A} = \frac{5,299\text{ µs}}{10,000\text{ µs}} = 52.99\% \quad (\text{WCET dominates period: } 53\%)$$
$$U_B = \frac{C_B}{T_B} = \frac{5,652\text{ µs}}{15,000\text{ µs}} = 37.68\%$$
$$U_C = \frac{C_C}{T_C} = \frac{7,065\text{ µs}}{20,000\text{ µs}} = 35.33\%$$

#### Core 0 Total Utilization:
$$U = \sum_{i=A}^{C} U_i = 52.99\% + 37.68\% + 35.33\% = \mathbf{126.0\%} > 100\%$$

Because $U = 126.0\% > 100\%$, the CPU is overloaded, triggering critical finding `autosar_cpu_overload`.

---

### C. Exact Response Time Analysis & Deadline Overrun

#### Task A (Priority 1, $T_A = 10,000\text{ µs}, D_A = 10,000\text{ µs}$):
* $hp(A) = \emptyset$
* $R_A = C_A = \mathbf{5,299.00\text{ µs}} \le 10,000\text{ µs}$  
* **Slack Margin:** $10,000 - 5,299 = \mathbf{+4,701.00\text{ µs}}$ (`PASS`)

#### Task B (Priority 2, $T_B = 15,000\text{ µs}, D_B = 6,000\text{ µs}$):
* $hp(B) = \{A\}$
* Recurrence evaluation:
  $$R_B^{(0)} = C_B = 5,652.00\text{ µs}$$
  $$R_B^{(1)} = C_B + \left\lceil \frac{R_B^{(0)}}{T_A} \right\rceil C_A = 5,652 + \left\lceil \frac{5,652}{10,000} \right\rceil \times 5,299 = 5,652 + (1 \times 5,299) = \mathbf{10,951.00\text{ µs}}\quad (\text{Converged})$$
* **Worst-Case Response Time:** $R_B = 10,951.00\text{ µs}$
* **Deadline Check:**
  $$\text{Margin}_B = D_B - R_B = 6,000 - 10,951 = \mathbf{-4,951.00\text{ µs}}$$
  $$\mathbf{VERDICT:}\quad \text{DEADLINE MISS}\quad (\text{Overrun: } +4,951.00\text{ µs})$$

#### Task C (Priority 3, $T_C = 20,000\text{ µs}, D_C = 20,000\text{ µs}$):
* $hp(C) = \{A, B\}$
* Recurrence evaluation under preemption from $A$ and $B$:
  $$R_C = \mathbf{28,967.00\text{ µs}} > 20,000\text{ µs}$$
* **Deadline Check:**
  $$\text{Margin}_C = D_C - R_C = 20,000 - 28,967 = \mathbf{-8,967.00\text{ µs}}$$
  $$\mathbf{VERDICT:}\quad \text{DEADLINE MISS}\quad (\text{Overrun: } +8,967.00\text{ µs})$$

---

### D. Rate Monotonic Sub-Optimality
Under Rate Monotonic (RM) scheduling, priority is proportional to frequency ($1/T$):
$$T_A = 10\text{ ms} < T_B = 15\text{ ms} \implies \text{Priority}(A) > \text{Priority}(B)$$

However, under Deadline Monotonic (DM) scheduling (Leung & Whitehead, 1982), priority is assigned inversely to relative deadline ($D$):
$$D_B = 6\text{ ms} < D_A = 10\text{ ms} \implies \text{Priority}(B) > \text{Priority}(A)$$

Because Task B has a constrained deadline, RM priority assignment is suboptimal. The tool emits finding `autosar_rm_suboptimal` informing the architect to adopt Deadline Monotonic or reduce WCET.

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0     1      10000   5299.00    0.00         IPET   5299.00        10000    4701.00
Task_B                     0     2      15000   5652.00    0.00         IPET  10951.00         6000   -4951.00
Task_C                     0     3      20000   7065.00    0.00         IPET  28967.00        20000   -8967.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [IPET] — deadline miss detected
```

### Generated Findings:
1. **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
   *Task 'Task_B' MISSES its deadline. Function: task_b, WCET: 5652.00 µs [IPET], Deadline: 6000 µs, Worst-case resp.: 10951.00 µs, Overrun: +4951.00 µs.*
2. **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
   *Task 'Task_C' MISSES its deadline. Function: task_c, WCET: 7065.00 µs [IPET], Deadline: 20000 µs, Worst-case resp.: 28967.00 µs, Overrun: +8967.00 µs.*
3. **`[CRITICAL] [CALCULATED] autosar_cpu_overload` (-25 points):**  
   *Core 0: CPU OVERLOADED. Utilization: 126.0% > 100%.*
4. **`[WARNING] [IPET] autosar_wcet_dominates` (-10 points):**  
   *Task 'Task_A': WCET dominates its period (53% of period).*
5. **`[INFO] [STATIC] autosar_rm_suboptimal`:**  
   *Task 'Task_B' has deadline < period (6000 µs < 15000 µs) — RM priority assignment is suboptimal, use DM.*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_3/firmware.elf \
  --map tests/Test_Suite2/Test_3/firmware.map \
  --ld  tests/Test_Suite2/Test_3/linker.ld \
  --chip tests/Test_Suite2/Test_3/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_3/schedule.json \
  --charts-dir tests/Test_Suite2/Test_3/charts/
```
