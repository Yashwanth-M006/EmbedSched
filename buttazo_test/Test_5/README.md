# Buttazzo Test Suite — Test Case 5: Earliest Deadline First (EDF) Schedulability (Buttazzo Ex. 3.1)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Chapter 3 (Dynamic-Priority Schedulability / Earliest Deadline First), Example 3.1.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization Diagnosis:** `GUARANTEED (80.0% <= 100.0% EDF Bound)`  
> **Algorithm:** `EDF (Earliest Deadline First)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 5 in the `buttazo_test` suite reproduces **Example 3.1 from Chapter 3 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark evaluates **dynamic-priority scheduling under the Earliest Deadline First (EDF) algorithm**:
1. **100% Schedulability Bound for Implicit Deadlines:** Liu & Layland (1973) proved that under preemptive EDF with implicit deadlines ($D_i = T_i$), a periodic task set is schedulable **if and only if total processor utilization does not exceed 100%**:
   $$U = \sum_{i=1}^{n} \frac{C_i}{T_i} \le 1.00$$
   Unlike fixed-priority RM (where $U_{\text{bound}} \approx 69.3\%$ for large $n$), EDF can fully utilize 100% of the CPU without missing a single deadline.
2. **Necessary & Sufficient Utilization Check:** Because all deadlines equal periods ($D_i = T_i$) and $U = 80\% \le 100\%$, Processor Demand Analysis (PDA) is not required. The utilization check alone guarantees schedulability.
3. **Dynamic-Priority Response Time Formulation:** Under EDF, tasks do not have static priorities; job priority is determined dynamically at runtime based on absolute deadlines ($d_{i,k} = r_{i,k} + D_i$). EmbedSched executes EDF-specific response time analysis across activations in the first busy period (Spuri 1996), calculating accurate worst-case response times and margins.

---

## 2. Theoretical Background & Specification (Buttazzo Ex. 3.1)

Three periodic tasks on a single core running under dynamic preemptive EDF with implicit deadlines ($D_i = T_i$):

| Task | Execution Time ($C_i$) | Period ($T_i$) | Deadline ($D_i$) | Scheduling Policy |
|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $1\text{ ms}\ (1,000\ \mu\text{s})$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | $4\text{ ms}\ (4,000\ \mu\text{s})$ | **Dynamic EDF (Earliest $d_i(t)$)** |
| $\tau_2$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $5\text{ ms}\ (5,000\ \mu\text{s})$ | $5\text{ ms}\ (5,000\ \mu\text{s})$ | **Dynamic EDF (Earliest $d_i(t)$)** |
| $\tau_3$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | $20\text{ ms}\ (20,000\ \mu\text{s})$ | **Dynamic EDF (Earliest $d_i(t)$)** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{1}{4} = 0.25000 \quad (25.00\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{2}{5} = 0.40000 \quad (40.00\%)$$
$$U_3 = \frac{C_3}{T_3} = \frac{3}{20} = 0.15000 \quad (15.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{3} \frac{C_i}{T_i} = 0.2500 + 0.4000 + 0.1500 = \mathbf{0.8000\ (80.00\%)}$$

**EDF Bound Comparison:**
For implicit deadlines under EDF:
$$U_{\text{EDF\_bound}} = 1.0000\ (100.0\%)$$
$$U = 80.0\% \le 100.0\% \implies \mathbf{GUARANTEED\ SCHEDULABLE}$$

EmbedSched displays:
```text
Core 0  (3 periodic tasks):
  [████████████████████████████████░░░░░░░|░]  80.0%  EDF bound: 100.0%  →  GUARANTEED (below EDF bound)

