# Test Case 8: EDF Processor Demand Analysis — Dense Task Set

> **Status:** `PASS`  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Dynamic Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 8 evaluates EmbedSched's implementation of **Earliest Deadline First (EDF)** scheduling theory under **constrained relative deadlines** ($D_i < T_i$).

In real-time computing literature (Baruah et al., 1990):
- For implicit-deadline tasks ($D_i = T_i$), EDF schedulability is proven if and only if utilization $U = \sum C_i/T_i \le 1.0$.
- For constrained-deadline tasks ($D_i < T_i$), the simple utilization test is **insufficient**. A system with $75\%$ utilization can fail to schedule under EDF if tasks demand bursts of computation within tight initial deadline windows.
- Schedulability can only be verified by evaluating the **Demand Bound Function** $h(L)$ at all deadline points up to the synchronous busy period.

This test proves that EmbedSched automatically detects constrained deadlines on EDF cores and activates the exact mathematical Demand Bound Function test.

---

## 2. Why It Was Performed

1. **Preventing Schedulability Blindspots:** Naive EDF analyzers only check if $\sum C_i/T_i \le 1.0$. This allows systems that will fail at runtime to pass static verification.
2. **Exact Test-Point Enumeration:** Proves that EmbedSched does not test arbitrary intervals, but systematically evaluates $h(L)$ at every exact deadline instant $L \in \{d_{i,k} \le L^*\}$.
3. **Tightest Margin Discovery:** Engineers designing high-rate sensor sampling or vision pipelines need to know exactly which time interval $L$ has the narrowest safety margin so they can size buffers and deadlines accordingly.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Three tasks scheduled on Core 0 under dynamic EDF:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | **8,000 µs (8 ms)** | `null` (EDF) | 3,000 µs (3.0 ms) | 30.0% |
| `Task_B` | 20,000 µs (20 ms) | **15,000 µs (15 ms)** | `null` (EDF) | 5,000 µs (5.0 ms) | 25.0% |
| `Task_C` | 40,000 µs (40 ms) | **30,000 µs (30 ms)** | `null` (EDF) | 8,000 µs (8.0 ms) | 20.0% |
| **Total** | — | — | — | — | **75.0%** |

Notice that every task has $D_i < T_i$.

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_8/firmware.map) at $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$):

$$\text{Instructions} = \frac{\text{Section Size (bytes)}}{2.5}$$
$$\text{Cycles} = \text{Instructions} \times 1.15$$
$$C_i = \text{WCET} = \frac{\text{Cycles}}{168\text{ MHz}} = \frac{\text{Cycles}}{168 \times 10^6} \times 10^6\text{ µs}$$

#### 1. Task_A (`task_a`):
* Symbol size in `.text.task_a`: `0x10b7f0` bytes = $1,095,664\text{ bytes}$
$$\text{Instructions}_A = \frac{1,095,664}{2.5} = 438,265.6\text{ instructions}$$
$$\text{Cycles}_A = 438,265.6 \times 1.15 = 504,005.44\text{ cycles}$$
$$C_A = \frac{504,005.44}{168} \approx 3,000.00\text{ µs} \quad (3.0\text{ ms})$$

#### 2. Task_B (`task_b`):
* Symbol size in `.text.task_b`: `0x1bdd32` bytes = $1,826,098\text{ bytes}$
$$\text{Instructions}_B = \frac{1,826,098}{2.5} = 730,439.2\text{ instructions}$$
$$\text{Cycles}_B = 730,439.2 \times 1.15 = 840,005.08\text{ cycles}$$
$$C_B = \frac{840,005.08}{168} \approx 5,000.00\text{ µs} \quad (5.0\text{ ms})$$

#### 3. Task_C (`task_c`):
* Symbol size in `.text.task_c`: `0x2c9518` bytes = $2,921,752\text{ bytes}$
$$\text{Instructions}_C = \frac{2,921,752}{2.5} = 1,168,700.8\text{ instructions}$$
$$\text{Cycles}_C = 1,168,700.8 \times 1.15 = 1,344,005.92\text{ cycles}$$
$$C_C = \frac{1,344,005.92}{168} \approx 8,000.00\text{ µs} \quad (8.0\text{ ms})$$

---

### B. Utilization Analysis

#### Task Utilizations:
$$U_A = \frac{3,000\text{ µs}}{10,000\text{ µs}} = 0.3000 \quad (30.0\%)$$
$$U_B = \frac{5,000\text{ µs}}{20,000\text{ µs}} = 0.2500 \quad (25.0\%)$$
$$U_C = \frac{8,000\text{ µs}}{40,000\text{ µs}} = 0.2000 \quad (20.0\%)$$

#### Total Utilization:
$$U = \sum_{i=1}^{3} U_i = 0.30 + 0.25 + 0.20 = 0.7500 \quad (75.0\%)$$

While $U = 75.0\% \le 100.0\%$, this test alone is **not sufficient** to guarantee schedulability because each task has a constrained deadline ($D_i < T_i$). The engine automatically invokes Processor Demand Analysis (PDA).

---

### C. Processor Demand Analysis (PDA) & Demand Bound Function $h(L)$

The Demand Bound Function $h(L)$ computes the maximum execution demand of all jobs whose arrival time and deadline both lie within an interval of length $L$:
$$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L - D_i}{T_i} \right\rfloor + 1\right) C_i$$

A constrained-deadline task set is schedulable under EDF if and only if:
$$\forall L \in \mathcal{D}, \quad h(L) \le L$$

Where $\mathcal{D} = \{k \cdot T_i + D_i \mid k \cdot T_i + D_i \le H\}$ and the hyperperiod $H = \text{LCM}(10, 20, 40) = 40\text{ ms} = 40,000\text{ µs}$.

