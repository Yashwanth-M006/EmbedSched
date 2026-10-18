# Buttazzo Test Suite — Test Case 3: RM Genuine Deadline Miss & CPU Overload (Buttazzo Ex. 4.3)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Chapter 4 (Fixed-Priority Servers / Rate Monotonic Schedulability), Example 4.3.  
> **Status:** `FAIL (NOT SCHEDULABLE)`  
> **Utilization Diagnosis:** `OVERLOADED (101.2% > 100.0%)`  
> **Critical Findings:** `autosar_deadline_miss`, `autosar_cpu_overload`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 3 in the `buttazo_test` suite reproduces **Example 4.3 from Giorgio Buttazzo's classic textbook *Hard Real-Time Computing Systems***.

This textbook benchmark represents an **unschedulable system due to CPU overload**:
1. **Total System Overload ($U > 1.00$):** By slightly increasing task $\tau_2$'s execution time from $3\text{ ms}$ to $4\text{ ms}$ (compared to Example 4.2), the cumulative workload demands **more than 100% of the CPU's processing capacity** ($U \approx 101.19\%$).
2. **Fundamental Theoretical Impossibility:** When $U > 1.00$, no scheduling algorithm (neither fixed-priority RM/DM nor dynamic-priority EDF) can schedule the task set without dropping jobs or missing deadlines.
3. **Exact Overrun Quantified by RTA:** While higher-priority tasks $\tau_1$ and $\tau_2$ continue to meet their deadlines, the lowest-priority task $\tau_3$ suffers excessive preemption, converging to a worst-case response time of **$22\text{ ms}$ against a $20\text{ ms}$ deadline** (an overrun of $+2\text{ ms}$ / Margin: $-2,000\ \mu\text{s}$).

This test validates that EmbedSched:
- Emits the critical finding `autosar_cpu_overload` when $U > 100\%$.
- Emits the critical finding `autosar_deadline_miss` for `tau3`.
- Renders the exact deadline overrun in the executive summary and RTA table with `Verdict: MISS` and negative margin (`-2000.00 µs`).
- Emits a final verdict of **`NOT SCHEDULABLE`**.

---

## 2. Theoretical Background & Specification (Buttazzo Ex. 4.3)

Three periodic tasks on a single core with implicit deadlines ($D_i = T_i$) assigned Rate Monotonic priorities ($T_1 < T_2 < T_3 \implies \text{Priority}(\tau_1) > \text{Priority}(\tau_2) > \text{Priority}(\tau_3)$):

