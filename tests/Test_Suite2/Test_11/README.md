# Test Case 11: WCET Confidence Propagation — Honest Verdict Tagging

> **Status:** `PASS [HEURISTIC]` (Confidence Contamination Verified)  
> **Confidence:** `[HEURISTIC]` (Lowest-Tier Propagation)  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 11 verifies the tool's **Confidence Tagging and Epistemic Honesty** architecture.

In static analysis tools, a major credibility flaw is "over-claiming": asserting that a system is mathematically guaranteed to meet its deadlines when one of the task's WCETs was actually an unverified heuristic guess.

EmbedSched establishes a strict multi-tier epistemic hierarchy:
$$\mathbf{[SIMULATED]} \longrightarrow \mathbf{[IPET]} \longrightarrow \mathbf{[IPET-ANNOTATED]} \longrightarrow \mathbf{[IPET-CONSERVATIVE]} \longrightarrow \mathbf{[CALCULATED]} \longrightarrow \mathbf{[HEURISTIC]}$$

This test proves that EmbedSched:
1. Displays the exact derivation source tag for every task in the RTA table.
2. Implements **Confidence Contamination**: the overall schedulability verdict strictly adopts the **lowest confidence tag** present among any of the analyzed tasks or callees.
3. If even a single task's WCET relies on `[HEURISTIC]`, the entire report verdict is downgraded to `[HEURISTIC]`.
4. Emits a diagnostic warning alerting developers to provide missing `.su` stack files or check symbol names to restore high-confidence verification.

---

## 2. Why It Was Performed

1. **Safety Case Integrity:** Under functional safety standards (ISO 26262, IEC 61508, DO-178C), safety auditors reject reports that present synthetic estimates as proven numbers. By explicitly labeling confidence tiers, EmbedSched builds audit credibility.
2. **Preventing Silent Downgrade Masks:** If a developer misnames a function or links a proprietary binary blob without debug symbols, EmbedSched must not silently hide this weakness behind a green banner.
3. **Traceability:** Engineers can immediately scan the RTA table to see which tasks need hardware measurement vs. which tasks are well-modeled by build artifacts.

---

## 3. Configuration & Task Set

### Task Set (`schedule.json`)
Three tasks with heterogeneous confidence sources:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | Entry Function | Confidence Tier | Derivation Source |
|:---|:---:|:---:|:---:|:---|:---:|:---|
| `Task_A` | 50,000 µs (50 ms) | 50,000 µs (50 ms) | 1 | `task_a_body` | `[SIMULATED]` | Renode PC dynamic trace log |
| `Task_B` | 100,000 µs (100 ms) | 100,000 µs (100 ms) | 2 | `task_b_body` | `[IPET]` | Microarchitectural analysis on ELF binary |
| `Task_C` | 200,000 µs (200 ms) | 200,000 µs (200 ms) | 3 | `task_c_missing` | `[HEURISTIC]` | Function absent from symbols; nominal fallback |

---

## 4. Step-by-Step Mathematical Calculations

### A. Derivation of WCETs per Confidence Tier

#### 1. Task_A (`task_a_body`) — Dynamic Simulation Source:
* Input artifact: Renode instruction trace log (`trace.log`).
* Dynamic execution count: Exactly $1,176\text{ instructions}$ logged for `task_a_body`.
$$\text{Cycles}_A = 1,176\text{ instructions} \times 1.0\text{ CPI} = 1,176\text{ cycles}$$
$$C_A = \frac{1,176\text{ cycles}}{168\text{ MHz}} = \mathbf{7.00\text{ µs}} \quad (\text{Confidence: } [\text{SIMULATED}])$$

