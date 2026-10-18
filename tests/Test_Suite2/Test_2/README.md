# Test Case 2: Rate Monotonic Utilization Boundary — The Tipping Point

> **Status:** `PASS` (with Schedulability Warning)  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 2 tests the classical **boundary condition of Rate Monotonic theory**. In real-time systems literature (Liu & Layland, 1973), the utilization bound test ($U \le n(2^{1/n} - 1)$) is **sufficient but not necessary**:
- If total utilization is below the bound, the system is **guaranteed** schedulable.
- If total utilization exceeds the bound, the system enters an **indeterminate region**: it may still be completely schedulable because the Liu & Layland bound is conservative for non-pathological period distributions.
- Schedulability can only be proven or disproven by running exact **Response Time Analysis (RTA)**.

Test Case 2 proves that EmbedSched correctly differentiates between the fast utilization heuristic and exact RTA, reporting **both** without prematurely aborting on a utilization bound violation.

---

## 2. Why It Was Performed

A common bug in commercial or naive real-time analysis tools is treating the Liu & Layland bound as an abort condition:
1. **Preventing Premature Failures:** Proves that EmbedSched does not raise a false `CRITICAL` failure when utilization exceeds 74.3%, but instead raises a `WARNING` and executes Joseph & Pandya's exact recurrence relation.
2. **Scannable Engineering Transparency:** Engineers must see why a 77.0% loaded system is safe. EmbedSched displays a distinctive **yellow indeterminate indicator** on the utilization bar while rendering a **green PASS verdict** on the RTA response time table.
3. **Harmonic Period Validation:** Schedulability beyond the Liu & Layland bound is common in production automotive firmware where periods are harmonic (10ms, 20ms, 40ms, 80ms, 160ms). The tool demonstrates that harmonic task sets can run safely up to 100% utilization.

---

## 3. Configuration & Task Set

### Task Configuration (`schedule.json`)
Five harmonic tasks running on Core 0:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | 2,000 µs (2.0 ms) | 20.0% |
| `Task_B` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | 3,000 µs (3.0 ms) | 15.0% |
| `Task_C` | 40,000 µs (40 ms) | 40,000 µs (40 ms) | 3 | 6,000 µs (6.0 ms) | 15.0% |
| `Task_D` | 80,000 µs (80 ms) | 80,000 µs (80 ms) | 4 | 12,000 µs (12.0 ms) | 15.0% |
| `Task_E` | 160,000 µs (160 ms) | 160,000 µs (160 ms) | 5 (Lowest) | 19,200 µs (19.2 ms) | 12.0% |
| **Total** | — | — | — | — | **77.0%** |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_2/firmware.map) to extract symbol sizes for each task located in `SRAM1` ($0\text{ wait states}$ on STM32F407):

* **Target Core:** ARM Cortex-M4 running at $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$).
* **Thumb-2 Instruction Model:** $2.5\text{ bytes/instruction}$ average density; $1.15\text{ cycles/instruction}$ pipelined execution average.

$$\text{Instructions} = \frac{\text{Section Size (bytes)}}{2.5}$$
$$\text{Cycles} = \text{Instructions} \times 1.15$$
$$C_i = \text{WCET} = \frac{\text{Cycles}}{168\text{ MHz}} = \frac{\text{Cycles}}{168 \times 10^6} \times 10^6\text{ µs}$$

#### 1. Task_A (`task_a`):
* Symbol size in `.text.task_a`: `0xb254e` bytes = $730,446\text{ bytes}$
$$\text{Instructions}_A = \frac{730,446}{2.5} = 292,178.4\text{ instructions}$$
$$\text{Cycles}_A = 292,178.4 \times 1.15 = 336,005.16\text{ cycles}$$
$$C_A = \frac{336,005.16}{168} \approx 2,000.00\text{ µs} \quad (2.0\text{ ms})$$

#### 2. Task_B (`task_b`):
* Symbol size in `.text.task_b`: `0x10b7f0` bytes = $1,095,664\text{ bytes}$
$$\text{Instructions}_B = \frac{1,095,664}{2.5} = 438,265.6\text{ instructions}$$
$$\text{Cycles}_B = 438,265.6 \times 1.15 = 504,005.44\text{ cycles}$$
$$C_B = \frac{504,005.44}{168} \approx 3,000.00\text{ µs} \quad (3.0\text{ ms})$$

#### 3. Task_C (`task_c`):
* Symbol size in `.text.task_c`: `0x216fd4` bytes = $2,191,316\text{ bytes}$
$$\text{Instructions}_C = \frac{2,191,316}{2.5} = 876,526.4\text{ instructions}$$
$$\text{Cycles}_C = 876,526.4 \times 1.15 = 1,008,005.36\text{ cycles}$$
$$C_C = \frac{1,008,005.36}{168} \approx 6,000.00\text{ µs} \quad (6.0\text{ ms})$$

