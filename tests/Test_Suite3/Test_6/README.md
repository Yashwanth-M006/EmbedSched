# Buttazzo Test Suite — Test Case 6: EDF Constrained Deadlines & Processor Demand Analysis (Buttazzo §5.5)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 5.5 (Processor Demand Criterion under EDF), Example 3.2.  
> **Status:** `PASS (SCHEDULABLE)`  
> **Utilization:** `63.3% <= 100.0% (PASS, but insufficient for constrained deadlines)`  
> **Demand Bound Analysis:** `h(L) <= L across all 7 deadline testing points (Tightest Margin: +2,000 µs at L = 7,000 µs)`  
> **Algorithm:** `EDF (Constrained Deadlines D < T)`  
> **Confidence:** `[CALCULATED]`  
> **Scheduler:** Single-Core Preemptive Earliest Deadline First (EDF)

---

## 1. What This Test Signifies

Test Case 6 in the `buttazo_test` suite reproduces **Example 3.2 from Section 5.5 of Giorgio Buttazzo's textbook *Hard Real-Time Computing Systems***.

This textbook benchmark evaluates **dynamic-priority EDF scheduling when tasks have constrained deadlines ($D_i < T_i$)**:
1. **The Insufficiency of the Utilization Test:** For constrained deadlines, the simple utilization test ($U \le 1.0$) is a *necessary* condition, but **NOT a sufficient condition**. A task set with only $U = 63.3\%$ can potentially miss deadlines if task arrival bursts demand excessive computation within short initial windows.
2. **Baruah's Processor Demand Analysis (PDA):** Schedulability can only be guaranteed by evaluating the **Demand Bound Function** $h(L)$ (Baruah, Mok, & Rosier, 1990) across all absolute deadlines up to the hyperperiod $H = \text{LCM}(T_1, T_2) = 30\text{ ms}$:
   $$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) C_i \le L, \quad \forall L \in \mathcal{D}$$
3. **Automated Detection of Constrained Deadlines:** EmbedSched automatically detects that $D_1 < T_1$ ($5 < 6\text{ ms}$) and $D_2 < T_2$ ($7 < 10\text{ ms}$), bypasses the naive utilization check, activates exact Processor Demand Analysis, and identifies the tightest margin point ($L = 7\text{ ms}$).

---

## 2. Theoretical Background & Specification (Buttazzo §5.5 Ex. 3.2)

Two periodic tasks with constrained deadlines ($D_i < T_i$) scheduled under preemptive EDF:

| Task | Execution Time ($C_i$) | Period ($T_i$) | Relative Deadline ($D_i$) | Constrained? | Scheduling Policy |
|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | $2\text{ ms}\ (2,000\ \mu\text{s})$ | $6\text{ ms}\ (6,000\ \mu\text{s})$ | $\mathbf{5\text{ ms}\ (5,000\ \mu\text{s})}$ | $D_1 < T_1\ (5 < 6)$ | **Dynamic EDF** |
| $\tau_2$ | $3\text{ ms}\ (3,000\ \mu\text{s})$ | $10\text{ ms}\ (10,000\ \mu\text{s})$ | $\mathbf{7\text{ ms}\ (7,000\ \mu\text{s})}$ | $D_2 < T_2\ (7 < 10)$ | **Dynamic EDF** |

---

## 3. Step-by-Step Mathematical Calculations

### A. Total Processor Utilization Check

The individual task utilizations are:
$$U_1 = \frac{C_1}{T_1} = \frac{2}{6} = \frac{1}{3} \approx 0.33333 \quad (33.33\%)$$
$$U_2 = \frac{C_2}{T_2} = \frac{3}{10} = 0.30000 \quad (30.00\%)$$

Total processor utilization:
$$U = \sum_{i=1}^{2} \frac{C_i}{T_i} = \frac{1}{3} + \frac{3}{10} = \frac{19}{30} \approx \mathbf{0.63333\ (63.33\%)}$$

**Evaluation:**
$$U = 63.33\% \le 1.0000\ (100.0\%)$$
While the system passes the utilization check, because $D_i < T_i$, this condition is **not sufficient**. Schedulability must be proven via processor demand analysis.

---

### B. Hyperperiod & Scheduling Checkpoint Generation

The hyperperiod is the Least Common Multiple of task periods:
$$H = \text{LCM}(T_1, T_2) = \text{LCM}(6\text{ ms}, 10\text{ ms}) = \mathbf{30\text{ ms}\ (30,000\ \mu\text{s})}$$

