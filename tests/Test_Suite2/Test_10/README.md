# Test Case 10: Cross-Core Resource Sharing — Circular Deadlock Risk

> **Status:** `PASS` Timing Deadlines / `CRITICAL: DEADLOCK_RISK DETECTED`  
> **Confidence:** `[STATIC]`  
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

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_10/firmware.map):
- `task_core0_alpha`: Symbol size `0x28` bytes = $40\text{ bytes}$
  $$\text{Instructions} = \frac{40}{2.5} = 16\text{ instructions}$$
  $$\text{Cycles} = 16 \times 1.15 \approx 18.4\text{ cycles}$$
  $$C_{\text{Alpha}} \approx 0.20\text{ µs}$$
- `task_core1_beta`: Symbol size `0x28` bytes = $40\text{ bytes}$
  $$C_{\text{Beta}} \approx 0.20\text{ µs}$$

### B. Timing Schedulability (The False Positive)
- `Task_Core0_Alpha` (Core 0): $T = 10,000\text{ µs}, D = 10,000\text{ µs}, C = 0.20\text{ µs} \implies R_{\text{Alpha}} = 0.20\text{ µs} \le 10,000\text{ µs}$ (`PASS`)
- `Task_Core1_Beta` (Core 1): $T = 20,000\text{ µs}, D = 20,000\text{ µs}, C = 0.20\text{ µs} \implies R_{\text{Beta}} = 0.20\text{ µs} \le 20,000\text{ µs}$ (`PASS`)

Pure timing analysis reports 100% schedulability with huge slack margins (+9,999.8 µs and +19,999.8 µs).

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
  Task_Core0_Alpha            10000      0.20      0.20     10000     9999.80     PASS
  Task_Core1_Beta             20000      0.20      0.20     20000    19999.80     PASS
  ────────────────────────────────────────────────────────────────────────────────────
  Overall: PASS [CALCULATED] — all tasks meet timing deadlines  ⚠ DEADLOCK_RISK DETECTED
```

### Generated Finding:
- **`[CRITICAL] autosar_deadlock_risk` (-30 points):**  
  *Deadlock risk detected — inconsistent lock acquisition order across tasks. Lock cycle: `mutex_A → mutex_B → mutex_A`.*  
  *Fix: Impose a global total order on all locks (e.g., alphabetical or by ID). Every task must acquire locks in that order.*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_10/firmware.elf \
  --map Test_SUITE_2/Test_10/firmware.map \
  --ld  Test_SUITE_2/Test_10/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_10/schedule.json \
  --charts-dir Test_SUITE_2/Test_10/charts/
```
