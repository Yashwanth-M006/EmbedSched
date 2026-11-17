# EmbedSched: Response Time Analysis (RTA) and Jitter Analysis Methodology

## 1. Executive Summary and Real-Time Foundations

In hard real-time and safety-critical embedded automotive systems conforming to ISO 26262 (ASIL-D) and AUTOSAR Classic platforms, verifying that individual task execution times ($\text{WCET}$) fit within allotted time slices is necessary but insufficient. In multi-tasking environments, tasks preempt one another, share mutex-protected resources, experience interrupt servicing interference, and communicate across cores.

To prove that no task ever misses its deadline under worst-case phasing, EmbedSched employs formal **Response Time Analysis (RTA)** combined with **Discrete-Event Schedule Simulation** and **Start-Time Jitter Analysis**.

This document defines the mathematical models, recurrence relations, protocol blocking equations, demand-bound criteria, hyperperiod algorithms, and jitter metrics implemented within EmbedSched.

---

## 2. Formal System Model

A real-time system is characterized by a set of $n$ periodic or sporadic tasks:

$$\Gamma = \{ \tau_1, \tau_2, \dots, \tau_n \}$$

Each task $\tau_i$ is defined by a 6-tuple:

$$\tau_i = \langle C_i, T_i, D_i, \Pi_i, \kappa_i, \mathcal{R}_i \rangle$$

Where:
* $C_i$: Worst-Case Execution Time ($\text{WCET}$) derived microarchitecturally via IPET (in microseconds).
* $T_i$: Minimum inter-arrival time or period (in microseconds).
* $D_i$: Relative deadline (in microseconds). EmbedSched supports two deadline models:
  - **Implicit Deadline Model:** $D_i = T_i$ for all tasks.
  - **Constrained Deadline Model:** $D_i \le T_i$ for all tasks.
* $\Pi_i$: Static priority integer. EmbedSched supports two priority ordering conventions configured via the command-line flags `--autosar-priority` or `--priority-order {standard,autosar}` (or extracted from `schedule.json`):
  - **Standard Real-Time Academic Convention (Default):** Lower numerical values represent higher priority ($\Pi_i < \Pi_j \implies \tau_i$ has higher priority than $\tau_j$). Here, $\Pi = 0$ or $1$ designates the highest priority (e.g., ISRs at $\Pi_{\text{ISR}} = 0$).
  - **AUTOSAR Classic / OSEK OS Convention:** Higher numerical values represent higher priority ($\Pi_i > \Pi_j \implies \tau_i$ has higher priority than $\tau_j$). Here, $\Pi = 255$ designates the highest priority (e.g., ISRs at $\Pi_{\text{ISR}} = 255$) and $\Pi = 0$ designates the lowest/idle task.
* $\kappa_i$: Assigned microcontroller core identifier ($\kappa_i \in \{0, 1, \dots, K-1\}$).
* $\mathcal{R}_i$: Set of shared resources accessed during execution ($\mathcal{R}_i \subseteq \{R_1, \dots, R_m\}$).

Interrupt Service Routines (ISRs) are modeled as pseudo-tasks running at the highest static priority on their respective hardware cores ($\Pi_{\text{ISR}} = 0$ under standard ordering, or $\Pi_{\text{ISR}} = 255$ under AUTOSAR ordering).

---

## 3. Response Time Analysis (RTA) for Fixed-Priority Preemptive Scheduling (FPPS)

Fixed-Priority Preemptive Scheduling encompasses Rate Monotonic (RM) scheduling (shorter period $\implies$ higher priority) and Deadline Monotonic (DM) scheduling (shorter deadline $\implies$ higher priority).

### 3.1 The Worst-Case Critical Instant and Synchronous Release Assumption

The response time $R_i$ of task $\tau_i$ is the duration elapsed between its release and its final completion. The worst-case response time occurs at Liu and Layland's **critical instant**: the exact point in time when $\tau_i$ is released simultaneously with all higher-priority tasks that can preempt it, having experienced the maximum possible lower-priority blocking.

