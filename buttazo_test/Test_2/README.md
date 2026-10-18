# Buttazzo Test Suite — Test Case 2: RM Critical Boundary & Zero Margin (Buttazzo Ex. 4.2)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Chapter 4 (Fixed-Priority Servers / Rate Monotonic Schedulability), Example 4.2.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization Diagnosis:** `INDETERMINATE (Warning Emitted: autosar_utilization_warning)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 2 in the `buttazo_test` suite reproduces **Example 4.2 from Giorgio Buttazzo's classic textbook *Hard Real-Time Computing Systems***.

This textbook benchmark evaluates a crucial **corner case** in real-time schedulability analysis:
1. **High Processor Utilization:** The total utilization is $U \approx 92.86\%$, far above the Liu & Layland bound for three tasks ($77.98\%$).
2. **Exact Critical Boundary ($R = D$):** Task $\tau_3$ experiences heavy interference from higher-priority tasks $\tau_1$ and $\tau_2$. Its worst-case response time converges to **exactly its deadline** ($R_3 = 20\text{ ms} = D_3$).
3. **Boundary Condition Compliance:** Real-time scheduling theory defines schedulability as $R_i \le D_i$ (less than or equal to deadline), NOT strictly $R_i < D_i$. Therefore, a response time equal to the deadline with **zero margin ($\text{Margin} = 0\text{ ms}$)** is strictly **schedulable (PASS)**.
4. **Full 420 ms Hyperperiod Simulation:** The periods are $7, 12, 20\text{ ms}$ with an exact Least Common Multiple:
   $$\text{LCM}(7, 12, 20) = 420\text{ ms}$$
   With only 116 total activations across the hyperperiod (60 of $\tau_1$, 35 of $\tau_2$, 21 of $\tau_3$), EmbedSched simulates the entire 420 ms timeline without false-positive capping.
5. **Context-Aware Jitter Assessment:** Because the core operates at high utilization ($92.9\%$), preemption jitter on lower-priority tasks ($\approx 22.6\%$ for $\tau_2$ and $28.3\%$ for $\tau_3$) is a natural physical consequence of irregular preemption. EmbedSched recognizes that priority assignment is already optimal (Rate Monotonic) and issues a context-aware recommendation: *"expected at high utilization; reduce utilization if jitter affects control stability"*.

---

## 2. Theoretical Background & Specification (Buttazzo Ex. 4.2)

Three periodic tasks on a single core with implicit deadlines ($D_i = T_i$) assigned Rate Monotonic priorities ($T_1 < T_2 < T_3 \implies \text{Priority}(\tau_1) > \text{Priority}(\tau_2) > \text{Priority}(\tau_3)$):

