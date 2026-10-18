# Buttazzo Test Suite — Test Case 4: Deadline Monotonic (DM) Schedulability (Buttazzo §4.4)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 4.4 (Deadline Monotonic), Example 2.1.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization Diagnosis:** `INDETERMINATE (78.3% > 78.0%)`  
> **Algorithm:** `DM (Deadline Monotonic)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Deadline Monotonic (DM)

---

## 1. What This Test Signifies

Test Case 4 in the `buttazo_test` suite reproduces **Example 2.1 from Section 4.4 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark evaluates **constrained-deadline task sets ($D_i < T_i$)**:
1. **The Sub-optimality of Rate Monotonic:** When deadlines are shorter than periods, Rate Monotonic (RM) priority ordering (based solely on periods $T_i$) is no longer optimal. Joseph & Pandya (1986) and Leung & Whitehead (1982) proved that **Deadline Monotonic (DM)** priority assignment (where tasks with shorter relative deadlines $D_i$ receive higher priority) is strictly optimal among all fixed-priority algorithms.
2. **Evaluation Against Deadlines ($D_i$), Not Periods ($T_i$):** Under constrained deadlines, Response Time Analysis must evaluate $R_i \le D_i$ rather than $R_i \le T_i$. Even if a task finishes before its period, finishing after its deadline constitutes a real-time failure.
3. **Automated Architectural Recommendation (`autosar_rm_suboptimal`):** If an engineer erroneously configures an RM scheduler for a constrained-deadline system, EmbedSched flags `autosar_rm_suboptimal` warnings for all tasks where $D_i < T_i$, recommending switching to DM or EDF.

---

## 2. Theoretical Background & Specification (Buttazzo §4.4 Ex. 2.1)

Three periodic tasks on a single core where every task has a relative deadline strictly shorter than its period ($D_i < T_i$). Under Deadline Monotonic policy, priorities are assigned according to relative deadlines ($D_1 < D_2 < D_3 \implies \text{Priority}(\tau_1) > \text{Priority}(\tau_2) > \text{Priority}(\tau_3)$):

| Task | Execution Time ($C_i$) | Period ($T_i$) | Relative Deadline ($D_i$) | Constrained? | DM Priority |
|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $1\text{ ms}\ (1,000\ \mu\text{s})$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $\mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$ | $D_1 < T_1\ (3 < 4)$ | **1 (Highest)** |
| $\tau_2$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $\mathbf{5\text{ ms}\ (5,000\ \mu\text{s})}$ | $D_2 < T_2\ (5 < 6)$ | **2** |
| $\tau_3$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $10\text{ ms}\ (10,000\ \mu\text{s})$ | $\mathbf{8\text{ ms}\ (8,000\ \mu\text{s})}$ | $D_3 < T_3\ (8 < 10)$ | **3 (Lowest)** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{1}{4} = 0.25000 \quad (25.00\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{2}{6} = \frac{1}{3} \approx 0.33333 \quad (33.33\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{2}{10} = 0.20000 \quad (20.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{3} \frac{C_i}{T_i} = 0.2500 + 0.3333 + 0.2000 = \frac{47}{60} \approx \mathbf{0.78333\ (78.33\%)}$$

**RM Bound Comparison:**
$$U_{\text{bound}}(3) = 3(2^{1/3} - 1) \approx 77.98\%$$
$$U = 78.33\% > 77.98\% \implies \mathbf{INDETERMINATE}$$
The core operates slightly above the classical bound, triggering the standard informational `autosar_utilization_warning` (-15 score penalty) and requiring exact RTA.

---

### B. Exact Response Time Analysis (RTA) Iterations (Joseph & Pandya)

The fixed-point recurrence evaluates response times against relative deadlines $D_i$:
$$R_i^{(0)} = C_i$$
$$R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### 1. Task $\tau_1$ (Priority 1 — Shortest Deadline $D_1 = 3\text{ ms}$)
Task $\tau_1$ suffers no preemption:
$$R_1 = C_1 = \mathbf{1\text{ ms}\ (1,000\ \mu\text{s})}$$
$$\text{Margin}_1 = D_1 - R_1 = 3\text{ ms} - 1\text{ ms} = \mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 2. Task $\tau_2$ (Priority 2 — Deadline $D_2 = 5\text{ ms}$)
Task $\tau_2$ is preempted only by $\tau_1$ ($\text{hp}(2) = \{ \tau_1 \}$):

- **Iteration 0 (Seed):**
  $$R_2^{(0)} = C_2 = 2\text{ ms}$$
- **Iteration 1:**
  $$R_2^{(1)} = C_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 2 + \left\lceil \frac{2}{4} \right\rceil \times 1 = 2 + (1 \times 1) = 3\text{ ms}$$
- **Iteration 2:**
  $$R_2^{(2)} = C_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 2 + \left\lceil \frac{3}{4} \right\rceil \times 1 = 2 + (1 \times 1) = \mathbf{3\text{ ms}}$$

**Convergence:**
$$R_2^{(2)} = R_2^{(1)} = \mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$$
$$\text{Margin}_2 = D_2 - R_2 = 5\text{ ms} - 3\text{ ms} = \mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 3. Task $\tau_3$ (Priority 3 — Deadline $D_3 = 8\text{ ms}$)
Task $\tau_3$ is preempted by both $\tau_1$ ($C_1=1, T_1=4$) and $\tau_2$ ($C_2=2, T_2=6$):

- **Iteration 0 (Seed):**
  $$R_3^{(0)} = C_3 = 2\text{ ms}$$
- **Iteration 1:**
  $$R_3^{(1)} = 2 + \left\lceil \frac{2}{4} \right\rceil \times 1 + \left\lceil \frac{2}{6} \right\rceil \times 2 = 2 + (1 \times 1) + (1 \times 2) = 2 + 1 + 2 = 5\text{ ms}$$
- **Iteration 2:**
  $$R_3^{(2)} = 2 + \left\lceil \frac{5}{4} \right\rceil \times 1 + \left\lceil \frac{5}{6} \right\rceil \times 2 = 2 + (2 \times 1) + (1 \times 2) = 2 + 2 + 2 = 6\text{ ms}$$
- **Iteration 3:**
  $$R_3^{(3)} = 2 + \left\lceil \frac{6}{4} \right\rceil \times 1 + \left\lceil \frac{6}{6} \right\rceil \times 2 = 2 + (2 \times 1) + (1 \times 2) = 2 + 2 + 2 = \mathbf{6\text{ ms}}$$

**Convergence:**
$$R_3^{(3)} = R_3^{(2)} = \mathbf{6\text{ ms}\ (6,000\ \mu\text{s})}$$

**Deadline Evaluation:**
$$R_3 = 6\text{ ms} \le D_3 = 8\text{ ms}$$
$$\text{Margin}_3 = D_3 - R_3 = 8\text{ ms} - 6\text{ ms} = \mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

## 4. Architectural Check: The `autosar_rm_suboptimal` Rule

EmbedSched implements Rule 13 (`autosar_rm_suboptimal`). If a user configures a core as `RM` when any task has a constrained deadline ($D < T$), EmbedSched detects the misconfiguration:

```text
[WARNING] [STATIC] autosar_rm_suboptimal
  Task 'tau1' has deadline < period (3000 µs < 4000 µs) — RM priority assignment is suboptimal, use DM.
  Fix: Change core scheduling algorithm to DM (Deadline Monotonic) or EDF.