> **Explicit Assumption: Synchronous Release**  
> The basic Joseph-Pandya recurrence assumes all tasks release simultaneously at time $t = 0$ (synchronous release). For implicit-deadline systems ($D_i = T_i$), this synchronous arrival is proven to produce the global worst-case response time. For constrained-deadline systems ($D_i < T_i$), the synchronous instant must be evaluated across multiple consecutive activations within the busy period to account for potential carry-in workload (detailed in Section 3.6).

The worst-case response time decomposes into three additive terms:

$$R_i = C_i + B_i + I_i$$

Where:
* $C_i$: Own worst-case execution time.
* $B_i$: Maximum duration of blocking caused by lower-priority tasks holding shared resources or cross-core locks.
* $I_i$: Maximum cumulative preemption interference caused by all higher-priority tasks released during the execution window of $\tau_i$.

### 3.2 Preemption Interference Formulation

Let $hp(i)$ denote the set of tasks with higher priority than $\tau_i$ allocated to the same core $\kappa_i$. Depending on the selected priority convention, $hp(i)$ is defined as:

* **Standard Priority Convention:**
  $$hp(i) = \{ \tau_j \in \Gamma \mid \kappa_j = \kappa_i \land \Pi_j < \Pi_i \}$$

* **AUTOSAR Priority Convention:**
  $$hp(i) = \{ \tau_j \in \Gamma \mid \kappa_j = \kappa_i \land \Pi_j > \Pi_i \}$$

During a response time interval of length $R$, a higher-priority task $\tau_j \in hp(i)$ with period $T_j$ can preempt $\tau_i$ at most:

$$N_j(R) = \left\lceil \frac{R}{T_j} \right\rceil$$

Each preemption costs $C_j$ units of processor execution time. Therefore, total interference $I_i(R)$ is:

$$I_i(R) = \sum_{j \in hp(i)} \left\lceil \frac{R}{T_j} \right\rceil C_j$$

### 3.3 The Fixed-Point Recurrence Relation

Because the interference term $I_i(R)$ depends on the response time $R$ itself, $R_i$ is determined through the Joseph-Pandya fixed-point iterative recurrence:

$$R_i^{(0)} = C_i + B_i$$

$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

### 3.4 Convergence and Termination Criteria

The recurrence generates a monotonically non-decreasing sequence:

$$R_i^{(0)} \le R_i^{(1)} \le R_i^{(2)} \le \dots \le R_i^{(k)}$$

The iteration terminates upon either:
1. **Convergence (Fixed Point Reached):**
   $$|R_i^{(k+1)} - R_i^{(k)}| < \epsilon$$
   The true worst-case response time is established: $R_i = R_i^{(k+1)}$.
2. **Deadline Violation (Infeasible):**
   $$R_i^{(k+1)} > D_i$$
   The task is mathematically proven unschedulable. Further iterations are halted to prevent runaway computation.
3. **Iteration Safety Cap:**
   If $k \ge K_{\max}$ (default 1000 iterations), the analysis halts and flags divergence (typically caused by core utilization approaching or exceeding 100%).

### 3.5 Schedulability and Margin Evaluation

For each task $\tau_i$:
* **Schedulability Verdict:** $\tau_i$ is schedulable if and only if $R_i \le D_i$.
* **Timing Margin ($\Delta_i$):**
  $$\Delta_i = D_i - R_i$$
* **Near-Deadline Threshold:** If $\Delta_i < 0.05 \cdot D_i$, EmbedSched fires a warning indicating that the task possesses less than 5% headroom against jitter or transient hardware stalls.

### 3.6 Constrained Deadlines ($D_i < T_i$) and the Multi-Instance Busy Period

For implicit-deadline task sets ($D_i = T_i$), evaluating the first activation ($q = 0$) at the synchronous critical instant is mathematically proven to yield the maximum response time.

However, for constrained-deadline task sets ($D_i < T_i$), a task's execution window can carry over into subsequent period intervals, creating a "carry-in" workload. In such cases, the worst-case response time does not necessarily occur on the first instance ($q = 0$), but may occur on a subsequent instance $q \in \{1, 2, \dots \}$ within the level-$i$ busy period.