| Task | Execution Time ($C_i$) | Period ($T_i$) | Deadline ($D_i$) | RM Priority |
|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $7\text{ ms}\ (7,000\ \mu\text{s})$ | $7\text{ ms}\ (7,000\ \mu\text{s})$ | **1 (Highest)** |
| $\tau_2$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | $12\text{ ms}\ (12,000\ \mu\text{s})$ | **2** |
| $\tau_3$ | $5\text{ ms}\ (5,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | **3 (Lowest)** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{3}{7} \approx 0.42857 \quad (42.86\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{3}{12} = 0.25000 \quad (25.00\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{5}{20} = 0.25000 \quad (25.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{3} \frac{C_i}{T_i} = \frac{3}{7} + \frac{1}{4} + \frac{1}{4} = \frac{3}{7} + \frac{1}{2} = \frac{13}{14} \approx \mathbf{0.92857\ (92.86\%)}$$

### B. Liu & Layland RM Bound Comparison

For $n = 3$ periodic tasks:
$$U_{\text{bound}}(3) = 3 \times \left(2^{1/3} - 1\right) \approx \mathbf{0.7798\ (77.98\%)}$$

**Evaluation:**
$$U = 92.86\% > U_{\text{bound}}(3) = 77.98\%$$

Since $U > U_{\text{bound}}$ but $U \le 1.00$:
- **Utilization Status:** **INDETERMINATE**
- EmbedSched emits:
  ```
  [WARNING] [CALCULATED] autosar_utilization_warning
    Core 0: utilization in INDETERMINATE zone.
      Utilization   : 92.9%
      RM bound      : 78.0% (n=3 tasks)
  ```

---

### C. Exact Response Time Analysis (RTA) Iterations

Using the Joseph & Pandya iterative recurrence:
$$R_i^{(0)} = C_i$$
$$R_i^{(k+1)} = C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### 1. Task $\tau_1$ (Priority 1 — Highest Priority)
Task $\tau_1$ has no higher-priority tasks:
$$R_1 = C_1 = \mathbf{3\text{ ms}\ (3,000\ \mu\text{s})}$$
$$\text{Margin}_1 = D_1 - R_1 = 7\text{ ms} - 3\text{ ms} = \mathbf{+4\text{ ms}\ (+4,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 2. Task $\tau_2$ (Priority 2)
Task $\tau_2$ is preempted only by $\tau_1$ ($\text{hp}(2) = \{ \tau_1 \}$):

- **Iteration 0 (Seed):**
  $$R_2^{(0)} = C_2 = 3\text{ ms}$$
- **Iteration 1:**
  $$R_2^{(1)} = C_2 + \left\lceil \frac{R_2^{(0)}}{T_1} \right\rceil C_1 = 3 + \left\lceil \frac{3}{7} \right\rceil \times 3 = 3 + (1 \times 3) = 6\text{ ms}$$
- **Iteration 2:**
  $$R_2^{(2)} = C_2 + \left\lceil \frac{R_2^{(1)}}{T_1} \right\rceil C_1 = 3 + \left\lceil \frac{6}{7} \right\rceil \times 3 = 3 + (1 \times 3) = \mathbf{6\text{ ms}}$$

**Convergence:**
$$R_2^{(2)} = R_2^{(1)} = \mathbf{6\text{ ms}\ (6,000\ \mu\text{s})}$$
$$\text{Margin}_2 = D_2 - R_2 = 12\text{ ms} - 6\text{ ms} = \mathbf{+6\text{ ms}\ (+6,000\ \mu\text{s})} \quad (\mathbf{PASS})$$

---

#### 3. Task $\tau_3$ (Priority 3 — Lowest Priority)
Task $\tau_3$ is preempted by both $\tau_1$ and $\tau_2$ ($\text{hp}(3) = \{ \tau_1, \tau_2 \}$):

- **Iteration 0 (Seed):**
  $$R_3^{(0)} = C_3 = 5\text{ ms}$$
- **Iteration 1:**
  $$R_3^{(1)} = 5 + \left\lceil \frac{5}{7} \right\rceil \times 3 + \left\lceil \frac{5}{12} \right\rceil \times 3 = 5 + (1 \times 3) + (1 \times 3) = 5 + 3 + 3 = 11\text{ ms}$$
- **Iteration 2:**
  $$R_3^{(2)} = 5 + \left\lceil \frac{11}{7} \right\rceil \times 3 + \left\lceil \frac{11}{12} \right\rceil \times 3 = 5 + (2 \times 3) + (1 \times 3) = 5 + 6 + 3 = 14\text{ ms}$$
- **Iteration 3:**
  $$R_3^{(3)} = 5 + \left\lceil \frac{14}{7} \right\rceil \times 3 + \left\lceil \frac{14}{12} \right\rceil \times 3 = 5 + (2 \times 3) + (2 \times 3) = 5 + 6 + 6 = 17\text{ ms}$$
- **Iteration 4:**
  $$R_3^{(4)} = 5 + \left\lceil \frac{17}{7} \right\rceil \times 3 + \left\lceil \frac{17}{12} \right\rceil \times 3 = 5 + (3 \times 3) + (2 \times 3) = 5 + 9 + 6 = 20\text{ ms}$$
- **Iteration 5:**
  $$R_3^{(5)} = 5 + \left\lceil \frac{20}{7} \right\rceil \times 3 + \left\lceil \frac{20}{12} \right\rceil \times 3 = 5 + (3 \times 3) + (2 \times 3) = 5 + 9 + 6 = \mathbf{20\text{ ms}}$$

**Convergence:**
$$R_3^{(5)} = R_3^{(4)} = \mathbf{20\text{ ms}\ (20,000\ \mu\text{s})}$$

**Deadline Evaluation:**
$$R_3 = 20\text{ ms} \le D_3 = 20\text{ ms}$$
$$\text{Margin}_3 = D_3 - R_3 = 20\text{ ms} - 20\text{ ms} = \mathbf{0.00\ \mu\text{s}\ (0\text{ ms})} \quad (\mathbf{PASS})$$

> **Critical Boundary Conclusion:** $R_3 \le D_3$ holds true with zero slack ($\text{Margin}_3 = 0$). EmbedSched properly distinguishes that $R \le D$ is the legal passing condition, certifying the system as **SCHEDULABLE**.

---

## 4. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo Chapter 4 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Total Core Utilization ($U$)** | $92.86\%$ | `92.9%` | :white_check_mark: Exact |
| **Liu & Layland Bound ($U_{\text{bound}}$)** | $77.98\%$ | `78.0%` | :white_check_mark: Exact |
| **Utilization Status** | `INDETERMINATE` | `INDETERMINATE (above RM bound)` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $3\text{ ms}\ (3,000\ \mu\text{s})$ | `3000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Margin** | $+4\text{ ms}\ (+4,000\ \mu\text{s})$ | `+4000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $6\text{ ms}\ (6,000\ \mu\text{s})$ | `6000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Margin** | $+6\text{ ms}\ (+6,000\ \mu\text{s})$ | `+6000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ WCRT ($R_3$)** | $20\text{ ms}\ (20,000\ \mu\text{s})$ | `20000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Margin** | $\mathbf{0\text{ ms}\ (0.00\ \mu\text{s})}$ | `0.00 µs` | :white_check_mark: Exact |
| **Overall System Verdict** | `SCHEDULABLE` | `PASS (SCHEDULABLE)` | :white_check_mark: Exact |

---

## 5. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_2

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
