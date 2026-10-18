# Test Case 11: WCET Confidence Propagation — Honest Verdict Tagging

> **Status:** `PASS [HEURISTIC]` (Confidence Contamination Verified)  
> **Confidence:** `[HEURISTIC]` (Lowest-Tier Propagation)  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 11 verifies the tool's **Confidence Tagging and Epistemic Honesty** architecture.

In static analysis tools, a major credibility flaw is "over-claiming": asserting that a system is mathematically guaranteed to meet its deadlines when one of the task's WCETs was actually an unverified heuristic guess.

EmbedSched establishes a strict three-tier epistemic hierarchy:
$$\mathbf{[SIMULATED]} > \mathbf{[CALCULATED]} > \mathbf{[HEURISTIC]}$$

This test proves that EmbedSched:
1. Displays the exact derivation source tag for every task in the RTA table.
2. Implements **Confidence Contamination**: the overall schedulability verdict strictly adopts the **lowest confidence tag** present among any of the analyzed tasks or callees.
3. If even a single task's WCET relies on `[HEURISTIC]`, the entire report verdict is downgraded from `[CALCULATED]` to `[HEURISTIC]`.
4. Emits a diagnostic warning alerting developers to provide missing `.su` stack files or check symbol names to restore high-confidence verification.

---

## 2. Why It Was Performed

1. **Safety Case Integrity:** Under functional safety standards (ISO 26262, IEC 61508, DO-178C), safety auditors reject reports that present synthetic estimates as proven numbers. By explicitly labeling confidence tiers, EmbedSched builds audit credibility.
2. **Preventing Silent Downgrade Masks:** If a developer misnames a function or links a proprietary binary blob without debug symbols, EmbedSched must not silently hide this weakness behind a green "PASS [CALCULATED]" banner.
3. **Traceability:** Engineers can immediately scan the RTA table to see which tasks need hardware measurement vs. which tasks are well-modeled by build artifacts.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Three tasks with heterogeneous confidence sources:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Entry Function | Confidence Tier | Derivation Source |
|:---|:---:|:---:|:---:|:---|:---:|:---|
| `Task_A` | 50,000 µs (50 ms) | 50,000 µs (50 ms) | 1 | `task_a_body` | `[SIMULATED]` | Renode PC dynamic trace log |
| `Task_B` | 100,000 µs (100 ms) | 100,000 µs (100 ms) | 2 | `task_b_body` | `[CALCULATED]` | Symbol size in `.map` ($2.5\text{ B/insn} \times 1.15$) |
| `Task_C` | 200,000 µs (200 ms) | 200,000 µs (200 ms) | 3 | `task_c_missing` | `[HEURISTIC]` | Function absent from symbols; nominal fallback |

---

## 4. Step-by-Step Mathematical Calculations

### A. Derivation of WCETs per Confidence Tier