● VERDICT: SCHEDULABLE  — all tasks meet their deadlines (per RTA).  [CALCULATED]
```

---

### B. Dynamic-Priority Response Time Analysis (Spuri 1996 / Buttazzo §3.4)

Under EDF, a task $\tau_i$'s response time is not fixed across all activations because competing tasks' relative priorities invert depending on whose absolute deadline is earlier. The response time for the $p$-th activation ($p \ge 0$) with absolute deadline $d_{i,p} = p \cdot T_i + D_i$ is evaluated by fixed-point iteration:

$$w = (p + 1) C_i + \sum_{j \ne i} \min\left( \max\left(0, \left\lfloor \frac{d_{i,p} - D_j}{T_j} \right\rfloor + 1\right), \left\lceil \frac{w}{T_j} \right\rceil \right) C_j$$
$$R_{i,p} = w - p \cdot T_i$$
$$R_i = \max_{p \ge 0} (R_{i,p})$$

#### 1. Task $\tau_1$ ($T_1=4\text{ ms}, D_1=4\text{ ms}, C_1=1\text{ ms}$)
During its worst-case initial release ($p=0, d_{1,0} = 4\text{ ms}$):
- $\tau_1$'s deadline ($4\text{ ms}$) is earlier than $\tau_2$'s deadline ($5\text{ ms}$) and $\tau_3$'s deadline ($20\text{ ms}$).
- Neither task can preempt $\tau_1$.
$$R_1 = \mathbf{1,000\ \mu\text{s}\ (1\text{ ms})} \le D_1 = 4,000\ \mu\text{s} \quad (\mathbf{Margin: +3,000\ \mu\text{s} / +3\text{ ms},\ PASS})$$

---

#### 2. Task $\tau_2$ ($T_2=5\text{ ms}, D_2=5\text{ ms}, C_2=2\text{ ms}$)
At $p=0, d_{2,0} = 5\text{ ms}$:
- $\tau_1$ has deadline $4\text{ ms} < 5\text{ ms}$, executing ahead of $\tau_2$ ($C_1 = 1\text{ ms}$).
- $\tau_3$ has deadline $20\text{ ms} > 5\text{ ms}$, executing after $\tau_2$.
$$R_2 = C_2 + C_1 = 2 + 1 = \mathbf{3,000\ \mu\text{s}\ (3\text{ ms})} \le D_2 = 5,000\ \mu\text{s} \quad (\mathbf{Margin: +2,000\ \mu\text{s} / +2\text{ ms},\ PASS})$$

---

#### 3. Task $\tau_3$ ($T_3=20\text{ ms}, D_3=20\text{ ms}, C_3=3\text{ ms}$)
At $p=0, d_{3,0} = 20\text{ ms}$:
- $\tau_1$ releases jobs with deadlines at $4, 8, 12, 16, 20\text{ ms}$ (all $\le 20\text{ ms}$).
- $\tau_2$ releases jobs with deadlines at $5, 10, 15, 20\text{ ms}$ (all $\le 20\text{ ms}$).
- The fixed-point iteration converges at:
$$R_3 = \mathbf{10,000\ \mu\text{s}\ (10\text{ ms})} \le D_3 = 20,000\ \mu\text{s} \quad (\mathbf{Margin: +10,000\ \mu\text{s} / +10\text{ ms},\ PASS})$$

---

## 4. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo Chapter 3 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Configured Algorithm** | `EDF` | `EDF` | :white_check_mark: Exact |
| **Total Core Utilization ($U$)** | $80.00\%$ | `80.0%` | :white_check_mark: Exact |
| **EDF Schedulability Bound** | $100.00\%$ | `100.0%` | :white_check_mark: Exact |
| **Utilization Status** | `GUARANTEED` | `GUARANTEED (below EDF bound)` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $1\text{ ms}\ (1,000\ \mu\text{s})$ | `1000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Deadline Margin** | $+3\text{ ms}\ (+3,000\ \mu\text{s})$ | `+3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $3\text{ ms}\ (3,000\ \mu\text{s})$ | `3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Deadline Margin** | $+2\text{ ms}\ (+2,000\ \mu\text{s})$ | `+2000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ WCRT ($R_3$)** | $10\text{ ms}\ (10,000\ \mu\text{s})$ | `10000.00 µs` | :white_check_mark: Exact |
| **$\tau_3$ Deadline Margin** | $+10\text{ ms}\ (+10,000\ \mu\text{s})$ | `+10000.00 µs` | :white_check_mark: Exact |
| **Overall System Verdict** | `SCHEDULABLE` | `PASS (SCHEDULABLE)` | :white_check_mark: Exact |

---

## 5. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_5

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