[WARNING] [STATIC] autosar_rm_suboptimal
  Task 'tau2' has deadline < period (5000 µs < 6000 µs) — RM priority assignment is suboptimal, use DM.

[WARNING] [STATIC] autosar_rm_suboptimal
  Task 'tau3' has deadline < period (8000 µs < 10000 µs) — RM priority assignment is suboptimal, use DM.
```

In this test, the core is explicitly configured with `"algorithm": "DM"`. EmbedSched recognizes that the architecture uses the optimal Deadline Monotonic assignment, suppressing the suboptimal warning and executing RTA under DM semantics.

---

## 5. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo §4.4 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Configured Algorithm** | `DM` | `DM` | :white_check_mark: Exact |
| **Total Core Utilization ($U$)** | $78.33\%$ | `78.3%` | :white_check_mark: Exact |
| **Liu & Layland Bound ($U_{\text{bound}}$)** | $77.98\%$ | `78.0%` | :white_check_mark: Exact |
| **Utilization Status** | `INDETERMINATE` | `INDETERMINATE (above RM bound)` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $1\text{ ms}\ (1,000\ \mu\text{s})$ | `1000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Deadline Margin** | $\mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})}$ ($D_1 = 3$) | `+2000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $3\text{ ms}\ (3,000\ \mu\text{s})$ | `3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Deadline Margin** | $\mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})}$ ($D_2 = 5$) | `+2000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ WCRT ($R_3$)** | $6\text{ ms}\ (6,000\ \mu\text{s})$ | `6000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Deadline Margin** | $\mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})}$ ($D_3 = 8$) | `+2000.00 µs` | :white_check_mark: Exact |
| **Overall System Verdict** | `SCHEDULABLE` | `PASS (SCHEDULABLE)` | :white_check_mark: Exact |

---

## 6. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_4

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