To guarantee soundness under constrained deadlines, EmbedSched evaluates the response time across all activations $q$ within the level-$i$ busy period:

$$w_i(q) = (q + 1)C_i + B_i + \sum_{j \in hp(i)} \left\lceil \frac{w_i(q)}{T_j} \right\rceil C_j$$

The response time for activation $q$ is:

$$R_i(q) = w_i(q) - q \cdot T_i$$

The overall worst-case response time is the maximum across all instances in the busy period:

$$R_i = \max_{q \ge 0} \{ R_i(q) \}$$

The search terminates at the first instance $q$ where:

$$w_i(q) \le (q + 1)T_i$$

Which indicates that activation $q$ completes before the next activation $q + 1$ arrives, ending the level-$i$ busy period.

If an implementation evaluates only instance $q = 0$ for constrained deadlines without multi-instance expansion, it is valid only under the condition that no carry-in occurs ($R_i \le T_i$). EmbedSched explicitly flags any constrained-deadline task ($D_i < T_i$) to distinguish single-instance bounds from full busy-period verifications.

---

## 4. Resource Sharing and Blocking Time ($B_i$) Calculation

When tasks share resources (such as hardware peripheral registers, communication buffers, or shared memory structures) guarded by synchronization primitives, a lower-priority task holding a resource can delay a higher-priority task.

EmbedSched distinguishes between two fundamentally different blocking mechanisms:
1. **Local Core Resource Sharing:** Guarded by the Priority Ceiling Protocol (PCP) / Stack Resource Policy (SRP), providing a single-blocking guarantee.
2. **Cross-Core Communication (IPC):** Guarded by hardware spinlocks, where contention occurs per shared-memory access.

### 4.1 Local Resource Sharing: Priority Ceiling Protocol (PCP)

Each shared resource $R_k$ on a core is assigned a static ceiling priority equal to the highest priority of any task that accesses it:

* **Standard Priority Convention:**
  $$\Pi_{\text{ceiling}}(R_k) = \min \{ \Pi_j \mid \tau_j \in \Gamma \land R_k \in \mathcal{R}_j \}$$

* **AUTOSAR Priority Convention:**
  $$\Pi_{\text{ceiling}}(R_k) = \max \{ \Pi_j \mid \tau_j \in \Gamma \land R_k \in \mathcal{R}_j \}$$

#### The Single-Blocking Theorem
Under PCP, task $\tau_i$ can be blocked by at most one critical section of any lower-priority task throughout its entire execution. Let $lp(i)$ denote the set of tasks with lower priority than $\tau_i$ on the same core:

* **Standard Priority Convention:**
  $$lp(i) = \{ \tau_j \in \Gamma \mid \kappa_j = \kappa_i \land \Pi_j > \Pi_i \}$$

* **AUTOSAR Priority Convention:**
  $$lp(i) = \{ \tau_j \in \Gamma \mid \kappa_j = \kappa_i \land \Pi_j < \Pi_i \}$$

A lower-priority task $\tau_j \in lp(i)$ can block $\tau_i$ only if $\tau_j$ enters a critical section guarded by resource $R_k$ whose ceiling is equal to or higher in priority than $\tau_i$:

* **Standard Priority Convention:** $\Pi_{\text{ceiling}}(R_k) \le \Pi_i$
* **AUTOSAR Priority Convention:** $\Pi_{\text{ceiling}}(R_k) \ge \Pi_i$

The worst-case local blocking duration $B_i^{\text{PCP}}$ is therefore the maximum critical section length among all eligible resources:

* **Standard Priority Convention:**
  $$B_i^{\text{PCP}} = \max_{\tau_j \in lp(i)} \left( \max_{R_k \in \mathcal{R}_j, \, \Pi_{\text{ceiling}}(R_k) \le \Pi_i} CS_{j, R_k} \right)$$

* **AUTOSAR Priority Convention:**
  $$B_i^{\text{PCP}} = \max_{\tau_j \in lp(i)} \left( \max_{R_k \in \mathcal{R}_j, \, \Pi_{\text{ceiling}}(R_k) \ge \Pi_i} CS_{j, R_k} \right)$$

