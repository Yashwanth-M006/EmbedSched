# Schedulability Analysis in EmbedSched: Architecture, Theory & Mathematics

> **Document Version:** 1.0  
> **Target Architectures:** ARM Cortex-M0/M3/M4/M7 (Single-core & Multicore)  
> **Supported OS Standards:** AUTOSAR OS, OSEK/VDX, FreeRTOS, Bare-Metal  
> **Analysis Engine:** Post-Compile Pre-Hardware Schedulability Pipeline

---

## Table of Contents
1. [Executive Overview & Philosophy](#1-executive-overview--philosophy)
2. [End-to-End Analysis Pipeline](#2-end-to-end-analysis-pipeline)
3. [Stage 1: Low-Level Binary Ingestion & WCET Derivation](#3-stage-1-low-level-binary-ingestion--wcet-derivation)
4. [Stage 2: Core Partitioning & Inter-Core IPC Latency](#4-stage-2-core-partitioning--inter-core-ipc-latency)
5. [Stage 3: Shared Resources & Priority Ceiling Protocol (PCP/SRP) Blocking](#5-stage-3-shared-resources--priority-ceiling-protocol-pcpsrp-blocking)
6. [Stage 4: Schedulability Analysis Engines](#6-stage-4-schedulability-analysis-engines)
   - [A. Fixed-Priority Rate Monotonic (RM) & Deadline Monotonic (DM)](#a-fixed-priority-rate-monotonic-rm--deadline-monotonic-dm)
   - [B. Dynamic-Priority Earliest Deadline First (EDF) & Processor Demand Analysis (PDA)](#b-dynamic-priority-earliest-deadline-first-edf--processor-demand-analysis-pda)
7. [Stage 5: Cross-Domain Firmware Risk Synthesis](#7-stage-5-cross-domain-firmware-risk-synthesis)
   - [A. Concurrent Preemption Stack Depth Analysis](#a-concurrent-preemption-stack-depth-analysis)
   - [B. Resource Allocation Graph (RAG) Deadlock Detection](#b-resource-allocation-graph-rag-deadlock-detection)
   - [C. Hyperperiod Combinatorial Explosion Protection](#c-hyperperiod-combinatorial-explosion-protection)
   - [D. Epistemic Confidence Propagation](#d-epistemic-confidence-propagation)
   - [E. Levenshtein Typo Recovery](#e-levenshtein-typo-recovery)
8. [Concrete Numerical Worked Examples](#8-concrete-numerical-worked-examples)

---

## 1. Executive Overview & Philosophy

Classical real-time scheduling theory (Liu & Layland, Joseph & Pandya, Baruah) assumes that each task's Worst-Case Execution Time ($C_i$) is an immutable constant provided by the system engineer. However, in embedded engineering reality:
1. **The Pre-Hardware Gap:** Firmware engineers compile code weeks or months before physical target boards or oscilloscopes are available.
2. **The Measurement Fallacy:** Measurement-based WCET (profiling on hardware) only records paths exercised by specific test vectors; it does not provide confidence bounds.
3. **The Disconnect Between Code and Timing:** Moving an interrupt handler from 0-wait-state RAM to 4-wait-state Flash drastically alters schedulability without altering a single line of C logic.

**EmbedSched bridges this gap.** It ingests post-compile build artifacts (`.elf`, `.map`, `.ld`, `.su`, `startup.s`) along with a silicon timing profile (`chip.yaml`) and an OS task schedule (`schedule.json`). It mathematically derives execution bounds, models silicon bus wait states and preemption stacks, and computes exact schedulability margins with confidence tags.

---

## 2. End-to-End Analysis Pipeline

```
                     ┌────────────────────────────────────────┐
                     │         FIRMWARE BUILD ARTIFACTS       │
                     │  .elf   .map   .ld   .su   startup.s   │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │          SILICON CHIP PROFILE          │
                     │  Clock frequency, memory regions, bus  │
                     │  matrix, wait states, exception cycles │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: WCET DERIVATION & ISR AUTO-DETECTION                                          │
│ • Symbol extraction from .map file & section classification                            │
│ • Three-tier extraction: [SIMULATED] (trace) vs [CALCULATED] (size) vs [HEURISTIC]     │
│ • Startup vector table scan: 24-cycle hardware exception stacking + Flash wait states  │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: MULTI-CORE PARTITIONING & IPC OVERHEAD                                        │
│ • Task-to-core binding & independent core clocks (e.g. 480 MHz M7 vs 240 MHz M4)       │
│ • Inter-core channels: hardware spinlock cycles + AHB write latency                    │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: RESOURCE CEILING & PCP BLOCKING BOUND (B_i)                                   │
│ • Priority Ceiling: Ceiling(r) = min_{t in users(r)} Priority(t)                       │
│ • Sha, Rajkumar, Lehoczky single-critical-section bound: B_i = max(CS_j)               │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: SCHEDULABILITY MATHEMATICS PER CORE                                           │
│ • Fixed-Priority (RM/DM): Extended Joseph & Pandya Recurrence (R_i <= D_i)             │
│ • Dynamic-Priority (EDF): Processor Demand Analysis (PDA) Demand Bound h(L) <= L       │
│ • Utilization Bound Check: Guaranteed vs Indeterminate Zone vs Overloaded              │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: CROSS-DOMAIN RISK SYNTHESIS & REPORTING                                       │
│ • Preemption stack chain summation vs _Min_Stack_Size                                  │
│ • Resource Allocation Graph (RAG) directed cycle detection (Deadlock)                  │
│ • Hyperperiod LCM explosion protection (cap simulation at 200ms, run analytical RTA)   │
│ • Epistemic confidence propagation: Verdict inherits min(Confidence_i)                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stage 1: Low-Level Binary Ingestion & WCET Derivation

EmbedSched derives task WCET ($C_i$) without requiring manual inputs through a deterministic, three-tiered model:

### A. Memory Region & Section Classification
The tool parses the GNU Linker map file (`firmware.map`) and ELF symbol table:
- Every function is mapped to its load address and run address.
- Addresses are resolved against `memory_regions` in `chip.yaml` (`DTCM`, `ITCM`, `SRAM1`, `FLASH`).
- Memory wait states ($w$) and bus matrix arbitration rules are retrieved for the linked region.

### B. Three-Tier WCET Derivation Formulae

#### Tier 1: `[SIMULATED]` (Highest Confidence — Rank 2)
When an execution trace from an instruction set simulator (such as Renode) is provided via `--trace trace.log`:
- The tool resolves program counter (PC) samples to function symbols in the ELF.
- Exact executed instructions ($N_{\text{inst}}$) are counted.

$$\text{Cycles}_i = N_{\text{inst}} \times \text{CPI}$$

$$C_i = \text{WCET} = \frac{\text{Cycles}_i}{f_{\text{core}}} = \frac{N_{\text{inst}} \times \text{CPI}}{f_{\text{core}} \times 10^6} \times 10^6\ \mu\text{s}$$

*(For Cortex-M3/M4/M7, nominal baseline $\text{CPI} \approx 1.0$ for non-memory operations).*

#### Tier 2: `[CALCULATED]` (Medium Confidence — Rank 1)
When analyzing production binaries without dynamic traces, the tool uses the ARMv7-M Thumb-2 architectural model:
- **Instruction Density:** Thumb-2 contains a mix of 16-bit and 32-bit instructions. Across standard compiled automotive code, average instruction density is $2.5\text{ bytes/instruction}$.
- **Pipeline Factor:** Cortex-M dual-issue/pipelined cores with multi-cycle instructions (`LDR`, `STR`, `MUL`, branch penalties) average $1.15\text{ cycles/instruction}$.

$$\text{Instructions}_i = \frac{S_{\text{bytes}}}{2.5}$$

$$\text{Cycles}_i = \text{Instructions}_i \times 1.15 = \left(\frac{S_{\text{bytes}}}{2.5}\right) \times 1.15$$

$$C_i = \text{WCET} = \frac{\text{Cycles}_i}{f_{\text{core}}}$$

*Example: For a 29,230-byte task running at 168 MHz:*
$$\text{Instructions} = \frac{29,230}{2.5} = 11,692$$
$$\text{Cycles} = 11,692 \times 1.15 = 13,445.8$$
$$C_i = \frac{13,445.8}{168} \approx 80.00\ \mu\text{s}$$

#### Tier 3: `[HEURISTIC]` (Lowest Confidence — Rank 0)
If a function symbol cannot be located in the ELF or map file (e.g., inlined, stripped, or misspelled in `schedule.json`), a nominal 10-cycle stub is assigned:

$$C_i = \frac{10}{f_{\text{core}}}$$

This triggers a safety audit deduction (-10 points) and downgrades the entire report confidence.

### C. Hardware ISR Auto-Detection & Flash Wait States
Physical microcontrollers execute interrupts at hardware priority above all OS software threads:
1. **Vector Scan:** The startup file (`startup_stm32*.s`) vector table is scanned. All handlers matching `*_IRQHandler` or device vectors are auto-injected as **Priority 0 (highest priority)** periodic tasks.
2. **Hardware Stacking Penalty (ARMv7-M Architecture Reference Manual §B1.5.6):**
   - Hardware exception entry stacking (registers R0–R3, R12, LR, PC, xPSR): **12 cycles**.
   - Hardware exception exit unstacking: **12 cycles**.
   - Total mandatory hardware context switch cost: **24 cycles**.
3. **Flash Wait-State Stall Penalty:**
   If the ISR resides in Flash at frequency $f$, wait states $w$ inflate instruction fetches:

$$\text{Cycles}_{\text{ISR}} = \text{Cycles}_{\text{body}} + 24 + (\text{Instructions}_{\text{body}} \times w)$$

$$C_{\text{ISR}} = \frac{\text{Cycles}_{\text{ISR}}}{f_{\text{core}}}$$

---

## 4. Stage 2: Core Partitioning & Inter-Core IPC Latency

In multicore embedded processors (e.g., STM32H745 with Cortex-M7 Core 0 and Cortex-M4 Core 1):

1. **Independent Core Timelines:**
   Tasks assigned to Core 0 do not preempt tasks on Core 1:
   $$\text{hp}(i) \subseteq \{ \tau_j \mid \text{Core}(\tau_j) = \text{Core}(\tau_i) \}$$

2. **Asymmetric Clock Scaling:**
   $$\text{Time per cycle on Core 0} = \frac{1}{f_0} = \frac{1}{480\text{ MHz}} \approx 2.083\text{ ns}$$
   $$\text{Time per cycle on Core 1} = \frac{1}{f_1} = \frac{1}{240\text{ MHz}} \approx 4.167\text{ ns}$$

3. **Inter-Core Communication (IPC) Latency Bound:**
   When a cross-core channel exists between $\tau_{\text{sender}}$ (Core 0) and $\tau_{\text{receiver}}$ (Core 1) through shared memory (e.g. `SRAM3`):
   - **Hardware Spinlock Contention:** Cortex-M hardware test-and-set semaphore takes 8 cycles on the receiver core:
     $$t_{\text{spin}} = \frac{\text{spinlock\_cycles}}{f_{\text{receiver}}}$$
   - **Total IPC Delay:**
     $$B_{\text{IPC}} = \text{Write Latency} + t_{\text{spin}}$$
   This delay is added directly to the blocking term $B_i$ of the receiver task.

---

## 5. Stage 3: Shared Resources & Priority Ceiling Protocol (PCP/SRP) Blocking

When tasks share mutual exclusion locks (mutexes), priority inversion can occur. EmbedSched models AUTOSAR OS Priority Ceiling Protocol (PCP) and Baker's Stack Resource Policy (SRP):

### A. Resource Priority Ceiling
For every shared resource $r$:

$$\text{Ceiling}(r) = \min_{\tau \in \text{accessed\_by}(r)} \text{Priority}(\tau)$$

*(In EmbedSched, smaller integer = higher priority; Priority 1 is highest).*

### B. The Single-Critical-Section Blocking Bound
Under PCP/SRP, a task $\tau_i$ can be blocked by lower-priority tasks for **at most the duration of a single critical section** of any lower-priority task holding a resource with ceiling equal to or higher than $\tau_i$'s priority:

$$B_i = \max_{\substack{\tau_k \in \text{lp}(i) \\ r \in \text{resources}(\tau_k) \\ \text{Ceiling}(r) \le \text{Priority}(i)}} \left( \text{CS}(r, \tau_k) \right) + B_{\text{IPC}, i}$$

where:
- $\text{lp}(i) = \{ \tau_k \mid \text{Priority}(\tau_k) > \text{Priority}(\tau_i) \}$ (tasks with lower priority)
- $\text{CS}(r, \tau_k)$ is the worst-case critical section duration of task $\tau_k$ holding resource $r$.

> **Key Theoretical Advantage:** PCP prevents unbounded priority inversion and guarantees that tasks **never** suffer cumulative blocking from multiple lower-priority critical sections. $B_i$ is bounded by $\max(CS)$, never $\sum CS$.

---

## 6. Stage 4: Schedulability Analysis Engines

### A. Fixed-Priority Rate Monotonic (RM) & Deadline Monotonic (DM)

#### 1. Utilization Bound Check (Liu & Layland, 1973)
Total core CPU utilization:

$$U = \sum_{i=1}^n \frac{C_i}{T_i}$$

Theoretical bound for $n$ tasks with implicit deadlines ($D_i = T_i$):

$$U_{\text{bound}}(n) = n \left(2^{1/n} - 1\right)$$

$$\lim_{n \to \infty} U_{\text{bound}}(n) = \ln 2 \approx 0.69315 \quad (69.3\%)$$

| $n$ (Task Count) | Exact Liu & Layland Bound ($U_{\text{bound}}$) |
|:---:|:---:|
| 1 | $1.0000$ (100.0%) |
| 2 | $2(\sqrt{2} - 1) \approx 0.8284$ (82.8%) |
| 3 | $3(2^{1/3} - 1) \approx 0.7798$ (78.0%) |
| 4 | $4(2^{1/4} - 1) \approx 0.7568$ (75.7%) |
| 5 | $5(2^{1/5} - 1) \approx 0.7435$ (74.3%) |

**Decision Logic:**
- **$U \le U_{\text{bound}}$:** System is **Guaranteed Schedulable** under RM (if $D_i = T_i$).
- **$U_{\text{bound}} < U \le 1.0$:** System is in the **Indeterminate Region**. The utilization bound is sufficient but *not necessary*. The system may be completely schedulable (especially if task periods are harmonic). EmbedSched flags an `autosar_utilization_warning` and executes exact RTA.
- **$U > 1.0$:** System is **Overutilized** (impossible to schedule without deadline misses).

---

#### 2. Exact Response Time Analysis (RTA) — Joseph & Pandya Recurrence (1986)
For each task $\tau_i$, its worst-case response time $R_i$ is calculated using the fixed-point iterative recurrence:

**Initial Condition:**
$$R_i^{(0)} = C_i + B_i$$

**Recurrence Iteration:**
$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

where:
- $\text{hp}(i)$ is the set of tasks with higher priority than task $i$.
- $\lceil R_i^{(k)} / T_j \rceil$ is the ceiling function, representing the maximum number of times task $\tau_j$ can release and preempt $\tau_i$ during interval $R_i^{(k)}$.

**Termination Conditions:**
1. **Convergence (Fixed Point):**
   $$\left| R_i^{(k+1)} - R_i^{(k)} \right| < 10^{-9} \implies R_i = R_i^{(k+1)}$$
2. **Deadline Miss (Overrun):**
   $$R_i^{(k+1)} > D_i \implies \text{DEADLINE MISS Detected!}$$
3. **Safety Cap:**
   $$k \ge 1000 \implies \text{Non-convergent divergence}$$

**Verdict & Margin:**
$$\text{Margin}_i = D_i - R_i$$

$$\text{Verdict}_i = \begin{cases} \mathbf{PASS} & \text{if } R_i \le D_i \quad (\text{Margin}_i \ge 0) \\ \mathbf{FAIL} & \text{if } R_i > D_i \quad (\text{Margin}_i < 0) \end{cases}$$

---

### B. Dynamic-Priority Earliest Deadline First (EDF) & Processor Demand Analysis (PDA)

On cores configured with EDF, priority is assigned dynamically at runtime: the active task whose absolute deadline $d_i(t) = t_{\text{release}} + D_i$ is closest to the current time executes first.

#### 1. Implicit Deadlines ($D_i = T_i$)
Under EDF, the utilization bound is $100\%$:

$$U = \sum_{i=1}^n \frac{C_i + B_i}{T_i} \le 1.0 \iff \text{System is Schedulable}$$

#### 2. Constrained Deadlines ($D_i < T_i$) — Baruah's Processor Demand Analysis
When deadlines are shorter than periods, tasks demand bursts of computation within tight initial windows. A system with $U = 75\%$ can fail under EDF.

EmbedSched activates the **Demand Bound Function** $h(L)$ (Baruah, Mok, Rosier 1990):

$$h(L) = \sum_{i=1}^n \max\left(0, \left\lfloor \frac{L + T_i - D_i}{T_i} \right\rfloor\right) (C_i + B_i)$$

where $h(L)$ represents the maximum execution demand requested by all jobs whose arrival time and deadline both fall strictly within an interval of length $L$.

**Schedulability Condition:**
The task set is schedulable under EDF if and only if:

$$\forall L \in \mathcal{D}, \quad h(L) \le L$$

where $\mathcal{D}$ is the set of all absolute deadline testing points up to the hyperperiod $H$:

$$\mathcal{D} = \{ k \cdot T_i + D_i \mid k \in \mathbb{N}_0, \ k \cdot T_i + D_i \le H \}$$

$$H = \text{LCM}(T_1, T_2, \dots, T_n)$$

EmbedSched evaluates $h(L)$ at every point in $\mathcal{D}$, identifies whether any point violates $h(L) > L$, and reports the **tightest margin point**:

$$\text{Tightest Margin} = \min_{L \in \mathcal{D}} (L - h(L))$$

---

## 7. Stage 5: Cross-Domain Firmware Risk Synthesis

EmbedSched combines timing mathematics with static binary inspection to identify real-world failure modes that pure schedulers ignore:

### A. Concurrent Preemption Stack Depth Analysis
In single-stack microcontroller architectures (e.g. FreeRTOS MSP, bare-metal main loop, or OSEK Basic Tasks BCC1):
- Each task consumes a stack frame for local buffers, register spills, and call chains.
- Under full preemption, higher-priority tasks preempt lower-priority tasks at their deepest call frames.
- All activation frames accumulate concurrently in physical memory:

$$\text{Stack}_{\text{worst-case}} = \sum_{i=1}^n \text{FrameDepth}(\tau_i)$$

EmbedSched traverses the static call graph, sums `.su` file frame sizes, and evaluates against linker script allocation:

$$\text{Margin}_{\text{stack}} = \text{\_Min\_Stack\_Size} - \text{Stack}_{\text{worst-case}}$$

$$\text{Margin}_{\text{stack}} < 0 \implies \mathbf{WARNING:\ Concurrent\ Stack\ Overflow\ Risk}$$

---

### B. Resource Allocation Graph (RAG) Deadlock Detection
If two tasks acquire shared locks in opposing order across cores:
- Task $\tau_1$ acquires Lock $A$ then Lock $B$.
- Task $\tau_2$ acquires Lock $B$ then Lock $A$.

EmbedSched constructs a directed lock-dependency graph $G = (V, E)$ where edges $(r_a \to r_b)$ represent acquiring $r_b$ while holding $r_a$:

$$V = \{ \text{all resources} \}$$
$$E = \{ (r_a \to r_b) \mid \exists\ \tau, \ \text{order}(r_a) < \text{order}(r_b) \}$$

The engine runs Tarjan's strongly connected components / DFS cycle detection:

$$\exists\ \text{Cycle in } G \implies \mathbf{CRITICAL:\ Circular\ Deadlock\ Risk\ Detected}$$

---

### C. Hyperperiod Combinatorial Explosion Protection
The simulation timeline spans one hyperperiod $H = \text{LCM}(T_1, \dots, T_n)$.  
If periods are non-harmonic (e.g. coprime primes: $7, 11, 13, 17, 19\text{ ms}$):

$$\text{LCM}(7, 11, 13, 17, 19) = 323,323\text{ ms} = 323.323\text{ seconds}$$

Simulating 323 seconds with microsecond resolution would create over $150,000,000$ event objects, causing out-of-memory crashes.

**EmbedSched Protection Rule:**
$$\text{If } H > 200\text{ ms}:$$
1. Cap discrete-event simulation window to a representative **30 ms** window.
2. Rely strictly on **analytical RTA** (which converges in under 5 iterations regardless of hyperperiod length).
3. Emit finding `autosar_hyperperiod_explosion`.

---

### D. Epistemic Confidence Propagation
Every calculated number carries a source confidence tag:
- `[SIMULATED]` (Rank 2)
- `[CALCULATED]` (Rank 1)
- `[HEURISTIC]` (Rank 0)

The system verdict confidence is determined by the minimum lattice operator:

$$\text{Confidence}_{\text{verdict}} = \min_{i=1}^n \left( \text{Rank}(\text{Confidence}(\tau_i)) \right)$$

$$\min(2, 1, 0) = 0 \implies \mathbf{[HEURISTIC]}$$

If even one task relies on an unverified heuristic, the entire schedulability verdict is downgraded to `[HEURISTIC]`, preventing over-claiming in functional safety audits (ISO 26262).

---

### E. Levenshtein Typo Recovery
When an entry function in `schedule.json` does not exist in `firmware.map`, the tool computes dynamic programming Levenshtein edit distance against all valid firmware symbols:

$$D(i, j) = \min \begin{cases}
D(i-1, j) + 1 \\
D(i, j-1) + 1 \\
D(i-1, j-1) + \mathbb{I}(s_1[i] \ne s_2[j])
\end{cases}$$

If $D(s_1, s_2) \le 3$, EmbedSched issues:
`Did you mean '<symbol>'? (Levenshtein distance: d)`
and excludes the invalid task from RTA to prevent unvalidated zero-time assumptions.

---

## 8. Concrete Numerical Worked Examples

### Example 1: Test Case 1 (Baseline Schedulable RM)
- **Architecture:** STM32F407 @ 168 MHz ($t_{\text{cycle}} \approx 5.952\text{ ns}$)
- **Tasks:**
  - $\tau_1$ (`Task_MotorControl`): $T_1 = 1,000\ \mu\text{s}, D_1 = 1,000\ \mu\text{s}, P_1 = 1$
  - $\tau_2$ (`Task_SensorAgg`): $T_2 = 20,000\ \mu\text{s}, D_2 = 20,000\ \mu\text{s}, P_2 = 2$
  - $\tau_3$ (`Task_CANTransmit`): $T_3 = 100,000\ \mu\text{s}, D_3 = 100,000\ \mu\text{s}, P_3 = 3$

#### WCET Derivation from `.map`:
- $\tau_1$: $29,230\text{ bytes} \implies \frac{29230}{2.5} \times 1.15 = 13,445.8\text{ cycles} \implies C_1 = \frac{13445.8}{168} = 80.00\ \mu\text{s}$
- $\tau_2$: $14,620\text{ bytes} \implies \frac{14620}{2.5} \times 1.15 = 6,725.2\text{ cycles} \implies C_2 = \frac{6725.2}{168} = 40.00\ \mu\text{s}$
- $\tau_3$: $7,316\text{ bytes} \implies \frac{7316}{2.5} \times 1.15 = 3,365.36\text{ cycles} \implies C_3 = \frac{3365.36}{168} = 20.00\ \mu\text{s}$

#### Utilization:
$$U = \frac{80}{1000} + \frac{40}{20000} + \frac{20}{100000} = 0.0800 + 0.0020 + 0.0002 = 0.0822 \quad (8.22\%)$$
$$U_{\text{bound}}(3) = 3(2^{1/3} - 1) \approx 77.98\%$$
$$U = 8.22\% \le 77.98\% \implies \mathbf{Guaranteed\ Schedulable}$$

#### RTA Recurrence:
- **Task 1:**
  $$R_1 = C_1 = \mathbf{80.00\ \mu\text{s}} \le 1,000\ \mu\text{s} \quad (\text{Margin: } +920\ \mu\text{s},\ \mathbf{PASS})$$
- **Task 2:**
  $$R_2^{(0)} = C_2 = 40.00\ \mu\text{s}$$
  $$R_2^{(1)} = 40 + \left\lceil \frac{40}{1000} \right\rceil \times 80 = 40 + (1 \times 80) = 120.00\ \mu\text{s}$$
  $$R_2^{(2)} = 40 + \left\lceil \frac{120}{1000} \right\rceil \times 80 = 40 + (1 \times 80) = \mathbf{120.00\ \mu\text{s}} \le 20,000\ \mu\text{s} \quad (\text{Margin: } +19,880\ \mu\text{s},\ \mathbf{PASS})$$
- **Task 3:**
  $$R_3^{(0)} = C_3 = 20.00\ \mu\text{s}$$
  $$R_3^{(1)} = 20 + \left\lceil \frac{20}{1000} \right\rceil \times 80 + \left\lceil \frac{20}{20000} \right\rceil \times 40 = 20 + 80 + 40 = 140.00\ \mu\text{s}$$
  $$R_3^{(2)} = 20 + \left\lceil \frac{140}{1000} \right\rceil \times 80 + \left\lceil \frac{140}{20000} \right\rceil \times 40 = 20 + 80 + 40 = \mathbf{140.00\ \mu\text{s}} \le 100,000\ \mu\text{s} \quad (\text{Margin: } +99,860\ \mu\text{s},\ \mathbf{PASS})$$

---

### Example 2: Test Case 3 (Constrained Deadline Miss)
- **Tasks:**
  - $\tau_A$: $T_A = 10,000\ \mu\text{s}, D_A = 10,000\ \mu\text{s}, C_A = 3,000\ \mu\text{s}, P_A = 1$
  - $\tau_B$: $T_B = 15,000\ \mu\text{s}, \mathbf{D_B = 6,000\ \mu\text{s}}, C_B = 3,200\ \mu\text{s}, P_B = 2$
  - $\tau_C$: $T_C = 20,000\ \mu\text{s}, D_C = 20,000\ \mu\text{s}, C_C = 4,000\ \mu\text{s}, P_C = 3$

#### Utilization Fallacy:
$$U = \frac{3000}{10000} + \frac{3200}{15000} + \frac{4000}{20000} = 0.3000 + 0.2133 + 0.2000 = 0.7133 \quad (71.3\%)$$
$$U_{\text{bound}} = 78.0\%$$
*A naive tool checking only $U \le U_{\text{bound}}$ declares this safe!*

#### Exact RTA Catching the Miss:
For $\tau_B$ ($D_B = 6,000\ \mu\text{s}$):
$$R_B^{(0)} = C_B = 3,200\ \mu\text{s}$$
$$R_B^{(1)} = 3,200 + \left\lceil \frac{3200}{10000} \right\rceil \times 3000 = 3,200 + (1 \times 3000) = 6,200\ \mu\text{s}$$
$$R_B^{(2)} = 3,200 + \left\lceil \frac{6200}{10000} \right\rceil \times 3000 = 3,200 + 3000 = \mathbf{6,200\ \mu\text{s}}$$

**Deadline Evaluation:**
$$R_B = 6,200\ \mu\text{s} > D_B = 6,000\ \mu\text{s}$$
$$\mathbf{Margin}_B = 6,000 - 6,200 = \mathbf{-200\ \mu\text{s}} \implies \mathbf{CRITICAL\ DEADLINE\ MISS\ (FAIL)}$$

---

### Example 3: Test Case 4 (PCP Mutex Blocking)
- **Tasks:**
  - $\tau_H$: $T = 10\text{ ms}, D = 10\text{ ms}, C = 3.0\text{ ms}, P = 1$ (uses `mutex_spi`)
  - $\tau_M$: $T = 20\text{ ms}, D = 20\text{ ms}, C = 2.0\text{ ms}, P = 2$ (uses `mutex_i2c`)
  - $\tau_L$: $T = 40\text{ ms}, D = 40\text{ ms}, C = 8.0\text{ ms}, P = 3$ (uses `mutex_spi` for 3.0 ms, `mutex_i2c` for 4.5 ms)

#### Ceilings:
- $\text{Ceiling}(\text{mutex\_spi}) = 1$
- $\text{Ceiling}(\text{mutex\_i2c}) = 2$

#### PCP Blocking Calculation:
- For $\tau_H$ (Priority 1):
  $$B_H = \max(CS(\text{mutex\_spi}, \tau_L)) = \mathbf{3.0\text{ ms}}$$
- For $\tau_M$ (Priority 2):
  $$B_M = \max(CS(\text{mutex\_spi}, \tau_L), CS(\text{mutex\_i2c}, \tau_L)) = \max(3.0, 4.5) = \mathbf{4.5\text{ ms}}$$
  *(Single-critical-section bound prevents summing $3.0 + 4.5 = 7.5\text{ ms}$).*

#### Extended RTA with Blocking:
- **Task H:**
  $$R_H = C_H + B_H = 3.0 + 3.0 = \mathbf{6.0\text{ ms}} \le 10\text{ ms} \quad (\text{Margin: } +4.0\text{ ms},\ \mathbf{PASS})$$
- **Task M:**
  $$R_M^{(0)} = C_M + B_M = 2.0 + 4.5 = 6.5\text{ ms}$$
  $$R_M^{(1)} = 2.0 + 4.5 + \left\lceil \frac{6.5}{10} \right\rceil \times 3.0 = 6.5 + (1 \times 3.0) = 9.5\text{ ms}$$
  $$R_M^{(2)} = 2.0 + 4.5 + \left\lceil \frac{9.5}{10} \right\rceil \times 3.0 = \mathbf{9.5\text{ ms}} \le 20\text{ ms} \quad (\text{Margin: } +10.5\text{ ms},\ \mathbf{PASS})$$

---

## 9. Conclusion

Schedulability analysis in EmbedSched is an integrated pipeline connecting silicon architecture to real-time mathematics:
1. **Physical Artifact Accuracy:** WCETs and hardware ISR delays originate in actual binary section layouts and MCU wait-state curves.
2. **Mathematical Completeness:** Schedulability is strictly evaluated via exact Joseph & Pandya recurrence or Baruah Demand Bound Functions, never resting solely on naive utilization checks.
3. **Multi-Domain Safety:** Memory placement, preemption stack growth, deadlock cycles, and confidence propagation are verified concurrently with timing deadlines.