The set of testing checkpoints $\mathcal{D}$ comprises all absolute deadlines $k \cdot T_i + D_i \le H$:
- For $\tau_1$ ($T_1=6, D_1=5$):
  $$k=0 \implies 5\text{ ms}$$
  $$k=1 \implies 6 + 5 = 11\text{ ms}$$
  $$k=2 \implies 12 + 5 = 17\text{ ms}$$
  $$k=3 \implies 18 + 5 = 23\text{ ms}$$
  $$k=4 \implies 24 + 5 = 29\text{ ms}$$
- For $\tau_2$ ($T_2=10, D_2=7$):
  $$k=0 \implies 7\text{ ms}$$
  $$k=1 \implies 10 + 7 = 17\text{ ms}$$
  $$k=2 \implies 20 + 7 = 27\text{ ms}$$

Combining and ordering all unique checkpoints up to $H=30\text{ ms}$:
$$\mathcal{D} = \{ 5, 7, 11, 17, 23, 27, 29 \}\text{ ms}$$

---

### C. Evaluation of the Demand Bound Function $h(L)$

The demand bound function is:
$$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) C_i$$

Evaluating $h(L)$ at all 7 scheduling checkpoints:

1. **At $L = 5\text{ ms}$:**
   $$h(5) = \left\lfloor \frac{5 + 6 - 5}{6} \right\rfloor \times 2 + \left\lfloor \frac{5 + 10 - 7}{10} \right\rfloor \times 3 = \lfloor 1 \rfloor \times 2 + \lfloor 0.8 \rfloor \times 3 = 2 + 0 = \mathbf{2\text{ ms}}$$
   $$h(5) = 2 \le L = 5 \implies \mathbf{PASS\ (Margin: +3\text{ ms})}$$

2. **At $L = 7\text{ ms}$ (The Tightest Margin Point):**
   $$h(7) = \left\lfloor \frac{7 + 6 - 5}{6} \right\rfloor \times 2 + \left\lfloor \frac{7 + 10 - 7}{10} \right\rfloor \times 3 = \lfloor 1.33 \rfloor \times 2 + \lfloor 1 \rfloor \times 3 = (1 \times 2) + (1 \times 3) = \mathbf{5\text{ ms}}$$
   $$h(7) = 5 \le L = 7 \implies \mathbf{PASS\ (Tightest\ Margin: +2\text{ ms}\ /\ +2,000\ \mu\text{s})}$$

3. **At $L = 11\text{ ms}$:**
   $$h(11) = \left\lfloor \frac{11 + 1}{6} \right\rfloor \times 2 + \left\lfloor \frac{11 + 3}{10} \right\rfloor \times 3 = \lfloor 2 \rfloor \times 2 + \lfloor 1.4 \rfloor \times 3 = 4 + 3 = \mathbf{7\text{ ms}}$$
   $$h(11) = 7 \le L = 11 \implies \mathbf{PASS\ (Margin: +4\text{ ms})}$$

4. **At $L = 17\text{ ms}$:**
   $$h(17) = \left\lfloor \frac{17 + 1}{6} \right\rfloor \times 2 + \left\lfloor \frac{17 + 3}{10} \right\rfloor \times 3 = \lfloor 3 \rfloor \times 2 + \lfloor 2 \rfloor \times 3 = 6 + 6 = \mathbf{12\text{ ms}}$$
   $$h(17) = 12 \le L = 17 \implies \mathbf{PASS\ (Margin: +5\text{ ms})}$$

5. **At $L = 23\text{ ms}$:**
   $$h(23) = \left\lfloor \frac{23 + 1}{6} \right\rfloor \times 2 + \left\lfloor \frac{23 + 3}{10} \right\rfloor \times 3 = \lfloor 4 \rfloor \times 2 + \lfloor 2.6 \rfloor \times 3 = 8 + 6 = \mathbf{14\text{ ms}}$$
   $$h(23) = 14 \le L = 23 \implies \mathbf{PASS\ (Margin: +9\text{ ms})}$$