Where $CS_{j, R_k}$ is the duration task $\tau_j$ holds resource $R_k$ (in microseconds).

### 4.2 Cross-Core Communication Blocking and Spinlock Latency ($B_i^{\text{IPC}}$)

In multicore architectures, tasks communicating across core boundaries through shared RAM regions synchronize using hardware spinlocks or atomic memory semaphores.

Unlike local PCP, **spinlocks do not possess the single-blocking property**. A task can experience contention every time it attempts to acquire a spinlock.

#### Multi-Access Formulation
Let $M_c \in \text{Channels}(\tau_i)$ denote an inter-core channel accessed by $\tau_i$, and let $m_{i, c}$ denote the number of times $\tau_i$ invokes channel $M_c$ during a single activation.

For each access:
* The hardware spinlock incurs an acquisition overhead of $N_{\text{spin}}$ clock cycles on core $\kappa_i$.
* The interconnect transfers payload data with write latency $t_{\text{write}}$.

The per-channel blocking duration is:

$$t_{\text{channel}}(M_c) = \frac{N_{\text{spin}}}{f_{\text{core}}(\kappa_i)} + t_{\text{write}}$$

The total inter-core blocking accumulated across all channel accesses within one activation is:

$$B_i^{\text{IPC}} = \sum_{M_c \in \text{Channels}(\tau_i)} m_{i, c} \cdot t_{\text{channel}}(M_c)$$

> **Explicit Assumption on Combined Blocking ($B_i$)**  
> The combined blocking term:  
> $$B_i = B_i^{\text{PCP}} + B_i^{\text{IPC}}$$  
> is valid under the operational assumption that each configured inter-core channel is accessed at most once per activation ($m_{i, c} = 1$), and that cross-core spinlock lockouts do not compound with local PCP suspensions. If a task executes multiple remote transactions per activation, $B_i^{\text{IPC}}$ must scale by the explicit call frequency $m_{i, c}$.

---

## 5. Dynamic Priority Scheduling: Earliest Deadline First (EDF)

For systems or cores operating under dynamic priority (where the active task with the closest absolute deadline executes first), static priority RTA does not apply. EmbedSched implements exact **Processor Demand Analysis (PDA)**.

### 5.1 Processor Demand Function $h(t)$

Baruah's processor demand function $h(t)$ represents the total computational demand released and required to complete within an arbitrary time interval $[0, t]$:

$$h(t) = \sum_{i: D_i \le t} \left( \left\lfloor \frac{t - D_i}{T_i} \right\rfloor + 1 \right) C_i$$

### 5.2 Schedulability Condition

A synchronous constrained-deadline task set is schedulable under preemptive EDF if and only if for all testing points $t > 0$:

$$h(t) \le t$$

If at any check point $t$ the demand exceeds the available interval ($h(t) > t$), a deadline miss is mathematically guaranteed.

### 5.3 Bound on Testing Points ($L^*$)

Testing every real number $t$ is impossible. Schedulability needs only be verified at discrete testing points corresponding to task absolute deadlines:

$$\mathcal{D} = \{ d_{i, k} = k \cdot T_i + D_i \mid d_{i, k} \le L^*, \, k \ge 0, \, 1 \le i \le n \}$$

The testing interval upper bound $L^*$ is determined by the length of the synchronous busy period $L_b$. Under constrained deadlines ($D_i \le T_i$), $L_b$ is the smallest positive fixed point of:

$$L_b = \sum_{i=1}^n \left\lceil \frac{L_b}{T_i} \right\rceil C_i$$

Alternatively, Baruah's algebraic upper bound provides:

$$L^* = \min \left( H, \, \max \left( D_{\max}, \, \frac{\sum_{i=1}^n (T_i - D_i) U_i}{1 - U} \right) \right)$$

Where:
* $U = \sum_{i=1}^n \frac{C_i}{T_i}$ is total core utilization. If $U \ge 1.0$, the core is permanently overloaded and unschedulable.
* $D_{\max} = \max_{1 \le i \le n} D_i$.
* $H = \text{LCM}(T_1, \dots, T_n)$ is the hyperperiod.