| Task | Execution Time ($C_i$) | Period ($T_i$) | Deadline ($D_i$) | RM Priority |
|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $7\text{ ms}\ (7,000\ \mu\text{s})$ | $7\text{ ms}\ (7,000\ \mu\text{s})$ | **1 (Highest)** |
| $\tau_2$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | **2** |
| $\tau_3$ | $5\text{ ms}\ (5,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | **3 (Lowest)** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{3}{7} \approx 0.42857 \quad (42.86\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{4}{12} = \frac{1}{3} \approx 0.33333 \quad (33.33\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{5}{20} = \frac{1}{4} = 0.25000 \quad (25.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{3} \frac{C_i}{T_i} = \frac{3}{7} + \frac{1}{3} + \frac{1}{4} = \frac{36 + 28 + 21}{84} = \frac{85}{84} \approx \mathbf{1.0119\ (101.19\%)}$$

**Evaluation:**
$$U = 101.19\% > 1.0000\ (100.0\%)$$

Since $U > 1.0$, the CPU is mathematically **OVERLOADED**:
- **Diagnosis:** **OVERLOADED**
- EmbedSched emits:
  ```
  [CRITICAL] [CALCULATED] autosar_cpu_overload
    Core 0: CPU OVERLOADED.
      Utilization : 101.2% > 100%
      Tasks       : 3
      System cannot be schedulable under any priority assignment.
  ```

---

### B. Exact Response Time Analysis (RTA) Iterations

Even though the system is proven unschedulable by utilization, EmbedSched executes the Joseph & Pandya iterative recurrence to identify which individual tasks survive and precisely when the first deadline is missed:

$$R_i^{(0)} = C_i$$
$$R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### 1. Task $\tau_1$ (Priority 1 — Highest Priority)
Task $\tau_1$ suffers no preemption:
$$R_1 = C_1 = \mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$$
$$\text{Margin}_1 = D_1 - R_1 = 7\text{ ms} - 3\text{ ms} = \mathbf{+4\text{ ms}\ (+4,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 2. Task $\tau_2$ (Priority 2)
Task $\tau_2$ is preempted only by $\tau_1$ ($\text{hp}(2) = \{ \tau_1 \}$):

- **Iteration 0 (Seed):**
  $$R_2^{(0)} = C_2 = 4\text{ ms}$$
- **Iteration 1:**
  $$R_2^{(1)} = C_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 4 + \left\lceil \frac{4}{7} \right\rceil \times 3 = 4 + (1 \times 3) = 7\text{ ms}$$
- **Iteration 2:**
  $$R_2^{(2)} = C_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 4 + \left\lceil \frac{7}{7} \right\rceil \times 3 = 4 + (1 \times 3) = \mathbf{7\text{ ms}}$$

**Convergence:**
$$R_2^{(2)} = R_2^{(1)} = \mathbf{7\text{ ms}\ (7,000\ \mu\text{s})}$$
$$\text{Margin}_2 = D_2 - R_2 = 12\text{ ms} - 7\text{ ms} = \mathbf{+5\text{ ms}\ (+5,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 3. Task $\tau_3$ (Priority 3 — Lowest Priority)
Task $\tau_3$ is preempted by both $\tau_1$ ($C_1=3, T_1=7$) and $\tau_2$ ($C_2=4, T_2=12$):

- **Iteration 0 (Seed):**
  $$R_3^{(0)} = C_3 = 5\text{ ms}$$
- **Iteration 1:**
  $$R_3^{(1)} = 5 + \left\lceil \frac{5}{7} \right\rceil \times 3 + \left\lceil \frac{5}{12} \right\rceil \times 4 = 5 + (1 \times 3) + (1 \times 4) = 5 + 3 + 4 = 12\text{ ms}$$
- **Iteration 2:**
  $$R_3^{(2)} = 5 + \left\lceil \frac{12}{7} \right\rceil \times 3 + \left\lceil \frac{12}{12} \right\rceil \times 4 = 5 + (2 \times 3) + (1 \times 4) = 5 + 6 + 4 = 15\text{ ms}$$
- **Iteration 3:**
  $$R_3^{(3)} = 5 + \left\lceil \frac{15}{7} \right\rceil \times 3 + \left\lceil \frac{15}{12} \right\rceil \times 4 = 5 + (2 \times 3) + (2 \times 4) = 5 + 6 + 8 = 19\text{ ms}$$
- **Iteration 4:**
  $$R_3^{(4)} = 5 + \left\lceil \frac{19}{7} \right\rceil \times 3 + \left\lceil \frac{19}{12} \right\rceil \times 4 = 5 + (3 \times 3) + (2 \times 4) = 5 + 9 + 8 = 22\text{ ms}$$
- **Iteration 5:**
  $$R_3^{(5)} = 5 + \left\lceil \frac{22}{7} \right\rceil \times 3 + \left\lceil \frac{22}{12} \right\rceil \times 4 = 5 + (4 \times 3) + (2 \times 4) = 5 + 12 + 8 = 25\text{ ms}$$

*(Notice: During iteration 4, $R_3^{(4)} = 22\text{ ms} > D_3 = 20\text{ ms}$. EmbedSched's early-termination condition detects the overrun immediately when $R > D$, recording $R_3 = 22,000\ \mu\text{s}$).*

**Deadline Evaluation:**
$$R_3 = 22\text{ ms} > D_3 = 20\text{ ms}$$
$$\text{Margin}_3 = D_3 - R_3 = 20\text{ ms} - 22\text{ ms} = \mathbf{-2\text{ ms}\ (-2,000\ \mu\text{s})} \implies \mathbf{DEADLINE\ MISS\ (FAIL)}$$

---

## 4. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo Chapter 4 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Total Core Utilization ($U$)** | $101.19\%$ | `101.2%` | :white_check_mark: Exact |
| **Utilization Status** | `OVERLOADED` | `OVERLOADED (> 100%)` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $3\text{ ms}\ (3,000\ \mu\text{s})$ | `3000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Margin** | $+4\text{ ms}\ (+4,000\ \mu\text{s})$ | `+4000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $7\text{ ms}\ (7,000\ \mu\text{s})$ | `7000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Margin** | $+5\text{ ms}\ (+5,000\ \mu\text{s})$ | `+5000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ WCRT ($R_3$)** | $22\text{ ms}\ (22,000\ \mu\text{s})$ | `22000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Margin** | $\mathbf{-2\text{ ms}\ (-2,000\ \mu\text{s})}$ | `-2000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Verdict** | `MISS` | `MISS` | :white_check_mark: Exact |
| **Overall System Verdict** | `NOT SCHEDULABLE` | `NOT SCHEDULABLE (FAIL)` | :white_check_mark: Exact |

---

## 5. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_3

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