#### 1. Task_A (`task_a_body`) — Dynamic Simulation Source:
* Input artifact: Renode instruction trace log ([trace.log](file:///e:/firmware_analyzer/Test_SUITE_2/Test_11/trace.log)).
* Dynamic execution count: Exactly $1,176\text{ instructions}$ logged for `task_a_body`.
$$\text{Cycles}_A = 1,176\text{ instructions} \times 1.0\text{ CPI} = 1,176\text{ cycles}$$
$$C_A = \frac{1,176\text{ cycles}}{168\text{ MHz}} = 7.00\text{ µs}$$
* **Assigned Tier:** `[SIMULATED]` (Highest tier — direct instruction trace observed).

#### 2. Task_B (`task_b_body`) — Static Binary Extraction:
* Input artifact: Symbol size in [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_11/firmware.map): `0x332` bytes = $818\text{ bytes}$.
$$\text{Instructions}_B = \frac{818}{2.5} = 327.2\text{ instructions}$$
$$\text{Cycles}_B = 327.2 \times 1.14 \approx 373\text{ cycles}$$
$$C_B = \frac{373\text{ cycles}}{168\text{ MHz}} \approx 2.22\text{ µs}$$
* **Assigned Tier:** `[CALCULATED]` (Medium tier — datasheet clock model + binary section size).

#### 3. Task_C (`task_c_missing`) — Unresolved Symbol Fallback:
* Input artifact: Symbol `task_c_missing` is absent from `.map`, `.elf`, and `trace.log`.
* Fallback heuristic: Nominal default function stub ($10\text{ instructions}$):
$$\text{Cycles}_C = 10 \times 1.0 = 10\text{ cycles}$$
$$C_C = \frac{10}{168\text{ MHz}} \approx 0.06\text{ µs}$$
* **Assigned Tier:** `[HEURISTIC]` (Lowest tier — unverified fallback).

---

### B. Confidence Propagation & Contamination Algebra

In `analysis/wcet_extractor.py`, confidence tiers are mapped to total order integers:
$$\text{Rank}([SIMULATED]) = 2$$
$$\text{Rank}([CALCULATED]) = 1$$
$$\text{Rank}([HEURISTIC]) = 0$$

The system-level confidence $Q_{\text{sys}}$ of a composite task set $\mathcal{T} = \{\tau_1, \tau_2, \dots, \tau_n\}$ is governed by the minimum lattice operator:
$$Q_{\text{sys}} = \min_{\tau_i \in \mathcal{T}} \text{Rank}(Q_i) = \min(2, 1, 0) = 0 \implies \mathbf{[HEURISTIC]}$$

Even though `Task_A` has high-grade dynamic simulation data and `Task_B` has static binary calculations, the presence of `Task_C` **contaminates** the overall schedulability verdict:
$$\mathbf{Verdict:}\quad \text{PASS } \mathbf{[HEURISTIC]}$$

The engine triggers finding `autosar_heuristic_wcet` (-10 deduction), warning the safety engineer that the pass verdict is provisional.

---

### C. Response Time Recurrence Iterations

#### 1. Task A (Priority 1, $T_A = 50,000\text{ µs}, D_A = 50,000\text{ µs}$):
* $hp(A) = \emptyset$
* $R_A = C_A = 7.00\text{ µs} \le 50,000\text{ µs}$  
* **Margin:** $50,000 - 7.00 = +49,993.00\text{ µs}$ (`PASS [SIMULATED]`)

#### 2. Task B (Priority 2, $T_B = 100,000\text{ µs}, D_B = 100,000\text{ µs}$):
* $hp(B) = \{A\}$
* $R_B^{(0)} = C_B = 2.22\text{ µs}$
* $R_B^{(1)} = 2.22 + \left\lceil \frac{2.22}{50,000} \right\rceil \times 7.00 = 2.22 + 7.00 = 9.22\text{ µs}$
* $R_B^{(2)} = 2.22 + \left\lceil \frac{9.22}{50,000} \right\rceil \times 7.00 = 9.22\text{ µs} \quad (\text{Converged})$
* **Margin:** $100,000 - 9.22 = +99,990.78\text{ µs}$ (`PASS [CALCULATED]`)

#### 3. Task C (Priority 3, $T_C = 200,000\text{ µs}, D_C = 200,000\text{ µs}$):
* $hp(C) = \{A, B\}$
* $R_C^{(0)} = C_C = 0.06\text{ µs}$
* $R_C^{(1)} = 0.06 + \left\lceil \frac{0.06}{50,000} \right\rceil \times 7.00 + \left\lceil \frac{0.06}{100,000} \right\rceil \times 2.22 = 0.06 + 7.00 + 2.22 = 9.28\text{ µs}$
* $R_C^{(2)} = 0.06 + \left\lceil \frac{9.28}{50,000} \right\rceil \times 7.00 + \left\lceil \frac{9.28}{100,000} \right\rceil \times 2.22 = 9.28\text{ µs} \quad (\text{Converged})$
* **Margin:** $200,000 - 9.28 = +199,990.72\text{ µs}$ (`PASS [HEURISTIC]`)

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_C                     0     3     200000      0.06    0.00    HEURISTIC      9.28       200000  199990.72      PASS
Task_B                     0     2     100000      2.22    0.00   CALCULATED      9.22       100000   99990.78      PASS
Task_A                     0     1      50000      7.00    0.00    SIMULATED      7.00        50000   49993.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [HEURISTIC] — all tasks meet timing deadlines
```

### Generated Finding:
- **`[WARNING] autosar_heuristic_wcet` (-10 points):**  
  *Task 'Task_C' WCET is heuristic — stack usage file missing or function 'task_c_missing' not found in ELF symbols or Renode trace. Recompile with `-fstack-usage` for higher confidence. [HEURISTIC]*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_11/firmware.elf \
  --map Test_SUITE_2/Test_11/firmware.map \
  --ld  Test_SUITE_2/Test_11/linker.ld \
  --trace Test_SUITE_2/Test_11/trace.log \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_11/schedule.json \
  --charts-dir Test_SUITE_2/Test_11/charts/
```