#### Evaluation at Scheduling Test Points up to $H = 40\text{ ms}$:

1. **At $L = 8,000\text{ µs}$ (Deadline of Task A):**
   $$h(8000) = \left(\left\lfloor \frac{8-8}{10} \right\rfloor + 1\right)(3000) + 0 + 0 = 3,000\text{ µs}$$
   $$\text{Slack} = 8,000 - 3,000 = \mathbf{+5,000\text{ µs}} \quad (h(L) \le L \implies \mathbf{PASS})$$
   *(Tightest margin point in the entire task set!)*

2. **At $L = 15,000\text{ µs}$ (Deadline of Task B):**
   $$h(15000) = \left(\left\lfloor \frac{15-8}{10} \right\rfloor + 1\right)(3000) + \left(\left\lfloor \frac{15-15}{20} \right\rfloor + 1\right)(5000) + 0 = (1)(3000) + (1)(5000) = 8,000\text{ µs}$$
   $$\text{Slack} = 15,000 - 8,000 = +7,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

3. **At $L = 18,000\text{ µs}$ (Second deadline of Task A):**
   $$h(18000) = \left(\left\lfloor \frac{18-8}{10} \right\rfloor + 1\right)(3000) + (1)(5000) + 0 = (2)(3000) + 5000 = 11,000\text{ µs}$$
   $$\text{Slack} = 18,000 - 11,000 = +7,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

4. **At $L = 28,000\text{ µs}$ (Third deadline of Task A):**
   $$h(28000) = \left(\left\lfloor \frac{28-8}{10} \right\rfloor + 1\right)(3000) + (1)(5000) + 0 = (3)(3000) + 5000 = 14,000\text{ µs}$$
   $$\text{Slack} = 28,000 - 14,000 = +14,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

5. **At $L = 30,000\text{ µs}$ (Deadline of Task C):**
   $$h(30000) = (3)(3000) + \left(\left\lfloor \frac{30-15}{20} \right\rfloor + 1\right)(5000) + \left(\left\lfloor \frac{30-30}{40} \right\rfloor + 1\right)(8000) = 9000 + 5000 + 8000 = 22,000\text{ µs}$$
   $$\text{Slack} = 30,000 - 22,000 = +8,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

6. **At $L = 35,000\text{ µs}$ (Second deadline of Task B):**
   $$h(35000) = (3)(3000) + \left(\left\lfloor \frac{35-15}{20} \right\rfloor + 1\right)(5000) + (1)(8000) = 9000 + (2)(5000) + 8000 = 27,000\text{ µs}$$
   $$\text{Slack} = 35,000 - 27,000 = +8,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

7. **At $L = 38,000\text{ µs}$ (Fourth deadline of Task A):**
   $$h(38000) = (4)(3000) + (2)(5000) + (1)(8000) = 12000 + 10000 + 8000 = 30,000\text{ µs}$$
   $$\text{Slack} = 38,000 - 30,000 = +8,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

Every test point satisfies $h(L) \le L$. Therefore, the task set is mathematically guaranteed schedulable.

---

### D. Worst-Case Response Time (WCRT) Under EDF

Under EDF simulation with synchronous release at $t = 0$:
- Absolute deadlines: $d_A = 8\text{ ms}$, $d_B = 15\text{ ms}$, $d_C = 30\text{ ms}$.
- `Task_A` has the earliest deadline ($8\text{ ms}$) and executes immediately:
  $$R_A = C_A = 3,000.00\text{ µs} \le 8,000\text{ µs} \quad (\text{Margin: } +5,000.00\text{ µs})$$
- `Task_B` has the next deadline ($15\text{ ms}$) and executes after `Task_A`:
  $$R_B = C_A + C_B = 3,000 + 5,000 = 8,000.00\text{ µs} \le 15,000\text{ µs} \quad (\text{Margin: } +7,000.00\text{ µs})$$
- `Task_C` has deadline $30\text{ ms}$. Over its execution, `Task_A` releases again at $t = 10\text{ ms}$ (deadline $18\text{ ms}$) and $t = 20\text{ ms}$ (deadline $28\text{ ms}$), preempting `Task_C`:
  $$R_C = C_C + (2 \times C_A) + C_B = 8,000 + (2 \times 3,000) + 5,000 = 19,000.00\text{ µs}$$
  $$R_C = 19,000.00\text{ µs} \le 30,000\text{ µs} \quad (\text{Margin: } +11,000.00\text{ µs})$$

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0   EDF      10000   3000.00    0.00   CALCULATED   3000.00         8000    5000.00      PASS
Task_B                     0   EDF      20000   5000.00    0.00   CALCULATED   8000.00        15000    7000.00      PASS
Task_C                     0   EDF      40000   8000.00    0.00   CALCULATED  19000.00        30000   11000.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

- **Dashboard:** Core 0 utilization displayed as:  
  `[██████████████████████████████░░░░░░░░░|░] 75.0% EDF bound: 100.0% (constrained deadline) → GUARANTEED (demand analysis: h(t) <= t)`
- **Findings:** Emits `[INFO] autosar_edf_constrained_deadline` noting that Processor Demand Analysis was activated and reports the tightest margin interval ($L = 8,000\text{ µs}$, Margin: $+5,000\text{ µs}$).

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_8/firmware.elf \
  --map Test_SUITE_2/Test_8/firmware.map \
  --ld  Test_SUITE_2/Test_8/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_8/schedule.json \
  --charts-dir Test_SUITE_2/Test_8/charts/
```
