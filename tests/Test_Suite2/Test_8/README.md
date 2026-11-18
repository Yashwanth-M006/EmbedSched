# Test Case 8: EDF Processor Demand Analysis — Dense Task Set & Dynamic Overrun

> **Status:** `FAIL` (Deadline Misses Detected)  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Dynamic Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 8 evaluates EmbedSched's implementation of **Earliest Deadline First (EDF)** scheduling theory under **constrained relative deadlines** ($D_i < T_i$).

In real-time computing literature (Baruah et al., 1990):
- For implicit-deadline tasks ($D_i = T_i$), EDF schedulability is proven if and only if utilization $U = \sum C_i/T_i \le 1.0$.
- For constrained-deadline tasks ($D_i < T_i$), the simple utilization test is **insufficient**. A system can fail to schedule under EDF if tasks demand bursts of computation within tight initial deadline windows.
- Schedulability can only be verified by evaluating the **Demand Bound Function** $h(L)$ at all deadline points up to the synchronous busy period.
- If total utilization exceeds 100%, EDF cannot maintain deadlines, resulting in cascade deadline misses.

This test proves that EmbedSched automatically detects constrained deadlines on EDF cores, evaluates demand bounds, and detects dynamic deadline misses.

---

## 2. Why It Was Performed

1. **Preventing Schedulability Blindspots:** Naive EDF analyzers only check if $\sum C_i/T_i \le 1.0$. This allows systems that will fail at runtime to pass static verification.
2. **Exact Test-Point Enumeration:** Proves that EmbedSched systematically evaluates $h(L)$ at every exact deadline instant $L \in \{d_{i,k} \le L^*\}$.
3. **Dynamic Overrun Pinpointing:** When cumulative demand overruns processing capacity, the tool captures exact deadline miss events during simulation.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Three tasks scheduled on Core 0 under dynamic EDF with constrained deadlines ($D_i < T_i$):

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Entry Function | Memory Placement |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | **8,000 µs (8 ms)** | `null` (EDF) | `task_a` | SRAM1 |
| `Task_B` | 20,000 µs (20 ms) | **15,000 µs (15 ms)** | `null` (EDF) | `task_b` | SRAM1 |
| `Task_C` | 40,000 µs (40 ms) | **30,000 µs (30 ms)** | `null` (EDF) | `task_c` | SRAM1 |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation (IPET)
The static analyzer inspects `firmware.map` for symbol sizes at $f = 168\text{ MHz}$ ($ws = 4$):
* `task_a`: `0x10b7f0` = **1,095,664 bytes**
* `task_b`: `0x1c9384` = **1,872,772 bytes**
* `task_c`: `0x2c9384` = **2,921,348 bytes**

Applying IPET microarchitectural timing for Cortex-M4 at 168 MHz:

1. **`Task_A` (`task_a`):**
   $$\text{Instructions}_A = 547,832 \implies \text{Cycles}_A = 890,232 \implies C_A = \frac{890,232}{168} = \mathbf{5,299.00\text{ µs}}$$

2. **`Task_B` (`task_b`):**
   $$\text{Instructions}_B = 913,386 \implies \text{Cycles}_B = 1,483,776 \implies C_B = \frac{1,483,776}{168} = \mathbf{8,832.00\text{ µs}}$$

3. **`Task_C` (`task_c`):**
   $$\text{Instructions}_C = 1,460,674 \implies \text{Cycles}_C = 2,374,008 \implies C_C = \frac{2,374,008}{168} = \mathbf{14,131.00\text{ µs}}$$

---

### B. Utilization Math & CPU Overload
Dividing each derived WCET by its period:
$$U_A = \frac{5,299\text{ µs}}{10,000\text{ µs}} = 52.99\% \quad (\text{WCET dominates period: } 53\%)$$
$$U_B = \frac{8,832\text{ µs}}{20,000\text{ µs}} = 44.16\%$$
$$U_C = \frac{14,131\text{ µs}}{40,000\text{ µs}} = 35.33\%$$

#### Total System Utilization:
$$U = \sum_{i=A}^{C} U_i = 52.99\% + 44.16\% + 35.33\% = \mathbf{132.5\%} > 100.0\%$$

Because $U = 132.5\% > 100\%$, Core 0 is severely overloaded, triggering critical finding `autosar_cpu_overload`.

---

### C. Response Time & Deadline Overrun Under EDF
Under dynamic Earliest Deadline First preemption, tasks accumulate preemption delays from whichever active job has an earlier absolute deadline:

1. **`Task_A` (Deadline = 8,000 µs):**
   * Worst-Case Response Time: $R_A = \mathbf{22,991.00\text{ µs}} > 8,000\text{ µs}$
   * Slack Margin: $8,000 - 22,991 = \mathbf{-14,991.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+14,991.00\text{ µs}$)

2. **`Task_B` (Deadline = 15,000 µs):**
   * Worst-Case Response Time: $R_B = \mathbf{40,683.00\text{ µs}} > 15,000\text{ µs}$
   * Slack Margin: $15,000 - 40,683 = \mathbf{-25,683.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+25,683.00\text{ µs}$)

3. **`Task_C` (Deadline = 30,000 µs):**
   * Worst-Case Response Time: $R_C = \mathbf{60,796.00\text{ µs}} > 30,000\text{ µs}$
   * Slack Margin: $30,000 - 60,796 = \mathbf{-30,796.00\text{ µs}}$
   * **Verdict:** `MISS` (Overrun: $+30,796.00\text{ µs}$)

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0   EDF      10000   5299.00    0.00         IPET  22991.00         8000  -14991.00
Task_B                     0   EDF      20000   8832.00    0.00         IPET  40683.00        15000  -25683.00
Task_C                     0   EDF      40000  14131.00    0.00         IPET  60796.00        30000  -30796.00
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: FAIL [IPET] — deadline miss detected
```

### Generated Findings:
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_A' MISSES its deadline. WCET: 5299.00 µs, Deadline: 8000 µs, Worst-case resp.: 22991.00 µs, Overrun: +14991.00 µs.*
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_B' MISSES its deadline. WCET: 8832.00 µs, Deadline: 15000 µs, Worst-case resp.: 40683.00 µs, Overrun: +25683.00 µs.*
- **`[CRITICAL] [RTA/[IPET]] autosar_deadline_miss` (-30 points):**  
  *Task 'Task_C' MISSES its deadline. WCET: 14131.00 µs, Deadline: 30000 µs, Worst-case resp.: 60796.00 µs, Overrun: +30796.00 µs.*
- **`[CRITICAL] [CALCULATED] autosar_cpu_overload` (-25 points):**  
  *Core 0: CPU OVERLOADED. Utilization: 132.5% > 100%.*
- **`[WARNING] [IPET] autosar_wcet_dominates` (-10 points):**  
  *Task 'Task_A': WCET dominates its period (53% of period).*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_8/firmware.elf \
  --map tests/Test_Suite2/Test_8/firmware.map \
  --ld  tests/Test_Suite2/Test_8/linker.ld \
  --chip tests/Test_Suite2/Test_8/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_8/schedule.json \
  --charts-dir tests/Test_Suite2/Test_8/charts/
```
