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

### D. Start-Time Jitter Analysis & Graph Validation

#### 1. Mathematical Formulation
In a hard real-time preemptive system, the ideal periodic release time for activation $k$ ($k \in \{0, 1, \dots, K_i - 1\}$) of task $\tau_i$ is:
$$t_{\text{rel}}(k) = k \cdot T_i$$

Under work-conserving, non-anticipative scheduling, a task cannot start prior to its release ($s_i(k) \ge t_{\text{rel}}(k)$). The start-time jitter $J_i(k)$ quantifies the non-negative dispatch latency incurred due to higher-priority task preemption or lower-priority blocking:
$$J_i(k) = s_i(k) - k \cdot T_i \ge 0$$

Across all $K_i = \lfloor H / T_i \rfloor$ timely activations over the simulation hyperperiod $H$:
* **Maximum Start-Time Jitter ($J_i^{\max}$):**
  $$J_i^{\max} = \max_{0 \le k < K_i} J_i(k)$$
* **Mean Start-Time Jitter ($J_i^{\text{mean}}$):**
  $$J_i^{\text{mean}} = \frac{1}{K_i} \sum_{k=0}^{K_i - 1} J_i(k)$$
* **Relative Jitter Ratio ($\rho_i$):**
  $$\rho_i = \frac{J_i^{\max}}{T_i} \times 100\%$$
* **Safety Assessment Classification:**
  - $\rho_i < 1\%$: **EXCELLENT** (negligible phase distortion; safe for high-frequency control loops)
  - $1\% \le \rho_i < 5\%$: **GOOD** (acceptable for general actuator & sensor processing)
  - $5\% \le \rho_i < 20\%$: **MODERATE** (detectable variation; acceptable for supervisory tasks)
  - $\rho_i \ge 20\%$: **HIGH WARNING** (significant preemption delay; risks control instability)

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 200,000\text{ µs}$)
1. **`Task_A` (Priority 1, $T = 50,000\text{ µs}$, $K = 4$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 50,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_B` (Priority 2, $T = 100,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (7.00 µs) (total synchronous release load $\sum C_{hp} = 7.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{7.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 6.23\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{6.23\text{ µs}}$, $J^{\text{mean}} = \mathbf{6.13\text{ µs}}$, $\rho = \frac{6.23}{100,000} \times 100\% = \mathbf{0.01\%} \implies$ **EXCELLENT (<1% of period)**.

3. **`Task_C` (Priority 3, $T = 200,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_A` (7.00 µs), `Task_B` (3.99 µs) (total synchronous release load $\sum C_{hp} = 10.99\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{10.99\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 10.06\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{10.06\text{ µs}}$, $J^{\text{mean}} = \mathbf{10.06\text{ µs}}$, $\rho = \frac{10.06}{200,000} \times 100\% = \mathbf{0.01\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_A` | 1 | `50,000 µs` | 4 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_B` | 2 | `100,000 µs` | 2 | `6.23 µs` | `6.13 µs` | `0.01%` | **EXCELLENT (<1% of period)** |
| `Task_C` | 3 | `200,000 µs` | 1 | `10.06 µs` | `10.06 µs` | `0.01%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_A`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 4 activation(s), visually proving zero start-time preemption.
  - **`Task_B`:** Plots 2 point(s) peaking at $y = 6.23\text{ µs}$ (mean $y = 6.13\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
  - **`Task_C`:** Plots 1 point(s) peaking at $y = 10.06\text{ µs}$ (mean $y = 10.06\text{ µs}$), visually confirming that dispatch delays remain strictly bounded by higher-priority task execution windows.
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
