# Test Case 10: Cross-Core Resource Sharing — Circular Deadlock Risk

> **Status:** `PASS` Timing Deadlines / `CRITICAL: DEADLOCK_RISK DETECTED`  
> **Confidence:** `[IPET-CONSERVATIVE]` / `[STATIC]`  
> **Architecture:** STM32H745 (Dual-Core: Cortex-M7 @ 480 MHz + Cortex-M4 @ 240 MHz)  
> **Rule:** `autosar_deadlock_risk`

---

## 1. What This Test Signifies

Test Case 10 validates the tool's **Resource Allocation Graph (RAG) and lock-ordering cycle detection**.

In multi-threaded and multi-core firmware, tasks frequently synchronize across cores using mutexes, spinlocks, or semaphores. If two tasks acquire multiple locks in opposite order (the classic **AB / BA lock-order inversion**), Coffman's circular wait condition is satisfied. At runtime, the system will inevitably experience a permanent freeze or watchdog reset:
1. Core 0 acquires Lock A.
2. Core 1 acquires Lock B.
3. Core 0 attempts to acquire Lock B (blocks waiting for Core 1).
4. Core 1 attempts to acquire Lock A (blocks waiting for Core 0).
5. **Deadlock:** Neither core can ever make forward progress.

This test proves that EmbedSched:
- Parses lock acquisition orders (`acquisition_order` in `schedule.json`).
- Constructs a global directed lock-dependency graph.
- Executes cycle-detection Depth First Search (DFS).
- Flags the exact circular path and identifies the offending tasks.
- Emits a high-priority warning banner before the executive summary and applies a -30 deduction.

---

## 2. Why It Was Performed

1. **Timing Analysis Blindspot:** A system can be 100% schedulable according to Response Time Analysis (all $R_i \le D_i$), yet freeze completely at runtime due to a deadlock. Schedulability tools that ignore lock-ordering provide a dangerous false sense of safety.
2. **Compile-Time Preemption:** Deadlocks are non-deterministic and notoriously difficult to reproduce in hardware labs because they depend on rare microsecond timing coincidences. Detecting them at compile-time completely prevents the bug from ever reaching physical hardware.
3. **Actionable Remediation:** Pinpoints the exact locks and tasks involved and instructs developers to enforce a strict global acquisition hierarchy.

---

## 3. Configuration & Task Set

### Hardware Definition (`stm32h745.yaml`)
- Dual-core Cortex-M7 + Cortex-M4 with shared SRAM3 memory.

### Mutex Configuration (`schedule.json`)
```json
"resources": [
  {
    "name": "mutex_A",
    "type": "spinlock",
    "accessed_by": ["Task_Core0_Alpha", "Task_Core1_Beta"],
    "acquisition_order": { "Task_Core0_Alpha": 1, "Task_Core1_Beta": 2 }
  },
  {
    "name": "mutex_B",
    "type": "spinlock",
    "accessed_by": ["Task_Core0_Alpha", "Task_Core1_Beta"],
    "acquisition_order": { "Task_Core0_Alpha": 2, "Task_Core1_Beta": 1 }
  }
]
```

Notice the inverted acquisition sequence:
- `Task_Core0_Alpha` on Core 0 acquires **`mutex_A` (1st)** $\to$ **`mutex_B` (2nd)**.
- `Task_Core1_Beta` on Core 1 acquires **`mutex_B` (1st)** $\to$ **`mutex_A` (2nd)**.

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & IPET WCET Derivation
The static analyzer inspects `firmware.map` and applies IPET microarchitectural timing:
- Because spinlocks contain polling loops that cannot be statically resolved without loop bound annotations, EmbedSched applies the conservative loop bound fallback tier (`[IPET-CONSERVATIVE]`):
  $$\text{WCET}_{\text{Alpha}} = \mathbf{114.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET-CONSERVATIVE}])$$
  $$\text{WCET}_{\text{Beta}} = \mathbf{114.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET-CONSERVATIVE}])$$

### B. Timing Schedulability (The False Positive)
- `Task_Core0_Alpha` (Core 0): $T = 10,000\text{ µs}, D = 10,000\text{ µs}, C = 114.00\text{ µs} \implies R_{\text{Alpha}} = 114.00\text{ µs} \le 10,000\text{ µs}$ (`PASS`, margin $+9,886.00\text{ µs}$)
- `Task_Core1_Beta` (Core 1): $T = 20,000\text{ µs}, D = 20,000\text{ µs}, C = 114.00\text{ µs} \implies R_{\text{Beta}} = 114.00\text{ µs} \le 20,000\text{ µs}$ (`PASS`, margin $+19,886.00\text{ µs}$)

Pure timing analysis reports 100% schedulability with huge slack margins.

### C. Directed Lock-Dependency Graph & Cycle Detection Math

Let $\mathcal{R} = \{\text{mutex\_A}, \text{mutex\_B}\}$ be the set of mutual exclusion locks.  
A directed edge $(r_1 \to r_2)$ exists in the lock-dependency graph $G = (V, E)$ if any task acquires $r_2$ while already holding $r_1$.

#### Edge Construction:
1. `Task_Core0_Alpha`:
   $$\text{Order} = \langle \text{mutex\_A}, \text{mutex\_B} \rangle \implies (\text{mutex\_A} \longrightarrow \text{mutex\_B}) \in E$$
2. `Task_Core1_Beta`:
   $$\text{Order} = \langle \text{mutex\_B}, \text{mutex\_A} \rangle \implies (\text{mutex\_B} \longrightarrow \text{mutex\_A}) \in E$$

#### Adjacency Matrix Representation:
$$M = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$$