EmbedSched evaluates all deadline points in $\mathcal{D}$ up to $L^*$. If $h(t) \le t$ holds at every deadline point in $\mathcal{D}$, the task set is proven schedulable under EDF.

---

## 6. Discrete-Event Schedule Simulation

To validate analytical RTA bounds and capture runtime dynamic effects (such as preemption points, release drift, and jitter), EmbedSched runs a deterministic discrete-event simulator over the global system hyperperiod.

### 6.1 Hyperperiod Formulation

The hyperperiod $H$ represents the minimum time window after which the global state of strictly periodic tasks repeats identically:

$$H = \text{LCM}(T_1, T_2, \dots, T_n)$$

The Least Common Multiple ($\text{LCM}$) of two periods $a$ and $b$ is computed via their Greatest Common Divisor ($\text{GCD}$) using the Euclidean algorithm:

$$\text{GCD}(a, b) = \begin{cases} a, & \text{if } b = 0 \\ \text{GCD}(b, a \bmod b), & \text{otherwise} \end{cases}$$

$$\text{LCM}(a, b) = \frac{a \cdot b}{\text{GCD}(a, b)}$$

For $n$ tasks:

$$H = \text{LCM}(T_1, \text{LCM}(T_2, \dots, \text{LCM}(T_{n-1}, T_n)))$$

### 6.2 Hyperperiod Explosion Mitigation vs. Analytical Independence

When tasks have co-prime periods (for example, $T_1 = 1000 \, \mu\text{s}$ and $T_2 = 997 \, \mu\text{s}$), $H = 997,000 \, \mu\text{s}$, creating millions of activations that exhaust memory during discrete-event simulation.

EmbedSched caps the simulation hyperperiod at $H_{\max} = 2,000,000 \, \mu\text{s}$ (2.0 seconds):
* If $H > H_{\max}$, the simulation duration is scaled to $H_{\max}$, and a notification is displayed on the Gantt chart.

> **Critical Distinction: Simulation Cap vs. Analytical RTA Correctness**  
> The hyperperiod cap applies **strictly and exclusively** to the discrete-event simulation and Gantt visualization.  
> Analytical Response Time Analysis (Section 3) and Processor Demand Analysis (Section 5) are completely independent of this cap:  
> * RTA fixed-point iterations operate in microsecond intervals bounded by individual deadlines ($R_i \le D_i$).  
> * PDA testing points are bounded by $L^*$, not the simulation timeline.  
> Therefore, formal mathematical schedulability guarantees remain exact, complete, and uncompromised regardless of hyperperiod scaling.

---

## 7. Jitter Analysis Methodology

In closed-loop automotive control engineering (such as motor field-oriented control, powertrain torque loops, and sensor sampling), execution jitter causes phase lag, sampling aliasing, and control loop instability. EmbedSched evaluates execution jitter across every task activation throughout the simulation.

### 7.1 Start-Time Jitter ($J_i^{\text{start}}$)

Ideal periodic execution assumes task $\tau_i$'s $k$-th activation begins running immediately at its release time $t_{\text{rel}}(k) = k \cdot T_i$.

In a work-conserving, non-anticipative scheduler, a task can never start *before* its release ($s_i^{(k)} \ge k \cdot T_i$). Start-time jitter represents the non-negative start delay caused by higher-priority task preemption or lower-priority blocking:

$$J_i^{\text{start}}(k) = s_i^{(k)} - k \cdot T_i \ge 0$$

Across all $K_i = \lfloor H / T_i \rfloor$ completed timely activations in the hyperperiod, EmbedSched computes:

#### Maximum Jitter ($J_i^{\max}$)
$$J_i^{\max} = \max_{0 \le k < K_i} J_i^{\text{start}}(k)$$

#### Mean Jitter ($J_i^{\text{mean}}$)
$$J_i^{\text{mean}} = \frac{1}{K_i} \sum_{k=0}^{K_i - 1} J_i^{\text{start}}(k)$$

#### Relative Jitter Ratio ($\rho_i$)
$$\rho_i = \frac{J_i^{\max}}{T_i} \times 100\%$$

