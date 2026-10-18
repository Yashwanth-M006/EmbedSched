# Test Case 9: Pathological Hyperperiod — LCM Explosion Protection

> **Status:** `PASS` (with Hyperperiod Warning)  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 9 tests **algorithmic resilience and memory safety** against non-harmonic task configurations.

In cyclic and discrete-event schedulers, the simulation timeline spans exactly one **Hyperperiod**, which is the Least Common Multiple (LCM) of all task periods:
$$\text{Hyperperiod} = \text{LCM}(T_1, T_2, \dots, T_n)$$

When periods are prime or pairwise co-prime, the hyperperiod experiences **combinatorial explosion**:
$$\text{LCM}(7, 11, 13, 17, 19)\text{ ms} = \mathbf{323,323\text{ ms}}\ (323.323\text{ seconds / 5.39 minutes})$$

Simulating 323.3 seconds of microsecond-level execution would generate over **150,000,000 event objects**, causing naive simulators to crash with out-of-memory errors or hang CI pipelines indefinitely.

This test proves that EmbedSched:
1. Detects hyperperiod explosion before allocating simulation heaps.
2. Caps the discrete-event simulation window safely at 200 ms and renders a **representative 30 ms execution window**.
3. Relies on **purely analytical Response Time Analysis (RTA)** for the schedulability verdict, which solves Joseph & Pandya's recurrence in milliseconds regardless of hyperperiod size.
4. Emits a transparent warning explaining the capped simulation window.

---

## 2. Why It Was Performed

1. **CI Pipeline Immunity:** A build tool running in automated pipelines must be completely resilient against pathological inputs. It must never freeze, hang, or consume unbounded RAM.
2. **Separating Simulation from Analytical Proof:** Proves that in EmbedSched, the schedulability verdict is **not** dependent on simulation. RTA is an analytical proof; simulation is an illustrative visual inspection tool.
3. **Graceful Degradation:** Demonstrates that the tool provides maximum possible utility (rendering the first 30 ms so developers can still inspect initial preemption dynamics) rather than crashing or outputting nothing.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Five tasks with co-prime prime-millisecond periods:

| Task Name | Period ($T$) | Deadline ($D$) | Priority (RM) | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_A` | 7,000 µs (7 ms) | 7,000 µs (7 ms) | 1 (Highest) | 60.00 µs | 0.86% |
| `Task_B` | 11,000 µs (11 ms) | 11,000 µs (11 ms) | 2 | 60.00 µs | 0.55% |
| `Task_C` | 13,000 µs (13 ms) | 13,000 µs (13 ms) | 3 | 60.00 µs | 0.46% |
| `Task_D` | 17,000 µs (17 ms) | 17,000 µs (17 ms) | 4 | 60.00 µs | 0.35% |
| `Task_E` | 19,000 µs (19 ms) | 19,000 µs (19 ms) | 5 (Lowest) | 60.00 µs | 0.32% |
| **Total** | — | — | — | — | **2.53%** |

$$\text{Hyperperiod} = \text{LCM}(7, 11, 13, 17, 19) = 323,323,000\text{ µs} = 323,323\text{ ms}$$

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_9/firmware.map) at $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$):

Each task function (`task_a`, `task_b`, `task_c`, `task_d`, `task_e`) occupies identical size in `SRAM1`:
* Symbol size: `0x54f8` bytes = $21,752\text{ bytes}$
$$\text{Instructions} = \frac{21,752}{2.5} = 8,700.8\text{ instructions}$$
$$\text{Cycles} = 8,700.8 \times 1.15 = 10,005.92\text{ cycles}$$
$$C_i = \text{WCET} = \frac{10,005.92}{168\text{ MHz}} \approx 59.56\text{ µs} \approx 60.00\text{ µs}$$

### B. Hyperperiod LCM Math
Because 7, 11, 13, 17, and 19 are all pairwise prime:
$$\text{LCM}(7, 11, 13, 17, 19) = 7 \times 11 \times 13 \times 17 \times 19 = 323,323\text{ ms} = 323.323\text{ seconds}$$

Threshold in [`analysis/scheduler_sim.py`](file:///e:/firmware_analyzer/analysis/scheduler_sim.py):
$$\text{Hyperperiod} = 323,323\text{ ms} > \text{Threshold}_{\text{sim}} (200\text{ ms})$$
The simulation timeline caps at a representative 30 ms window to prevent out-of-memory lockups, while exact schedulability is resolved through analytical RTA.

### C. Utilization Analysis
$$U_A = \frac{60\text{ µs}}{7,000\text{ µs}} = 0.00857 \quad (0.86\%)$$
$$U_B = \frac{60\text{ µs}}{11,000\text{ µs}} = 0.00545 \quad (0.55\%)$$
$$U_C = \frac{60\text{ µs}}{13,000\text{ µs}} = 0.00462 \quad (0.46\%)$$
$$U_D = \frac{60\text{ µs}}{17,000\text{ µs}} = 0.00353 \quad (0.35\%)$$
$$U_E = \frac{60\text{ µs}}{19,000\text{ µs}} = 0.00316 \quad (0.32\%)$$
$$U = \sum_{i=1}^{5} U_i \approx 0.0253 \quad (2.53\% \approx 2.5\%)$$

Liu & Layland bound for $n = 5$:
$$U_{\text{bound}} = 5(2^{1/5} - 1) \approx 74.35\%$$
$$U = 2.5\% \ll U_{\text{bound}} = 74.3\% \implies \mathbf{GUARANTEED\ SCHEDULABLE}$$

---

### D. Exact Response Time Analysis (Instant Analytical Convergence)

Even though simulating the hyperperiod would require tracking hundreds of thousands of events, exact RTA converges in only 2 iterations for each task:

#### 1. Task A (Priority 1, $T = 7,000\text{ µs}, D = 7,000\text{ µs}$):
* $hp(A) = \emptyset$
* $R_A = C_A = 60.00\text{ µs} \le 7,000\text{ µs}$  
* **Margin:** $7,000 - 60 = +6,940.00\text{ µs}$ (`PASS`)

#### 2. Task B (Priority 2, $T = 11,000\text{ µs}, D = 11,000\text{ µs}$):
* $hp(B) = \{A\}$
* $R_B^{(0)} = 60.00\text{ µs}$
* $R_B^{(1)} = 60.00 + \left\lceil \frac{60}{7000} \right\rceil \times 60 = 60 + 60 = 120.00\text{ µs}$
* $R_B^{(2)} = 60.00 + \left\lceil \frac{120}{7000} \right\rceil \times 60 = 60 + 60 = 120.00\text{ µs} \quad (\text{Converged})$
* **Margin:** $11,000 - 120 = +10,880.00\text{ µs}$ (`PASS`)

#### 3. Task C (Priority 3, $T = 13,000\text{ µs}, D = 13,000\text{ µs}$):
* $hp(C) = \{A, B\}$
* $R_C^{(0)} = 60.00\text{ µs}$
* $R_C^{(1)} = 60.00 + \left\lceil \frac{60}{7000} \right\rceil \times 60 + \left\lceil \frac{60}{11000} \right\rceil \times 60 = 60 + 60 + 60 = 180.00\text{ µs}$
* $R_C^{(2)} = 60.00 + \left\lceil \frac{180}{7000} \right\rceil \times 60 + \left\lceil \frac{180}{11000} \right\rceil \times 60 = 180.00\text{ µs} \quad (\text{Converged})$
* **Margin:** $13,000 - 180 = +12,820.00\text{ µs}$ (`PASS`)

#### 4. Task D (Priority 4, $T = 17,000\text{ µs}, D = 17,000\text{ µs}$):
* $hp(D) = \{A, B, C\}$
* $R_D^{(0)} = 60.00\text{ µs}$
* $R_D^{(1)} = 60.00 + 3 \times 60.00 = 240.00\text{ µs}$
* $R_D^{(2)} = 60.00 + \left\lceil \frac{240}{7000} \right\rceil(60) + \left\lceil \frac{240}{11000} \right\rceil(60) + \left\lceil \frac{240}{13000} \right\rceil(60) = 240.00\text{ µs} \quad (\text{Converged})$
* **Margin:** $17,000 - 240 = +16,760.00\text{ µs}$ (`PASS`)

#### 5. Task E (Priority 5, $T = 19,000\text{ µs}, D = 19,000\text{ µs}$):
* $hp(E) = \{A, B, C, D\}$
* $R_E^{(0)} = 60.00\text{ µs}$
* $R_E^{(1)} = 60.00 + 4 \times 60.00 = 300.00\text{ µs}$
* $R_E^{(2)} = 60.00 + \left\lceil \frac{300}{7000} \right\rceil(60) + \left\lceil \frac{300}{11000} \right\rceil(60) + \left\lceil \frac{300}{13000} \right\rceil(60) + \left\lceil \frac{300}{17000} \right\rceil(60) = 300.00\text{ µs} \quad (\text{Converged})$
* **Margin:** $19,000 - 300 = +18,700.00\text{ µs}$ (`PASS`)

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_E                     0     5      19000     60.00    0.00   CALCULATED    300.00        19000   18700.00      PASS
Task_D                     0     4      17000     60.00    0.00   CALCULATED    240.00        17000   16760.00      PASS
Task_C                     0     3      13000     60.00    0.00   CALCULATED    180.00        13000   12820.00      PASS
Task_B                     0     2      11000     60.00    0.00   CALCULATED    120.00        11000   10880.00      PASS
Task_A                     0     1       7000     60.00    0.00   CALCULATED     60.00         7000    6940.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

### Generated Finding:
- **`[WARNING] autosar_hyperperiod_explosion`:**  
  *Hyperperiod = 323,323ms — full simulation disabled. Showing representative 30ms window only. RTA used for schedulability verdict. [CALCULATED]*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_9/firmware.elf \
  --map Test_SUITE_2/Test_9/firmware.map \
  --ld  Test_SUITE_2/Test_9/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_9/schedule.json \
  --charts-dir Test_SUITE_2/Test_9/charts/
```
