# EmbedSched: Schedulability & Timing Formulas Reference

This document provides a clean, clear mathematical reference for all equations, bounds, and algorithms used in **EmbedSched**. 

Each formula is presented in three formats:
1. **Visual Text / ASCII Box** (guaranteed crystal-clear in all text editors and terminals)
2. **Standard LaTeX Math** (for rendering in markdown viewers with KaTeX/MathJax)
3. **Definition of Terms & Concrete Units**

---

## Table of Contents
1. [WCET Derivation Formulas](#1-wcet-derivation-formulas)
2. [Hardware ISR & Memory Stall Formulas](#2-hardware-isr--memory-stall-formulas)
3. [Multi-Core & IPC Latency Formulas](#3-multi-core--ipc-latency-formulas)
4. [Resource Ceiling & PCP Blocking Formulas](#4-resource-ceiling--pcp-blocking-formulas)
5. [Utilization Bounds (Liu & Layland)](#5-utilization-bounds-liu--layland)
6. [Exact Response Time Analysis (RTA — Joseph & Pandya)](#6-exact-response-time-analysis-rta--joseph--pandya)
7. [Earliest Deadline First & Demand Bound Analysis (EDF / PDA — Baruah)](#7-earliest-deadline-first--demand-bound-analysis-edf--pda--baruah)
8. [Cross-Domain Safety Formulas (Stack & Confidence)](#8-cross-domain-safety-formulas-stack--confidence)
9. [Quick Reference Summary Table](#9-quick-reference-summary-table)

---

## 1. WCET Derivation Formulas

EmbedSched computes the Worst-Case Execution Time ($C_i$) of a task using a three-tier model depending on available input artifacts.

### Tier 1: `[SIMULATED]` (Renode Trace Available)
When an instruction trace log is provided, execution cycles are counted directly:

```
+-----------------------------------------------------------+
|                                                           |
|                 N_instructions * CPI                      |
|   WCET (s)  =  ----------------------                     |
|                        f_core                             |
|                                                           |
|                 N_instructions * CPI * 1,000,000          |
|   WCET (us) =  ----------------------------------         |
|                        f_core (in Hz)                     |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$C_i = \frac{N_{\text{inst}} \times \text{CPI}}{f_{\text{core}}}$$

- $N_{\text{inst}}$: Total retired instructions recorded in the trace.
- $\text{CPI}$: Cycles Per Instruction (Nominal baseline = $1.0$ for ARM Cortex-M).
- $f_{\text{core}}$: Target core clock frequency (e.g., $168\text{ MHz} = 168 \times 10^6\text{ Hz}$).

---

### Tier 2: `[CALCULATED]` (Static Binary Analysis)
When analyzing compiled `.elf` and `.map` files without dynamic traces:
- **Thumb-2 Instruction Density:** Average instruction width = $2.5\text{ bytes/instruction}$
- **Pipeline Penalty Factor:** Average execution factor = $1.15\text{ cycles/instruction}$

```
+-----------------------------------------------------------+
|                                                           |
|   1. Instruction Count:                                   |
|                          Size_bytes                       |
|      N_instructions  =  ------------                      |
|                             2.5                           |
|                                                           |
|   2. Execution Cycles:                                    |
|      Cycles          =  N_instructions * 1.15             |
|                                                           |
|                      =  (Size_bytes / 2.5) * 1.15         |
|                                                           |
|   3. WCET in microseconds:                                |
|                                 Cycles                    |
|      WCET (us)       =  -----------------------           |
|                          f_core (in MHz)                  |
|                                                           |
+-----------------------------------------------------------+
```

**Combined Direct Formula:**
```
+-----------------------------------------------------------+
|                                                           |
|                     Size_bytes * 1.15                     |
|      WCET (us)  =  -------------------                    |
|                      2.5 * f_core_MHz                     |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$C_i = \frac{\left( \frac{S_i}{2.5} \right) \times 1.15}{f_{\text{core}}}$$

- $S_i$: Function binary footprint in bytes from the `.map` file.
- $f_{\text{core}}$: Core clock in MHz (e.g., $168$ for $168\text{ MHz}$).

---

### Tier 3: `[HEURISTIC]` (Symbol Missing / Stub)
If an entry function cannot be found in the symbol table:

```
+-----------------------------------------------------------+
|                                10                         |
|   WCET_stub (us)  =  ----------------------               |
|                         f_core (in MHz)                   |
+-----------------------------------------------------------+
```

---

## 2. Hardware ISR & Memory Stall Formulas

### Hardware Context Stacking Penalty
ARMv7-M hardware automatically pushes 8 registers (`R0-R3`, `R12`, `LR`, `PC`, `xPSR`) upon exception entry and pops them upon exception return:

```
+-----------------------------------------------------------+
|   Exception Entry Cost :  12 clock cycles                 |
|   Exception Exit Cost  :  12 clock cycles                 |
|   -----------------------------------------------------   |
|   Total Hardware Overhead = 12 + 12 = 24 clock cycles     |
+-----------------------------------------------------------+
```

### Flash Wait-State Stall Penalty
If code resides in Flash memory running at high frequencies, the Flash controller introduces wait states ($w$):

```
+-----------------------------------------------------------+
|                                                           |
|   Cycles_ISR = Cycles_body + 24 + (N_inst_body * w)       |
|                                                           |
|                     Cycles_ISR                            |
|   WCET_ISR   =  -------------------                       |
|                   f_core (in MHz)                         |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$C_{\text{ISR}} = \frac{\text{Cycles}_{\text{body}} + 24 + (N_{\text{inst}} \times w)}{f_{\text{core}}}$$

- $w$: Flash memory wait states (e.g., $w = 4$ for STM32F407 @ 168 MHz).
- $24$: Mandatory ARMv7-M hardware stacking and unstacking cycle overhead.

---

## 3. Multi-Core & IPC Latency Formulas

### Asymmetric Core Cycle Times
In heterogeneous systems (e.g., STM32H745 Dual Core):
- Core 0 (Cortex-M7): $f_0 = 480\text{ MHz}$
- Core 1 (Cortex-M4): $f_1 = 240\text{ MHz}$

```
+-----------------------------------------------------------+
|                               1                           |
|   Cycle Time Core 0  =  -------------  =  2.083 ns        |
|                            480 MHz                        |
|                                                           |
|                               1                           |
|   Cycle Time Core 1  =  -------------  =  4.167 ns        |
|                            240 MHz                        |
+-----------------------------------------------------------+
```

### Inter-Process Communication (IPC) Spinlock Delay
When tasks communicate across cores via shared RAM (e.g., SRAM3), the receiver task suffers hardware spinlock acquisition latency:

```
+-----------------------------------------------------------+
|                                                           |
|                          spinlock_cycles                  |
|   t_spin (us)       =  -------------------                |
|                         f_receiver (in MHz)               |
|                                                           |
|   B_IPC             =  write_latency + t_spin             |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$B_{\text{IPC}} = t_{\text{write}} + \frac{\text{Cycles}_{\text{spin}}}{f_{\text{receiver}}}$$

---

## 4. Resource Ceiling & PCP Blocking Formulas

To prevent unbounded priority inversion, EmbedSched implements the **Priority Ceiling Protocol (PCP)** and Baker's **Stack Resource Policy (SRP)**.

### Resource Priority Ceiling
```
+-----------------------------------------------------------+
|                                                           |
|   Ceiling(r)  =  min { Priority(t) | t accesses r }       |
|                                                           |
|   (Smaller integer represents higher priority)            |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$\text{Ceiling}(r) = \min_{\tau \in \text{accessed\_by}(r)} \text{Priority}(\tau)$$

---

### Single-Critical-Section Blocking Bound ($B_i$)
Under PCP, a task $\tau_i$ can be blocked by lower-priority tasks for **at most one single critical section**:

```
+-----------------------------------------------------------+
|                                                           |
|   B_i  =  max { CS(r, t_k) }  +  B_IPC                    |
|                                                           |
|   Conditions for candidate critical sections:             |
|     1. Priority(t_k) > Priority(t_i)   (t_k has LOWER prio)|
|     2. Ceiling(r)   <= Priority(t_i)   (Resource ceiling  |
|                                         is >= task prio)  |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$B_i = \max_{\substack{\tau_k \in \text{lp}(i) \\ r \in \text{resources}(\tau_k) \\ \text{Ceiling}(r) \le \text{Priority}(i)}} \left( \text{CS}(r, \tau_k) \right) + B_{\text{IPC}, i}$$

> **Key Rule:** Critical section durations are **never summed**. $B_i = \max(CS)$, not $\sum CS$.

---

## 5. Utilization Bounds (Liu & Layland)

### Task and Core Utilization
```
+-----------------------------------------------------------+
|                 C_i                                       |
|   U_i       =  -----                                      |
|                 T_i                                       |
|                                                           |
|                 n       C_i                               |
|   U_total   =  SUM  (  -----  )                           |
|                i=1      T_i                               |
+-----------------------------------------------------------+
```

### Rate Monotonic (RM) Utilization Bound
For $n$ periodic tasks with implicit deadlines ($D_i = T_i$):

```
+-----------------------------------------------------------+
|                                                           |
|   U_bound(n)  =  n * ( 2^(1/n) - 1 )                      |
|                                                           |
|   As n -> infinity:                                       |
|   lim U_bound(n) = ln(2) approx 0.69315  (69.3%)          |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$U_{\text{bound}}(n) = n \left(2^{1/n} - 1\right)$$

#### Standard Bound Reference Values:
| $n$ (Task Count) | $U_{\text{bound}}$ (Decimal) | $U_{\text{bound}}$ (Percentage) |
|:---:|:---:|:---:|
| **1** | $1.0000$ | $100.0\%$ |
| **2** | $2(\sqrt{2}-1) \approx 0.8284$ | $82.8\%$ |
| **3** | $3(2^{1/3}-1) \approx 0.7798$ | $78.0\%$ |
| **4** | $4(2^{1/4}-1) \approx 0.7568$ | $75.7\%$ |
| **5** | $5(2^{1/5}-1) \approx 0.7435$ | $74.3\%$ |
| **$\infty$** | $\ln(2) \approx 0.6931$ | $69.3\%$ |

#### Schedulability Decision Criteria:
```
           U <= U_bound(n)            -->  GUARANTEED Schedulable
  U_bound(n) < U <= 1.00              -->  INDETERMINATE (Exact RTA Required)
           U > 1.00                   -->  OVERLOADED (Unscheduable)
```

---

## 6. Exact Response Time Analysis (RTA — Joseph & Pandya)

Fixed-point iteration calculates the exact Worst-Case Response Time ($R_i$) for each task.

### The Recurrence Relation

```
+-----------------------------------------------------------------------+
|                                                                       |
|   Step 0: Initial Seed                                                |
|                                                                       |
|      R_i^(0) = C_i + B_i                                              |
|                                                                       |
|   Step k+1: Iteration                                                 |
|                                                                       |
|                         ---  /  R_i^(k)  \                            |
|      R_i^(k+1) = C_i + B_i + >   |  -------- |  * C_j                 |
|                         ---  \    T_j    /                            |
|                        j in hp(i)                                     |
|                                                                       |
+-----------------------------------------------------------------------+
```

**LaTeX Formula:**
$$R_i^{(0)} = C_i + B_i$$

$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

- $C_i$: WCET of task $\tau_i$.
- $B_i$: Maximum blocking time suffered by task $\tau_i$.
- $\text{hp}(i)$: Set of tasks with higher priority than $\tau_i$.
- $\lceil R_i^{(k)} / T_j \rceil$: Ceiling operator (preemption count of task $j$ during window $R_i^{(k)}$).

### Convergence & Verdict
```
+-----------------------------------------------------------------------+
|   1. Convergence (Fixed Point):                                       |
|      If | R_i^(k+1) - R_i^(k) | < 10^(-9)   -->  R_i = R_i^(k+1)       |
|                                                                       |
|   2. Schedulability Verdict:                                          |
|      Margin_i = D_i - R_i                                             |
|                                                                       |
|      Margin_i >= 0  (R_i <= D_i)            -->  PASS                 |
|      Margin_i <  0  (R_i >  D_i)            -->  FAIL (Deadline Miss) |
+-----------------------------------------------------------------------+
```

---

## 7. Earliest Deadline First & Demand Bound Analysis (EDF / PDA — Baruah)

Under EDF, dynamic priorities are assigned based on earliest absolute deadline:
$$d_i(t) = t_{\text{release}} + D_i$$

### Implicit Deadlines ($D_i = T_i$)
The system is schedulable if and only if total utilization does not exceed 100%:

```
+-----------------------------------------------------------+
|                                                           |
|            n     C_i + B_i                                |
|      U  = SUM ( ----------- )  <=  1.00   (100%)          |
|           i=1       T_i                                   |
|                                                           |
+-----------------------------------------------------------+
```

---

### Constrained Deadlines ($D_i < T_i$): Processor Demand Analysis
When deadlines are shorter than periods, systems with $U < 100\%$ can still miss deadlines. EmbedSched evaluates the **Demand Bound Function** $h(L)$:

```
+-----------------------------------------------------------------------+
|                                                                       |
|               n      /      / L + T_i - D_i \ \                       |
|      h(L)  = SUM max | 0,  | --------------- | | * (C_i + B_i)        |
|              i=1     \      \      T_i      / /                       |
|                                                                       |
+-----------------------------------------------------------------------+
```

**LaTeX Formula:**
$$h(L) = \sum_{i=1}^n \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) (C_i + B_i)$$

- $\lfloor \cdot \rfloor$: Floor operator.
- $h(L)$: Maximum processor demand requested by all jobs arriving and completing within an interval of length $L$.

### Testing Set $\mathcal{D}$ & Condition
The test evaluates all absolute deadline checkpoints up to the hyperperiod $H$:

```
+-----------------------------------------------------------------------+
|   Hyperperiod:                                                        |
|      H  =  LCM( T_1, T_2, ..., T_n )                                  |
|                                                                       |
|   Testing Checkpoints D:                                              |
|      D  =  { k * T_i + D_i  |  k >= 0  AND  k * T_i + D_i <= H }      |
|                                                                       |
|   Schedulability Criterion:                                           |
|      FOR ALL L in D :   h(L) <= L                                     |
|                                                                       |
|   Tightest Margin:                                                    |
|      Tightest_Margin = min { L - h(L) }  over all L in D              |
+-----------------------------------------------------------------------+
```

---

## 8. Cross-Domain Safety Formulas (Stack & Confidence)

### Worst-Case Preemption Stack Depth
In single-stack embedded architectures (e.g., bare-metal or FreeRTOS MSP):

```
+-----------------------------------------------------------+
|                                                           |
|                         n                                 |
|      Stack_worst-case = SUM ( FrameDepth(tau_i) )         |
|                        i=1                                |
|                                                           |
|      Margin_stack     = _Min_Stack_Size - Stack_worst     |
|                                                           |
|      Margin_stack >= 0  -->  SAFE                         |
|      Margin_stack <  0  -->  STACK OVERFLOW RISK          |
|                                                           |
+-----------------------------------------------------------+
```

**LaTeX Formula:**
$$\text{Stack}_{\text{worst-case}} = \sum_{i=1}^n \text{FrameDepth}(\tau_i)$$
$$\text{Margin}_{\text{stack}} = \text{\_Min\_Stack\_Size} - \text{Stack}_{\text{worst-case}}$$

---

### Epistemic Confidence Lattice
EmbedSched associates each derived quantity with a confidence rank:
- `[SIMULATED]` = Rank 2
- `[CALCULATED]` = Rank 1
- `[HEURISTIC]` = Rank 0

The overall report verdict inherits the weakest link in the calculation chain:

```
+-----------------------------------------------------------+
|                                                           |
|   Confidence_verdict = min { Rank(Confidence(tau_i)) }    |
|                         i                                 |
|                                                           |
|   min( 2, 1, 0 ) = 0  -->  [HEURISTIC]                    |
|   min( 2, 1, 1 ) = 1  -->  [CALCULATED]                   |
|   min( 2, 2, 2 ) = 2  -->  [SIMULATED]                    |
|                                                           |
+-----------------------------------------------------------+
```

---

## 9. Quick Reference Summary Table

| Category | Parameter | Formula | Key Condition / Threshold |
|:---|:---|:---|:---|
| **WCET (Tier 1)** | $C_i$ (Trace) | $C_i = (N_{\text{inst}} \times \text{CPI}) / f_{\text{core}}$ | Nominal $\text{CPI} = 1.0$ |
| **WCET (Tier 2)** | $C_i$ (Thumb-2) | $C_i = (S_{\text{bytes}} / 2.5) \times 1.15 / f_{\text{core}}$ | Average $2.5\text{ B/inst}, 1.15\text{ cyc/inst}$ |
| **ISR Hardware** | $C_{\text{ISR}}$ | $(\text{Cycles}_{\text{body}} + 24 + N_{\text{inst}} \cdot w) / f_{\text{core}}$ | $24\text{ cycles}$ hardware stacking |
| **IPC Latency** | $B_{\text{IPC}}$ | $t_{\text{write}} + (\text{Cycles}_{\text{spin}} / f_{\text{rx}})$ | Added to receiver task $B_i$ |
| **PCP Ceiling** | $\text{Ceiling}(r)$ | $\min_{\tau \in \text{users}(r)} \text{Priority}(\tau)$ | Lowest numerical value |
| **PCP Blocking** | $B_i$ | $\max \{ \text{CS}(r, \tau_k) \} + B_{\text{IPC}}$ | Max single lower-priority critical section |
| **Utilization** | $U$ | $\sum_{i=1}^n (C_i / T_i)$ | Compare with $U_{\text{bound}}(n)$ |
| **RM Bound** | $U_{\text{bound}}(n)$ | $n(2^{1/n} - 1)$ | $\approx 69.3\%$ as $n \to \infty$ |
| **Exact RTA** | $R_i^{(k+1)}$ | $C_i + B_i + \sum_{j \in \text{hp}(i)} \lceil R_i^{(k)} / T_j \rceil C_j$ | Terminate when $R_i^{(k+1)} = R_i^{(k)} \le D_i$ |
| **EDF Bound** | $U_{\text{EDF}}$ | $\sum_{i=1}^n ((C_i + B_i) / T_i) \le 1.0$ | Schedulable if $\le 100\%$ ($D_i = T_i$) |
| **EDF Demand** | $h(L)$ | $\sum \max(0, \lfloor \frac{L + T_i - D_i}{T_i} \rfloor) (C_i + B_i)$ | $\forall L \in \mathcal{D}, h(L) \le L$ |
| **Stack Depth** | $\text{Stack}_{\text{worst}}$ | $\sum_{i=1}^n \text{FrameDepth}(\tau_i)$ | Must be $\le \text{\_Min\_Stack\_Size}$ |