#### 2. Task_B (`task_b_body`) — Static Microarchitectural Analysis (IPET):
* Input artifact: Binary ELF disassembly and CFG microarchitectural analysis.
* Pipelined execution and Flash wait-state modeling yields:
$$C_B = \mathbf{3.99\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$$

#### 3. Task_C (`task_c_missing`) — Unresolved Symbol Fallback:
* Input artifact: Symbol `task_c_missing` is absent from `.map`, `.elf`, and `trace.log`.
* Fallback heuristic: Nominal default function stub ($10\text{ instructions}$):
$$\text{Cycles}_C = 10\text{ cycles} \implies C_C = \frac{10}{168\text{ MHz}} \approx \mathbf{0.06\text{ µs}} \quad (\text{Confidence: } [\text{HEURISTIC}])$$

---

### B. Confidence Propagation & Contamination Algebra

Confidence tiers are ordered:
$$\text{Rank}([SIMULATED]) > \text{Rank}([IPET]) > \text{Rank}([CALCULATED]) > \text{Rank}([HEURISTIC])$$

The system-level confidence $Q_{\text{sys}}$ of composite task set $\mathcal{T} = \{\tau_1, \tau_2, \tau_3\}$ is governed by the minimum lattice operator:
$$Q_{\text{sys}} = \min(Q_A, Q_B, Q_C) = \min([\text{SIMULATED}], [\text{IPET}], [\text{HEURISTIC}]) = \mathbf{[HEURISTIC]}$$

Even though `Task_A` has dynamic simulation data and `Task_B` has microarchitectural IPET data, the presence of `Task_C` **contaminates** the overall schedulability verdict:
$$\mathbf{Verdict:}\quad \text{PASS } \mathbf{[HEURISTIC]}$$

The engine triggers finding `autosar_heuristic_wcet` (-10 deduction), alerting the engineer that the verdict contains unverified fallback estimates.

---

### C. Response Time Recurrence Iterations

1. **`Task_A` (Priority 1):**
   * $\text{hp}(A) = \emptyset \implies R_A = C_A = \mathbf{7.00\text{ µs}} \le 50,000\text{ µs}$  
   * Slack Margin: $50,000 - 7.00 = \mathbf{+49,993.00\text{ µs}}$ (`PASS [SIMULATED]`)

2. **`Task_B` (Priority 2):**
   * $\text{hp}(B) = \{A\}$
   * $R_B^{(0)} = C_B = 3.99\text{ µs}$
   * $R_B^{(1)} = 3.99 + \left\lceil \frac{3.99}{50,000} \right\rceil \times 7.00 = 3.99 + 7.00 = \mathbf{10.99\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $100,000 - 10.99 = \mathbf{+99,989.01\text{ µs}}$ (`PASS [IPET]`)

3. **`Task_C` (Priority 3):**
   * $\text{hp}(C) = \{A, B\}$
   * $R_C^{(0)} = C_C = 0.06\text{ µs}$
   * $R_C^{(1)} = 0.06 + \left\lceil \frac{0.06}{50,000} \right\rceil \times 7.00 + \left\lceil \frac{0.06}{100,000} \right\rceil \times 3.99 = 0.06 + 7.00 + 3.99 = \mathbf{11.05\text{ µs}}\quad (\text{Converged})$
   * Slack Margin: $200,000 - 11.05 = \mathbf{+199,988.95\text{ µs}}$ (`PASS [HEURISTIC]`)

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_A                     0     1      50000      7.00    0.00    SIMULATED      7.00        50000   49993.00
Task_B                     0     2     100000      3.99    0.00         IPET     10.99       100000   99989.01
Task_C                     0     3     200000      0.06    0.00    HEURISTIC     11.05       200000  199988.95
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [HEURISTIC] — all tasks meet deadlines
```

### Generated Finding:
- **`[WARNING] [HEURISTIC] autosar_heuristic_wcet` (-10 points):**  
  *Task 'Task_C' WCET is heuristic — stack usage file missing or function 'task_c_missing' not found in ELF symbols or Renode trace. Recompile with `-fstack-usage` for higher confidence. [HEURISTIC]*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_11/firmware.elf \
  --map tests/Test_Suite2/Test_11/firmware.map \
  --ld  tests/Test_Suite2/Test_11/linker.ld \
  --renode-trace tests/Test_Suite2/Test_11/trace.log \
  --chip tests/Test_Suite2/Test_11/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_11/schedule.json \
  --charts-dir tests/Test_Suite2/Test_11/charts/
```
