# Buttazzo Test Suite — Test Case 1: Classic Three-Task RM Schedulability

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Chapter 4 (Fixed-Priority Servers / Rate Monotonic Schedulability), Example 4.1.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization Diagnosis:** `INDETERMINATE (Warning Emitted: autosar_utilization_warning)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 1 in the `buttazo_test` suite directly reproduces **Example 4.1 from Giorgio Buttazzo's classic textbook *Hard Real-Time Computing Systems***. 

This textbook benchmark represents the foundational proof that **Liu & Layland's Rate Monotonic Utilization Bound is a *sufficient* condition, but NOT a *necessary* condition**:
1. When a task set has total utilization $U \le U_{\text{bound}}(n) = n(2^{1/n}-1)$, it is guaranteed to be schedulable.
2. When $U > U_{\text{bound}}(n)$ but $U \le 1.00$, the utilization test is **inconclusive (INDETERMINATE)**. A naive scheduler analysis tool that only evaluates utilization would reject the firmware as unschedulable.
3. However, exact **Response Time Analysis (RTA)** using the Joseph & Pandya iterative recurrence proves that all tasks converge to response times well within their deadlines.

This test validates that EmbedSched:
- Accurately flags the utilization warning `autosar_utilization_warning` with an overall score penalty (-15 points).
- Correctly marks the core's utilization status as **INDETERMINATE**.
- Proceeds to execute exact RTA and correctly declares the system **SCHEDULABLE** with positive margins on every task.

---

## 2. Theoretical Background & Specification (Buttazzo Ex. 4.1)

A single processor runs three periodic tasks with implicit deadlines ($D_i = T_i$) assigned fixed priorities according to Rate Monotonic policy ($T_1 < T_2 < T_3 \implies \text{Priority}(\tau_1) > \text{Priority}(\tau_2) > \text{Priority}(\tau_3)$):

| Task | Execution Time ($C_i$) | Period ($T_i$) | Deadline ($D_i$) | RM Priority |
|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $1\text{ ms}\ (1,000\ \mu\text{s})$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | **1 (Highest)** |
| $\tau_2$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | **2** |
| $\tau_3$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | **3 (Lowest)** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total System Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{1}{4} = 0.2500 \quad (25.0\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{2}{6} \approx 0.3333 \quad (33.33\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{3}{12} = 0.2500 \quad (25.0\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{3} \frac{C_i}{T_i} = 0.2500 + 0.3333 + 0.2500 = \frac{3}{12} + \frac{4}{12} + \frac{3}{12} = \frac{10}{12} = \frac{5}{6} \approx \mathbf{0.8333\ (83.33\%)}$$

### B. Liu & Layland RM Bound Comparison

For $n = 3$ periodic tasks, the theoretical Liu & Layland schedulability bound is:
$$U_{\text{bound}}(3) = 3 \times \left(2^{1/3} - 1\right) = 3 \times (1.259921 - 1) = 3 \times 0.259921 \approx \mathbf{0.7798\ (77.98\%)}$$

**Evaluation:**
$$U = 83.33\% > U_{\text{bound}}(3) = 77.98\%$$

Since $U > U_{\text{bound}}$, Liu & Layland's sufficient condition is violated:
- **Verdict on Utilization:** **INDETERMINATE**
- EmbedSched emits finding:
  ```
  [WARNING] [CALCULATED] autosar_utilization_warning
    Core 0: utilization in INDETERMINATE zone.
      Utilization   : 83.3%
      RM bound      : 78.0% (n=3 tasks)
  ```

---

### C. Exact Response Time Analysis (RTA) Iterations

Because utilization falls in the indeterminate zone ($0.7798 < U \le 1.00$), exact worst-case response times must be calculated using the Joseph & Pandya iterative recurrence:

$$R_i^{(0)} = C_i$$
$$R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### 1. Task $\tau_1$ (Priority 1 — Highest Priority)
Task $\tau_1$ has no higher-priority tasks ($\text{hp}(1) = \emptyset$):
$$R_1 = C_1 = \mathbf{1\text{ ms}\ (1,000\ \mu\text{s})}$$
$$\text{Margin}_1 = D_1 - R_1 = 4\text{ ms} - 1\text{ ms} = \mathbf{+3\text{ ms}\ (+3,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 2. Task $\tau_2$ (Priority 2)
Task $\tau_2$ is preempted only by $\tau_1$ ($\text{hp}(2) = \{ \tau_1 \}$):

- **Iteration 0 (Seed):**
  $$R_2^{(0)} = C_2 = 2\text{ ms}$$
- **Iteration 1:**
  $$R_2^{(1)} = C_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 2 + \left\lceil \frac{2}{4} \right\rceil \times 1 = 2 + (1 \times 1) = 3\text{ ms}$$
- **Iteration 2:**
  $$R_2^{(2)} = C_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 2 + \left\lceil \frac{3}{4} \right\rceil \times 1 = 2 + (1 \times 1) = \mathbf{3\text{ ms}}$$

**Convergence:**
$$R_2^{(2)} = R_2^{(1)} = \mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$$
$$\text{Margin}_2 = D_2 - R_2 = 6\text{ ms} - 3\text{ ms} = \mathbf{+3\text{ ms}\ (+3,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 3. Task $\tau_3$ (Priority 3 — Lowest Priority)
Task $\tau_3$ is preempted by both $\tau_1$ and $\tau_2$ ($\text{hp}(3) = \{ \tau_1, \tau_2 \}$):

- **Iteration 0 (Seed):**
  $$R_3^{(0)} = C_3 = 3\text{ ms}$$
- **Iteration 1:**
  $$R_3^{(1)} = 3 + \left\lceil \frac{3}{4} \right\rceil \times 1 + \left\lceil \frac{3}{6} \right\rceil \times 2 = 3 + (1 \times 1) + (1 \times 2) = 3 + 1 + 2 = 6\text{ ms}$$
- **Iteration 2:**
  $$R_3^{(2)} = 3 + \left\lceil \frac{6}{4} \right\rceil \times 1 + \left\lceil \frac{6}{6} \right\rceil \times 2 = 3 + (2 \times 1) + (1 \times 2) = 3 + 2 + 2 = 7\text{ ms}$$
- **Iteration 3:**
  $$R_3^{(3)} = 3 + \left\lceil \frac{7}{4} \right\rceil \times 1 + \left\lceil \frac{7}{6} \right\rceil \times 2 = 3 + (2 \times 1) + (2 \times 2) = 3 + 2 + 4 = 9\text{ ms}$$
- **Iteration 4:**
  $$R_3^{(4)} = 3 + \left\lceil \frac{9}{4} \right\rceil \times 1 + \left\lceil \frac{9}{6} \right\rceil \times 2 = 3 + (3 \times 1) + (2 \times 2) = 3 + 3 + 4 = 10\text{ ms}$$
- **Iteration 5:**
  $$R_3^{(5)} = 3 + \left\lceil \frac{10}{4} \right\rceil \times 1 + \left\lceil \frac{10}{6} \right\rceil \times 2 = 3 + (3 \times 1) + (2 \times 2) = 3 + 3 + 4 = \mathbf{10\text{ ms}}$$

**Convergence:**
$$R_3^{(5)} = R_3^{(4)} = \mathbf{10\text{ ms}\ (10,000\ \mu\text{s})}$$
$$\text{Margin}_3 = D_3 - R_3 = 12\text{ ms} - 10\text{ ms} = \mathbf{+2\text{ ms}\ (+2,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

## 4. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo Chapter 4 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Total Core Utilization ($U$)** | $83.33\%$ | `83.3%` | :white_check_mark: Exact |
| **Liu & Layland Bound ($U_{\text{bound}}$)** | $77.98\%$ | `78.0%` | :white_check_mark: Exact |
| **Utilization Status** | `INDETERMINATE` | `INDETERMINATE (above RM bound)` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $1\text{ ms}\ (1,000\ \mu\text{s})$ | `1000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Margin** | $+3\text{ ms}\ (+3,000\ \mu\text{s})$ | `+3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $3\text{ ms}\ (3,000\ \mu\text{s})$ | `3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Margin** | $+3\text{ ms}\ (+3,000\ \mu\text{s})$ | `+3000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ WCRT ($R_3$)** | $10\text{ ms}\ (10,000\ \mu\text{s})$ | `10000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Margin** | $+2\text{ ms}\ (+2,000\ \mu\text{s})$ | `+2000.00 µs` | :white_check_mark: Exact |
| **Overall System Verdict** | `SCHEDULABLE` | `PASS (SCHEDULABLE)` | :white_check_mark: Exact |

---

## 5. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_1

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