#### DFS Cycle Traversal:
1. Visit node `mutex_A`: mark as active in recursion stack.
2. Follow outgoing edge to `mutex_B`: mark `mutex_B` active.
3. Follow outgoing edge from `mutex_B` to `mutex_A`.
4. Node `mutex_A` is already in the active recursion stack:
   $$\text{Directed Cycle Detected:}\quad \mathbf{\text{mutex\_A} \longrightarrow \text{mutex\_B} \longrightarrow \text{mutex\_A}}$$

This satisfies **Coffman Condition #4 (Circular Wait)**:
$$\exists\ \text{Cycle in } G \implies \mathbf{DEADLOCK\ RISK\ (CRITICAL)}$$

Score deduction: -30 points (Overall score: 70/100).

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

#### 2. Step-by-Step Task Jitter Calculations (Hyperperiod $H = 20,000\text{ µs}$)
1. **`Task_Core0_Alpha` (Priority 1, $T = 10,000\text{ µs}$, $K = 2$ activations):**
   * **Interference:** Highest-priority task on Core 0; no higher-priority preemptions ($hp = \emptyset$).
   * **Dispatch:** Dispatches immediately at $s_i(k) = k \cdot 10,000\text{ µs}$ for every activation $k$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

2. **`Task_Core1_Beta` (Priority 1, $T = 20,000\text{ µs}$, $K = 1$ activations):**
   * **Interference:** Preempted by higher-priority workload: `Task_Core0_Alpha` (114.00 µs) (total synchronous release load $\sum C_{hp} = 114.00\text{ µs}$).
   * **Theoretical Start Delay Bound:** At synchronous release $t = 0$ ($k = 0$), start delay is upper-bounded by $J_{\text{bound}} = \sum_{j \in hp} C_j = \mathbf{114.00\text{ µs}}$.
   * **Simulated Dispatch:** Under discrete-event simulation (with stochastic execution times), actual observed worst-case start delay is $s_i(k) - k \cdot T_i = 0.00\text{ µs}$.
   * **Calculated Metrics:** $J^{\max} = \mathbf{0.00\text{ µs}}$, $J^{\text{mean}} = \mathbf{0.00\text{ µs}}$, $\rho = \frac{0.00}{20,000} \times 100\% = \mathbf{0.00\%} \implies$ **EXCELLENT (<1% of period)**.

#### 3. Jitter Summary Table
| Task Name | Priority | Period ($T_i$) | Activations ($K_i$) | Max Jitter ($J_i^{\max}$) | Mean Jitter ($J_i^{\text{mean}}$) | Jitter Ratio ($\rho_i$) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Task_Core0_Alpha` | 1 | `10,000 µs` | 2 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |
| `Task_Core1_Beta` | 1 | `20,000 µs` | 1 | `0.00 µs` | `0.00 µs` | `0.00%` | **EXCELLENT (<1% of period)** |

#### 4. Validating the Matplotlib Graph (`charts/jitter_chart.png`)
The generated visual plot [charts/jitter_chart.png](charts/jitter_chart.png) renders the start-time variation for each task across the entire simulated timeline:
* **Horizontal Axis (`Activation #`):** Represents discrete activation instances $k \in \{0, 1, \dots, K_i - 1\}$.
* **Vertical Axis (`Jitter (µs)`):** Represents the dispatch latency $s_i(k) - k \cdot T_i$ in microseconds.
* **Visual Trace Validation:**
  - **`Task_Core0_Alpha`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 2 activation(s), visually proving zero start-time preemption.
  - **`Task_Core1_Beta`:** Renders as a flat horizontal trace at $y = 0.00\text{ µs}$ across all 1 activation(s), visually proving zero start-time preemption.
---

## 5. Expected vs Actual Tool Output

```
==============================================================================
 AUTOSAR SCHEDULABILITY ANALYSIS
==============================================================================

  ⚠  DEADLOCK_RISK  ⚠
  ────────────────────────────────────────
  Deadlock risk detected — inconsistent lock acquisition order across tasks.
    Lock cycle: mutex_A → mutex_B → mutex_A
    Task_Core0_Alpha acquires: mutex_A → mutex_B
    Task_Core1_Beta acquires: mutex_B → mutex_A
    Enforce a consistent global lock ordering to eliminate the cycle. [STATIC]

EXECUTIVE SUMMARY: SCHEDULABILITY OVERVIEW
  ────────────────────────────────────────────────────────────────────────────────────
  Task                    Period µs   WCET µs      R µs      D µs   Margin µs  Verdict
  ────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha            10000    114.00    114.00     10000     9886.00     PASS
  Task_Core1_Beta             20000    114.00    114.00     20000    19886.00     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [IPET-CONSERVATIVE] — all tasks meet timing deadlines  ⚠ DEADLOCK_RISK DETECTED


3. RESPONSE TIME ANALYSIS TABLE
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Task_Core0_Alpha           0     1      10000    114.00    0.00 IPET-CONSERVATIVE    114.00        10000    9886.00
  Task_Core1_Beta            1     1      20000    114.00    0.00 IPET-CONSERVATIVE    114.00        20000   19886.00
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

### Generated Finding:
- **`[CRITICAL] [STATIC] autosar_deadlock_risk` (-30 points):**  
  *Deadlock risk detected — inconsistent lock acquisition order across tasks. Lock cycle: `mutex_A → mutex_B → mutex_A`.*  
  *Fix: Impose a global total order on all locks (e.g., alphabetical or by ID). Every task must acquire locks in that order.*

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_10/firmware.elf \
  --map tests/Test_Suite2/Test_10/firmware.map \
  --ld  tests/Test_Suite2/Test_10/linker.ld \
  --chip tests/Test_Suite2/Test_10/stm32f407.yaml \
  --autosar-config tests/Test_Suite2/Test_10/schedule.json \
  --charts-dir tests/Test_Suite2/Test_10/charts/
```