6. **At $L = 27\text{ ms}$:**
   $$h(27) = \left\lfloor \frac{27 + 1}{6} \right\rfloor \times 2 + \left\lfloor \frac{27 + 3}{10} \right\rfloor \times 3 = \lfloor 4.67 \rfloor \times 2 + \lfloor 3 \rfloor \times 3 = 8 + 9 = \mathbf{17\text{ ms}}$$
   $$h(27) = 17 \le L = 27 \implies \mathbf{PASS\ (Margin: +10\text{ ms})}$$

7. **At $L = 29\text{ ms}$:**
   $$h(29) = \left\lfloor \frac{29 + 1}{6} \right\rfloor \times 2 + \left\lfloor \frac{29 + 3}{10} \right\rfloor \times 3 = \lfloor 5 \rfloor \times 2 + \lfloor 3.2 \rfloor \times 3 = 10 + 9 = \mathbf{19\text{ ms}}$$
   $$h(29) = 19 \le L = 29 \implies \mathbf{PASS\ (Margin: +10\text{ ms})}$$

**Processor Demand Conclusion:**
$$\forall L \in \mathcal{D}, \quad h(L) \le L \implies \mathbf{SCHEDULABLE}$$
The minimum slack across all points is:
$$\text{Tightest Margin} = \min_{L \in \mathcal{D}} (L - h(L)) = 7 - 5 = \mathbf{2\text{ ms}\ (2,000\ \mu\text{s})\ at\ L = 7\text{ ms}}$$

---

### D. Exact Response Times under Preemptive EDF

Evaluating activations across the first busy period:
- **Task $\tau_1$:**
  $$R_1 = C_1 = \mathbf{2,000\ \mu\text{s}\ (2\text{ ms})} \le D_1 = 5,000\ \mu\text{s} \quad (\mathbf{Margin: +3,000\ \mu\text{s} / +3\text{ ms},\ PASS})$$
- **Task $\tau_2$:**
  $$R_2 = C_2 + C_1 = 3 + 2 = \mathbf{5,000\ \mu\text{s}\ (5\text{ ms})} \le D_2 = 7,000\ \mu\text{s} \quad (\mathbf{Margin: +2,000\ \mu\text{s} / +2\text{ ms},\ PASS})$$

---

## 4. Comparison Summary: Theoretical vs. EmbedSched Output

| Metric / Parameter | Buttazzo §5.5 Theoretical Value | EmbedSched Tool Output | Match? |
|:---|:---:|:---:|:---:|
| **Configured Algorithm** | `EDF` | `EDF` | :white_check_mark: Exact |
| **Constrained Deadlines ($D < T$)** | Detected ($\tau_1, \tau_2$) | `Tasks (tau1, tau2) have constrained deadlines (D < T)` | :white_check_mark: Exact |
| **Total Core Utilization ($U$)** | $63.33\%$ | `63.3%` | :white_check_mark: Exact |
| **Analysis Method** | Processor Demand Analysis | `processor demand analysis used instead of simple utilization check` | :white_check_mark: Exact |
| **PDA Tightest Point ($L$)** | $7\text{ ms}\ (7,000\ \mu\text{s})$ | `L=7000.0µs` | :white_check_mark: Exact |
| **PDA Tightest Margin** | $+2\text{ ms}\ (+2,000\ \mu\text{s})$ | `+2000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ WCRT ($R_1$)** | $2\text{ ms}\ (2,000\ \mu\text{s})$ | `2000.00 µs` | :white_check_mark: Exact |
| **$\tau_1$ Deadline Margin** | $+3\text{ ms}\ (+3,000\ \mu\text{s})$ | `+3000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ WCRT ($R_2$)** | $5\text{ ms}\ (5,000\ \mu\text{s})$ | `5000.00 µs` | :white_check_mark: Exact |
| **$\tau_2$ Deadline Margin** | $+2\text{ ms}\ (+2,000\ \mu\text{s})$ | `+2000.00 µs` | :white_check_mark: Exact |
| **Overall System Verdict** | `SCHEDULABLE` | `PASS (SCHEDULABLE)` | :white_check_mark: Exact |

---

## 5. How to Replicate

From the workspace root:

```bash
# 1. Navigate to the test directory
cd buttazo_test/Test_6

# 2. Compile the ARM Cortex-M firmware (if rebuilding)
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -O0 \
  -ffunction-sections -fdata-sections -nostdlib -T linker.ld \
  "-Wl,-Map=firmware.map" -o firmware.elf main.c

# 3. Run the EmbedSched analysis engine
python run.py

# 4. View results in results.md and visual plots in charts/
cat results.md
```