#### 4. Task_D (`task_d`):
* Symbol size in `.text.task_d`: `0x42df9c` bytes = $4,382,620\text{ bytes}$
$$\text{Instructions}_D = \frac{4,382,620}{2.5} = 1,753,048.0\text{ instructions}$$
$$\text{Cycles}_D = 1,753,048.0 \times 1.15 = 2,016,005.20\text{ cycles}$$
$$C_D = \frac{2,016,005.20}{168} \approx 12,000.00\text{ µs} \quad (12.0\text{ ms})$$

#### 5. Task_E (`task_e`):
* Symbol size in `.text.task_e`: `0x6aff5a` bytes = $7,012,186\text{ bytes}$
$$\text{Instructions}_E = \frac{7,012,186}{2.5} = 2,804,874.4\text{ instructions}$$
$$\text{Cycles}_E = 2,804,874.4 \times 1.15 = 3,225,605.56\text{ cycles}$$
$$C_E = \frac{3,225,605.56}{168} \approx 19,200.00\text{ µs} \quad (19.2\text{ ms})$$

---

### B. Utilization Math & Indeterminate Zone Analysis

#### Individual Task Utilizations:
$$U_A = \frac{C_A}{T_A} = \frac{2,000\text{ µs}}{10,000\text{ µs}} = 0.2000 \quad (20.0\%)$$
$$U_B = \frac{C_B}{T_B} = \frac{3,000\text{ µs}}{20,000\text{ µs}} = 0.1500 \quad (15.0\%)$$
$$U_C = \frac{C_C}{T_C} = \frac{6,000\text{ µs}}{40,000\text{ µs}} = 0.1500 \quad (15.0\%)$$
$$U_D = \frac{C_D}{T_D} = \frac{12,000\text{ µs}}{80,000\text{ µs}} = 0.1500 \quad (15.0\%)$$
$$U_E = \frac{C_E}{T_E} = \frac{19,200\text{ µs}}{160,000\text{ µs}} = 0.1200 \quad (12.0\%)$$

#### System Total Utilization:
$$U = \sum_{i=1}^{5} U_i = 0.20 + 0.15 + 0.15 + 0.15 + 0.12 = 0.7700 \quad (77.0\%)$$

#### Comparison Against Liu & Layland Bound ($n = 5$):
$$U_{\text{bound}} = n(2^{1/n} - 1) = 5(2^{1/5} - 1) = 5(1.148698 - 1) \approx 74.35\%$$

**Evaluation:**
$$U = 77.0\% > U_{\text{bound}} = 74.35\%$$

Because $74.35\% < U \le 100.0\%$, the system is in the **indeterminate region**. The Liu & Layland utilization test cannot guarantee schedulability, triggering warning `autosar_utilization_warning` (-15 pts deduction). Schedulability must be resolved strictly through exact Response Time Analysis.

---

### C. Exact Response Time Analysis (Joseph & Pandya Recurrence)

The recurrence relation calculates worst-case response time $R_i$:
$$R_i^{(0)} = C_i$$
$$R_i^{(k+1)} = C_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### Task A (Priority 1, $T_A = 10\text{ ms}$, $D_A = 10\text{ ms}$):
* $hp(A) = \emptyset$
* $R_A = C_A = 2,000\text{ µs} \le 10,000\text{ µs}$  
* **Margin:** $10,000 - 2,000 = +8,000\text{ µs}$ (`PASS`)

#### Task B (Priority 2, $T_B = 20\text{ ms}$, $D_B = 20\text{ ms}$):
* $hp(B) = \{A\}$
* $R_B^{(0)} = 3,000\text{ µs}$
* $R_B^{(1)} = 3,000 + \lceil 3,000 / 10,000 \rceil \times 2,000 = 3,000 + 1 \times 2,000 = 5,000\text{ µs}$
* $R_B^{(2)} = 3,000 + \lceil 5,000 / 10,000 \rceil \times 2,000 = 3,000 + 1 \times 2,000 = 5,000\text{ µs}$ (Converged)
* $R_B = 5,000\text{ µs} \le 20,000\text{ µs}$  
* **Margin:** $20,000 - 5,000 = +15,000\text{ µs}$ (`PASS`)

#### Task C (Priority 3, $T_C = 40\text{ ms}$, $D_C = 40\text{ ms}$):
* $hp(C) = \{A, B\}$
* $R_C^{(0)} = 6,000\text{ µs}$
* $R_C^{(1)} = 6,000 + \lceil 6,000 / 10,000 \rceil \times 2,000 + \lceil 6,000 / 20,000 \rceil \times 3,000 = 6,000 + 2,000 + 3,000 = 11,000\text{ µs}$
* $R_C^{(2)} = 6,000 + \lceil 11,000 / 10,000 \rceil \times 2,000 + \lceil 11,000 / 20,000 \rceil \times 3,000 = 6,000 + (2 \times 2,000) + (1 \times 3,000) = 13,000\text{ µs}$
* $R_C^{(3)} = 6,000 + \lceil 13,000 / 10,000 \rceil \times 2,000 + \lceil 13,000 / 20,000 \rceil \times 3,000 = 6,000 + 4,000 + 3,000 = 13,000\text{ µs}$ (Converged)
* $R_C = 13,000\text{ µs} \le 40,000\text{ µs}$  
* **Margin:** $40,000 - 13,000 = +27,000\text{ µs}$ (`PASS`)

