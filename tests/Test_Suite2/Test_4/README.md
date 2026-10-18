# Test Case 4: Priority Inversion via Resource Sharing — PCP Blocking

> **Status:** `PASS`  
> **Confidence:** `[CALCULATED]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic with Priority Ceiling Protocol (PCP/SRP)

---

## 1. What This Test Signifies

Test Case 4 evaluates the tool's implementation of **shared resource synchronization and priority inversion bounding**. 

When tasks share mutual exclusion locks (mutexes), a lower-priority task holding a lock can temporarily block a higher-priority task. Without synchronization protocols, unbounded priority inversion occurs (as famously seen on the Mars Pathfinder spacecraft in 1997).

This test validates that EmbedSched:
1. Parses AUTOSAR shared resource declarations (`resources` in `schedule.json`).
2. Computes the **Priority Ceiling** of each resource ($Ceiling = \min_{t} Prio(t)$).
3. Correctly calculates the worst-case **blocking term ($B_i$)** using Sha, Rajkumar, & Lehoczky's Priority Ceiling Protocol (PCP).
4. Demonstrates that under PCP/SRP, blocking is **strictly bounded to at most a single critical section** ($B_i = \max CS$), rather than the naive sum of all lower-priority critical sections (which occurs under unrestricted Priority Inheritance Protocol).

---

## 2. Why It Was Performed

1. **Protocol Rigor:** Many commercial schedulability calculators either ignore mutex blocking entirely (producing unsafely optimistic response times) or naively sum critical sections (producing overly pessimistic rejections).
2. **AUTOSAR OS Compliance:** AUTOSAR OS and OSEK VDMS mandate the Priority Ceiling Protocol / Stack Resource Policy (SRP) for internal resources. The analyzer must accurately reflect this OS guarantee.
3. **Traceable Blocking Terms:** Engineers need to see exactly *which* lower-priority task and *which* mutex caused blocking in the RTA table.

---

## 3. Configuration & Task Set

### Resource Definitions (`schedule.json`)
```json
"resources": [
  {
    "name": "mutex_spi",
    "type": "mutex",
    "accessed_by": ["Task_H", "Task_L"],
    "max_critical_section_ms": 3.0
  },
  {
    "name": "mutex_i2c",
    "type": "mutex",
    "accessed_by": ["Task_M", "Task_L"],
    "max_critical_section_ms": 4.5
  }
]
```

#### Computed Priority Ceilings:
- **`mutex_spi`**: Accessed by `Task_H` (Prio 1) and `Task_L` (Prio 3) $\implies \mathbf{Ceiling = 1}$.
- **`mutex_i2c`**: Accessed by `Task_M` (Prio 2) and `Task_L` (Prio 3) $\implies \mathbf{Ceiling = 2}$.

### Task Configuration (`schedule.json`)
Three tasks on Core 0:

| Task Name | Period ($T$) | Deadline ($D$) | Priority | WCET ($C$) | Resources Accessed | Max Critical Section |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `Task_H` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | 3,000 µs (3.0 ms) | `mutex_spi` | — |
| `Task_M` | 20,000 µs (20 ms) | 20,000 µs (20 ms) | 2 | 2,000 µs (2.0 ms) | `mutex_i2c` | — |
| `Task_L` | 40,000 µs (40 ms) | 40,000 µs (40 ms) | 3 (Lowest) | 8,000 µs (8.0 ms) | `mutex_spi`, `mutex_i2c` | 3.0 ms (`spi`), 4.5 ms (`i2c`) |

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_4/firmware.map) to extract symbol sizes for each task located in `SRAM1` ($0\text{ wait states}$ on STM32F407):

* **Target Core:** ARM Cortex-M4 running at $f = 168\text{ MHz}$ ($t_{\text{cycle}} \approx 5.952\text{ ns}$).
* **Thumb-2 Instruction Model:** $2.5\text{ bytes/instruction}$ average density; $1.15\text{ cycles/instruction}$ pipelined execution average.

$$\text{Instructions} = \frac{\text{Section Size (bytes)}}{2.5}$$
$$\text{Cycles} = \text{Instructions} \times 1.15$$
$$C_i = \text{WCET} = \frac{\text{Cycles}}{168\text{ MHz}} = \frac{\text{Cycles}}{168 \times 10^6} \times 10^6\text{ µs}$$

#### 1. Task_H (`task_h`):
* Symbol size in `.text.task_h`: `0x10b7f0` bytes = $1,095,664\text{ bytes}$
$$\text{Instructions}_H = \frac{1,095,664}{2.5} = 438,265.6\text{ instructions}$$
$$\text{Cycles}_H = 438,265.6 \times 1.15 = 504,005.44\text{ cycles}$$
$$C_H = \frac{504,005.44}{168} \approx 3,000.00\text{ µs} \quad (3.0\text{ ms})$$

#### 2. Task_M (`task_m`):
* Symbol size in `.text.task_m`: `0xb2550` bytes = $730,448\text{ bytes}$
$$\text{Instructions}_M = \frac{730,448}{2.5} = 292,179.2\text{ instructions}$$
$$\text{Cycles}_M = 292,179.2 \times 1.15 = 336,006.08\text{ cycles}$$
$$C_M = \frac{336,006.08}{168} \approx 2,000.00\text{ µs} \quad (2.0\text{ ms})$$

#### 3. Task_L (`task_l`):
* Symbol size in `.text.task_l`: `0x2c9518` bytes = $2,921,752\text{ bytes}$
$$\text{Instructions}_L = \frac{2,921,752}{2.5} = 1,168,700.8\text{ instructions}$$
$$\text{Cycles}_L = 1,168,700.8 \times 1.15 = 1,344,005.92\text{ cycles}$$
$$C_L = \frac{1,344,005.92}{168} \approx 8,000.00\text{ µs} \quad (8.0\text{ ms})$$

---

### B. Priority Ceiling Protocol (PCP) Blocking Derivation

Under the Priority Ceiling Protocol (Sha, Rajkumar, & Lehoczky 1990), a task $\tau_i$ can be blocked by lower-priority tasks for **at most the duration of a single critical section**:
$$B_i = \max \{ c_{k, r} \mid k \in \text{lp}(i), \text{Ceiling}(r) \le \text{Priority}(i) \}$$

#### 1. Blocking for Task_H (Priority 1):
* Lower priority tasks: $\text{lp}(H) = \{\text{Task\_M}, \text{Task\_L}\}$
* Critical sections accessed by $\text{lp}(H)$ with $\text{Ceiling} \le 1$:
  - `mutex_spi` held by `Task_L` ($\text{Ceiling} = 1 \le 1$): $CS = 3.0\text{ ms} = 3,000\text{ µs}$
  - `mutex_i2c` held by `Task_M` or `Task_L` ($\text{Ceiling} = 2 \not\le 1$): cannot block `Task_H`
* Resulting blocking term:
  $$B_H = \max(3,000\text{ µs}) = 3,000.00\text{ µs}$$

#### 2. Blocking for Task_M (Priority 2):
* Lower priority tasks: $\text{lp}(M) = \{\text{Task\_L}\}$
* Critical sections accessed by $\text{lp}(M)$ with $\text{Ceiling} \le 2$:
  - `mutex_spi` held by `Task_L` ($\text{Ceiling} = 1 \le 2$): $CS = 3.0\text{ ms} = 3,000\text{ µs}$
  - `mutex_i2c` held by `Task_L` ($\text{Ceiling} = 2 \le 2$): $CS = 4.5\text{ ms} = 4,500\text{ µs}$
* Crucial PCP property: `Task_M` can be blocked by at most **one** critical section (never the sum of $3.0 + 4.5 = 7.5\text{ ms}$):
  $$B_M = \max(3,000\text{ µs}, 4,500\text{ µs}) = 4,500.00\text{ µs}$$

#### 3. Blocking for Task_L (Priority 3, Lowest):
* $\text{lp}(L) = \emptyset \implies B_L = 0.00\text{ µs}$

---

### C. Extended Response Time Analysis with Blocking

The extended RTA recurrence equation incorporating PCP blocking:
$$R_i^{(0)} = C_i + B_i$$
$$R_i^{(k+1)} = C_i + B_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$

#### Task H (Priority 1, $T_H = 10,000\text{ µs}, D_H = 10,000\text{ µs}$):
* $\text{hp}(H) = \emptyset$
* Evaluation:
  $$R_H = C_H + B_H = 3,000.00 + 3,000.00 = 6,000.00\text{ µs}$$
* **Deadline Check:**
  $$R_H = 6,000.00\text{ µs} \le D_H = 10,000\text{ µs}$$
  $$\text{Margin}_H = 10,000 - 6,000 = +4,000.00\text{ µs} \quad (\mathbf{PASS})$$

#### Task M (Priority 2, $T_M = 20,000\text{ µs}, D_M = 20,000\text{ µs}$):
* $\text{hp}(M) = \{\text{Task\_H}\}$
* Recurrence iterations:
  $$R_M^{(0)} = C_M + B_M = 2,000.00 + 4,500.00 = 6,500.00\text{ µs}$$
  $$R_M^{(1)} = 2,000 + 4,500 + \left\lceil \frac{6,500}{10,000} \right\rceil \times 3,000 = 6,500 + (1 \times 3,000) = 9,500.00\text{ µs}$$
  $$R_M^{(2)} = 2,000 + 4,500 + \left\lceil \frac{9,500}{10,000} \right\rceil \times 3,000 = 6,500 + (1 \times 3,000) = 9,500.00\text{ µs} \quad (\text{Converged})$$
* **Deadline Check:**
  $$R_M = 9,500.00\text{ µs} \le D_M = 20,000\text{ µs}$$
  $$\text{Margin}_M = 20,000 - 9,500 = +10,500.00\text{ µs} \quad (\mathbf{PASS})$$

#### Task L (Priority 3, $T_L = 40,000\text{ µs}, D_L = 40,000\text{ µs}$):
* $\text{hp}(L) = \{\text{Task\_H}, \text{Task\_M}\}$
* Recurrence iterations:
  $$R_L^{(0)} = C_L + B_L = 8,000.00 + 0 = 8,000.00\text{ µs}$$
  $$R_L^{(1)} = 8,000 + \left\lceil \frac{8,000}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{8,000}{20,000} \right\rceil \times 2,000 = 8,000 + 3,000 + 2,000 = 13,000.00\text{ µs}$$
  $$R_L^{(2)} = 8,000 + \left\lceil \frac{13,000}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{13,000}{20,000} \right\rceil \times 2,000 = 8,000 + (2 \times 3,000) + (1 \times 2,000) = 16,000.00\text{ µs}$$
  $$R_L^{(3)} = 8,000 + \left\lceil \frac{16,000}{10,000} \right\rceil \times 3,000 + \left\lceil \frac{16,000}{20,000} \right\rceil \times 2,000 = 8,000 + (2 \times 3,000) + (1 \times 2,000) = 16,000.00\text{ µs} \quad (\text{Converged})$$
* **Deadline Check:**
  $$R_L = 16,000.00\text{ µs} \le D_L = 40,000\text{ µs}$$
  $$\text{Margin}_L = 40,000 - 16,000 = +24,000.00\text{ µs} \quad (\mathbf{PASS})$$

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_L                     0     3      40000   8000.00    0.00   CALCULATED  16000.00        40000   24000.00      PASS
Task_M                     0     2      20000   2000.00 4500.00   CALCULATED   9500.00        20000   10500.00      PASS
Task_H                     0     1      10000   3000.00 3000.00   CALCULATED   6000.00        10000    4000.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

### Generated Findings:
- **`[INFO] autosar_pcp_blocking`:**  
  *Task H blocked by lower priority tasks on shared resource for up to 3.0ms [CALCULATED]*
- **`[INFO] autosar_pcp_blocking`:**  
  *Task M blocked by lower priority tasks on shared resource for up to 4.5ms [CALCULATED]*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_4/firmware.elf \
  --map Test_SUITE_2/Test_4/firmware.map \
  --ld  Test_SUITE_2/Test_4/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_4/schedule.json \
  --charts-dir Test_SUITE_2/Test_4/charts/
```