> **Decoupling Jitter from Deadline Misses**  
> Jitter analysis measures start-time variation strictly for valid scheduling activations ($s_i^{(k)} + C_i \le k \cdot T_i + D_i$). If a task activation is delayed beyond its deadline, it is treated as a **Deadline Miss Violation**, not masked by an artificial modulo or period clamp.

### 7.2 Safety Assessment Classification

EmbedSched classifies task jitter against strict real-time thresholds:

| Jitter Ratio ($\rho_i$) | Assessment Grade | Engineering Implication |
| :--- | :--- | :--- |
| $\rho_i < 1\%$ | **EXCELLENT** | Negligible phase distortion; ideal for high-bandwidth feedback loops |
| $1\% \le \rho_i < 5\%$ | **GOOD** | Acceptable for general automotive sensor and actuator processing |
| $5\% \le \rho_i < 20\%$ | **MODERATE** | Detectable start variation; acceptable only for background supervisory tasks |
| $\rho_i \ge 20\%$ | **HIGH WARNING** | Severe preemption delay; risks degradation of control stability |

### 7.3 Jitter-Expanded RTA Recurrence

When input release jitter $J_j^{\text{rel}}$ is introduced by upstream interrupt servicing or hardware sampling latencies, higher-priority tasks can burst closer together. The RTA recurrence is extended to account for arbitrary release jitter:

$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i^{(k)} + J_j^{\text{rel}}}{T_j} \right\rceil C_j$$

---

## 8. Summary of Analysis Formulas and Applicability Boundaries

| Analysis Metric | Mathematical Formula | Applicability Boundary | Purpose |
| :--- | :--- | :--- | :--- |
| **Fixed-Priority RTA** | $R_i^{(k+1)} = C_i + B_i + \sum_{j \in hp(i)} \lceil R_i^{(k)} / T_j \rceil C_j$ | Exact (necessary & sufficient) for FPPS with synchronous release ($D_i \le T_i$); $hp(i)$ determined by standard or AUTOSAR convention | Worst-case completion latency |
| **Constrained-Deadline RTA** | $w_i(q) = (q+1)C_i + B_i + \sum \lceil w_i(q)/T_j \rceil C_j$ | Exact across all busy-period activations $q$ for $D_i < T_i$ | Prevents carry-in underestimation |
| **PCP Blocking** | $B_i^{\text{PCP}} = \max_{\tau_j \in lp(i), \, \Pi_{\text{ceiling}}(R_k) \succeq \Pi_i} CS_{j, R_k}$ | Local core mutexes under PCP / SRP ($\le$ for standard, $\ge$ for AUTOSAR) | Single-blocking priority inversion bound |
| **IPC Spinlock Latency** | $B_i^{\text{IPC}} = \sum m_{i, c} \cdot (N_{\text{spin}} / f_{\text{core}} + t_{\text{write}})$ | Multi-core shared memory channels | Cumulative spinlock & bus write delay |
| **EDF Processor Demand** | $h(t) = \sum_{i: D_i \le t} (\lfloor (t - D_i)/T_i \rfloor + 1) C_i \le t$ | Exact (necessary & sufficient) for dynamic priority EDF ($D_i \le T_i$) | Verifies processor demand at all $t \in \mathcal{D}$ |
| **System Hyperperiod** | $H = \text{LCM}(T_1, T_2, \dots, T_n)$ | Periodic tasks; capped at 2.0s for simulation only | Repeating cycle for schedule simulation |
| **Start-Time Jitter** | $J_i^{\text{start}}(k) = s_i^{(k)} - k \cdot T_i \ge 0$ | Evaluated across completed timely activations | Start deviation affecting control phase margin |
| **Utilization Pre-Filter** | $U = \sum_{i=1}^n \frac{C_i}{T_i} \le n(2^{1/n} - 1)$ | Sufficient **only** for RM with implicit deadlines ($D_i = T_i$) & $B_i = 0$ | Fast sanity check pre-filter |
| **General Utilization Limit** | $U = \sum_{i=1}^n \frac{C_i}{T_i} \le 1.0$ | Necessary condition for all single-core preemptive schedulers | Overload detection (if $U > 1$, unschedulable) |