#### Task D (Priority 4, $T_D = 80\text{ ms}$, $D_D = 80\text{ ms}$):
* $hp(D) = \{A, B, C\}$
* $R_D^{(0)} = 12,000\text{ µs}$
* $R_D^{(1)} = 12,000 + \lceil 12,000/10,000 \rceil \times 2,000 + \lceil 12,000/20,000 \rceil \times 3,000 + \lceil 12,000/40,000 \rceil \times 6,000 = 12,000 + 4,000 + 3,000 + 6,000 = 25,000\text{ µs}$
* $R_D^{(2)} = 12,000 + \lceil 25,000/10,000 \rceil \times 2,000 + \lceil 25,000/20,000 \rceil \times 3,000 + \lceil 25,000/40,000 \rceil \times 6,000 = 12,000 + (3 \times 2,000) + (2 \times 3,000) + (1 \times 6,000) = 30,000\text{ µs}$
* $R_D^{(3)} = 12,000 + \lceil 30,000/10,000 \rceil \times 2,000 + \lceil 30,000/20,000 \rceil \times 3,000 + \lceil 30,000/40,000 \rceil \times 6,000 = 12,000 + 6,000 + 6,000 + 6,000 = 30,000\text{ µs}$ (Converged)
* $R_D = 30,000\text{ µs} \le 80,000\text{ µs}$  
* **Margin:** $80,000 - 30,000 = +50,000\text{ µs}$ (`PASS`)

#### Task E (Priority 5, $T_E = 160\text{ ms}$, $D_E = 160\text{ ms}$):
* $hp(E) = \{A, B, C, D\}$
* $R_E^{(0)} = 19,200\text{ µs}$
* $R_E^{(1)} = 19,200 + \lceil 19,200/10,000 \rceil \times 2,000 + \lceil 19,200/20,000 \rceil \times 3,000 + \lceil 19,200/40,000 \rceil \times 6,000 + \lceil 19,200/80,000 \rceil \times 12,000 = 19,200 + 4,000 + 3,000 + 6,000 + 12,000 = 44,200\text{ µs}$
* $R_E^{(2)} = 19,200 + \lceil 44,200/10,000 \rceil \times 2,000 + \lceil 44,200/20,000 \rceil \times 3,000 + \lceil 44,200/40,000 \rceil \times 6,000 + \lceil 44,200/80,000 \rceil \times 12,000 = 19,200 + (5 \times 2,000) + (3 \times 3,000) + (2 \times 6,000) + (1 \times 12,000) = 62,200\text{ µs}$
* $R_E^{(3)} = 19,200 + \lceil 62,200/10,000 \rceil \times 2,000 + \lceil 62,200/20,000 \rceil \times 3,000 + \lceil 62,200/40,000 \rceil \times 6,000 + \lceil 62,200/80,000 \rceil \times 12,000 = 19,200 + (7 \times 2,000) + (4 \times 3,000) + (2 \times 6,000) + (1 \times 12,000) = 69,200\text{ µs}$
* $R_E^{(4)} = 19,200 + \lceil 69,200/10,000 \rceil \times 2,000 + \lceil 69,200/20,000 \rceil \times 3,000 + \lceil 69,200/40,000 \rceil \times 6,000 + \lceil 69,200/80,000 \rceil \times 12,000 = 19,200 + 14,000 + 12,000 + 12,000 + 12,000 = 69,200\text{ µs}$ (Converged)
* $R_E = 69,200\text{ µs} \le 160,000\text{ µs}$  
* **Margin:** $160,000 - 69,200 = +90,800\text{ µs}$ (`PASS`)

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_E                     0     5     160000  19200.00    0.00   CALCULATED  69200.00       160000   90800.00      PASS
Task_D                     0     4      80000  12000.00    0.00   CALCULATED  30000.00        80000   50000.00      PASS
Task_C                     0     3      40000   6000.00    0.00   CALCULATED  13000.00        40000   27000.00      PASS
Task_B                     0     2      20000   3000.00    0.00   CALCULATED   5000.00        20000   15000.00      PASS
Task_A                     0     1      10000   2000.00    0.00   CALCULATED   2000.00        10000    8000.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

- **Dashboard:** Core 0 utilization bar shows **YELLOW INDETERMINATE** ($77.0\%$).
- **Findings:** Emits `[WARNING] autosar_utilization_warning` with exact explanation:  
  *Utilization exceeds Liu & Layland bound (77.0% > 74.3%) — system is in indeterminate region. Exact RTA confirms all tasks meet deadlines.*
- **Overall Verdict:** `PASS [CALCULATED]`

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_2/firmware.elf \
  --map Test_SUITE_2/Test_2/firmware.map \
  --ld  Test_SUITE_2/Test_2/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_2/schedule.json \
  --charts-dir Test_SUITE_2/Test_2/charts/
```
