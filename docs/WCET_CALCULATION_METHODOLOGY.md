# EmbedSched: Worst-Case Execution Time (WCET) Calculation Methodology

## 1. Executive Overview

In hard real-time and safety-critical embedded systems (such as AUTOSAR Classic platforms and ISO 26262 automotive ECUs), knowing the **Worst-Case Execution Time ($C_i$ or $\text{WCET}$)** of every task and Interrupt Service Routine (ISR) is mandatory. Without accurate WCETs, mathematical schedulability analysis—such as Response Time Analysis (RTA) and CPU utilization bounding—is impossible.

Traditional tools often require engineers to manually guess or annotate WCET values in configuration tables, introducing human error. **EmbedSched derives WCET automatically from actual compiled firmware build artifacts** and hardware chip specifications.

EmbedSched implements a **three-tier confidence hierarchy**, an **ARM architecture hardware timing model**, **disassembly call-graph traversal**, and **hardware exception/flash-wait-state modeling**.

---

## 2. Input Artifacts Used for WCET

EmbedSched extracts execution time by fusing five distinct data sources:

| Artifact | Source / Tool | Extracted Information |
| :--- | :--- | :--- |
| **ELF Binary (`.elf`)** | `arm-none-eabi-gcc` | Symbol table, function sizes (in bytes), executable sections (`.text`), entry point addresses |
| **Disassembly (`objdump -d`)** | `arm-none-eabi-objdump` | Branch-and-link instructions (`bl`, `blx`) to reconstruct caller $\rightarrow$ callee call graphs |
| **Chip Profile (`.yaml`)** | Hardware Datasheets / Manuals | Clock frequency ($f_{\text{core}}$), Flash wait states ($w$), exception entry/exit cycles, core architecture |
| **Task Config (`schedule.json`)** | AUTOSAR / OS Specification | Task entry functions, periods ($T_i$), deadlines ($D_i$), core assignments (`core_id`) |
| **Renode Dynamic Trace (`.txt`)** *(Optional)* | Renode Functional Simulator | Exact retired instruction counts per function during simulated execution |

---

## 3. The Three-Tier Confidence Model

Because different projects provide different levels of verification data, EmbedSched assigns an explicit **Confidence Tag** to every task's WCET. If a task invokes sub-functions of mixed confidence, **the lowest confidence tag contaminates the entire task and propagates to the final safety audit report**.

```
    [SIMULATED]    Highest Confidence   Measured functional instruction trace (Renode)
         ▲
         │ (Falls back if trace not provided)
         │
    [CALCULATED]   Medium Confidence    Static binary analysis (.text symbol size + ARM core model)
         ▲
         │ (Falls back if symbol missing in ELF)
         │
    [HEURISTIC]    Lowest Confidence    10-cycle placeholder; flags schedulability as UNRELIABLE
```

### Tier 1: `[SIMULATED]` (Dynamic Simulation Trace)
* **Trigger:** A Renode execution trace is provided (`--renode-repl` or `--renode-trace`).
* **Mechanism:** The trace is parsed to count the exact number of retired instructions ($N_{\text{inst}}$) executed by the function and its callees.
* **Cycle Calculation:**
  $$\text{Cycles} = N_{\text{inst}} \times 1.0 \text{ cycle/instruction}$$
* **Confidence Level:** Functional flow and loop trip counts are accurate. However, Renode does not simulate micro-architectural cache hits/misses or AHB bus contention, so the tag remains `[SIMULATED]` rather than cycle-accurate hardware bench measurement.

### Tier 2: `[CALCULATED]` (Static Binary Analysis)
* **Trigger:** No dynamic trace is provided, but function symbols are located in the compiled ELF `.text` section.
* **Mechanism:** Uses the binary footprint ($S_i$ in bytes) from the symbol table, divided by the architecture's instruction density ($BPI$), multiplied by the architecture pipeline CPI penalty ($CPI_{\text{penalty}}$):
  $$\text{Raw Instructions} = \frac{S_i}{\text{Bytes Per Instruction (BPI)}}$$
  $$\text{Cycles}_{\text{body}} = \left\lfloor \text{Raw Instructions} \times CPI_{\text{penalty}} \right\rfloor$$
* **Confidence Level:** Sound, conservative estimate based on total code footprint along the worst-case call path.

### Tier 3: `[HEURISTIC]` (Missing Symbol Fallback)
* **Trigger:** The function name listed in `schedule.json` does not exist in the ELF symbol table (e.g., inlined by compiler `-O3`, stripped, located in an external binary blob, or misspelled).
* **Mechanism:** Assigns a conservative 10-cycle placeholder:
  $$\text{Cycles} = 10 \text{ cycles}$$
* **Safety Impact:** Generates an immediate `check_heuristic_wcet` finding and flags the overall schedulability report as **UNRELIABLE** until the symbol is resolved.

---

## 4. Hardware Architecture Timing Profiles

Instruction density and pipeline penalty depend strongly on the target ARM core. EmbedSched maintains an internal hardware database of architecture parameters:

```python
CORE_DEFAULTS = {
    # ARMv6-M: mostly 16-bit Thumb, Von Neumann bus, simple 2-stage pipeline
    "cortex-m0":     (2.10 BPI, 1.35 CPI),
    "cortex-m0+":    (2.10 BPI, 1.35 CPI),
    "cortex-m1":     (2.10 BPI, 1.35 CPI),

    # ARMv7-M / ARMv7E-M: Harvard bus, 3-stage pipeline, mixed 16/32-bit Thumb-2
    "cortex-m3":     (2.50 BPI, 1.15 CPI),
    "cortex-m4":     (2.50 BPI, 1.15 CPI),

    # ARMv7E-M: 6-stage dual-issue superscalar pipeline with branch prediction
    "cortex-m7":     (2.60 BPI, 0.85 CPI),

    # ARMv8-M Baseline & Mainline
    "cortex-m23":    (2.15 BPI, 1.30 CPI),
    "cortex-m33":    (2.55 BPI, 1.15 CPI),

    # ARMv8.1-M Superscalar with Helium vector extensions
    "cortex-m55":    (2.65 BPI, 0.90 CPI),
    "cortex-m85":    (2.70 BPI, 0.75 CPI),

    # ARM Real-Time cores (Cortex-R)
    "cortex-r4":     (2.50 BPI, 0.90 CPI),
    "cortex-r5":     (2.50 BPI, 0.90 CPI),
    "cortex-r52":    (2.50 BPI, 0.90 CPI),

    # ARM Application 64-bit cores (AArch64)
    "cortex-a53":    (4.00 BPI, 0.50 CPI),
    "cortex-a72":    (4.00 BPI, 0.50 CPI),
}
```

### Resolution Precedence:
When calculating WCET for a task assigned to `core_id`:
1. **Per-core explicit override** in chip YAML `core_types[core_id].bytes_per_instruction` / `cpi_penalty`.
2. **Global override** at the root of chip YAML (`bytes_per_instruction` / `cpi_penalty`).
3. **Automatic core lookup** matching `core_types[core_id].type` or `chip_profile.core` against `CORE_DEFAULTS`.
4. **Default fallback:** $BPI = 2.50\text{ bytes/insn}$, $CPI = 1.15\text{ cycles/insn}$.

---

## 5. Call-Graph Traversal & Deepest Call Path

A task rarely consists of a single monolithic function; it usually delegates work to subroutines and helper functions. EmbedSched accounts for this using **Depth-First Search (DFS) over the reconstructed disassembly call graph**:

```
Task Entry: Task_MotorControl (80 bytes)
  ├── read_adc_sensors() (120 bytes)
  │     └── calibrate_offset() (60 bytes)
  └── update_pwm_duty() (90 bytes)
```

### DFS Algorithm (`_compute_wcet_cycles`):
1. **Cycle Accumulation:**
   - Computes local cycles for the entry function: $\text{Cycles}_{\text{own}}$.
   - Recursively traverses all callees listed in the call graph.
   - For multiple branches, EmbedSched selects the **worst-case branch**:
     $$\text{Cycles}_{\text{task}} = \text{Cycles}_{\text{own}} + \max_{\text{callee} \in \text{Callees}} \left( \text{Cycles}_{\text{callee\_subtree}} \right)$$
2. **Recursion Protection:**
   - A `visited` set tracks currently active functions in the call stack to prevent infinite recursion on recursive or re-entrant code.
3. **Call Chain Preservation:**
   - Preserves the worst-case execution path:
     $$\text{Chain} = [\text{Task\_MotorControl}, \text{read\_adc\_sensors}, \text{calibrate\_offset}]$$
4. **Confidence Contamination Propagation:**
   - The tag of the task becomes the **lowest confidence tag** among the entry function and any visited callee:
     $$\text{Tag}_{\text{task}} = \min \left( \text{Tag}_{\text{own}}, \min_{\text{callee}} \text{Tag}_{\text{callee}} \right)$$

---

## 6. Interrupt Service Routine (ISR) Timing Model

Interrupt Service Routines operate under direct hardware dispatch. Their execution time differs fundamentally from standard tasks due to **hardware stacking overhead** and **Flash memory wait-state stalls**.

EmbedSched applies an **exception-entry-aware formula**:

$$\text{Cycles}_{\text{ISR}} = \text{Overhead}_{\text{hardware}} + \text{Cycles}_{\text{body}} + \text{Penalty}_{\text{flash}}$$

### 1. Hardware Context Stacking Overhead
ARM Cortex-M hardware automatically saves and restores eight CPU registers (`R0-R3`, `R12`, `LR`, `PC`, `xPSR`):
* **Hardware Exception Entry:** 12 clock cycles
* **Hardware Exception Exit:** 12 clock cycles
* $$\text{Overhead}_{\text{hardware}} = 12 + 12 = 24 \text{ clock cycles}$$

### 2. Flash Wait-State Penalty Lookup
Flash memory is significantly slower than the CPU core. At high clock speeds, Flash access requires wait states ($w$):
* EmbedSched queries the chip profile's `flash_wait_states` table based on the core frequency $f_{\text{core}}$:
  * For example, STM32F407 @ 168 MHz requires $w = 5 \text{ wait states}$ (or 4 wait states depending on voltage scaling).
* For an ISR with body code of $N_{\text{inst}}$ instructions:
  $$\text{Penalty}_{\text{flash}} = N_{\text{inst}} \times w$$

### 3. Total ISR Cycles:
$$\text{Cycles}_{\text{ISR}} = 24 + N_{\text{inst}} + (N_{\text{inst}} \times w) = 24 + N_{\text{inst}} \cdot (1 + w)$$

> **Safety Warning:** If an ISR is located in Flash rather than ITCM (Instruction Tightly-Coupled Memory), EmbedSched triggers rule `check_isr_flash_wcet`, noting that placing ISRs in Flash introduces non-deterministic wait-state stalls and instruction cache miss penalties.

---

## 7. Converting Cycles to Microseconds

Once total worst-case cycles ($\text{Cycles}$) are determined, EmbedSched converts cycles into microseconds ($\mu\text{s}$) according to the target core's operating frequency:

1. **Cycle Duration in Nanoseconds ($t_{\text{cycle}}$):**
   $$t_{\text{cycle}} = \frac{1000.0}{f_{\text{core}} \text{ (in MHz)}} \quad [\text{ns}]$$

2. **Execution Time in Microseconds ($C_i$):**
   $$C_i = \frac{\text{Cycles} \times t_{\text{cycle}}}{1000.0} = \frac{\text{Cycles}}{f_{\text{core}} \text{ (in MHz)}} \quad [\mu\text{s}]$$

3. **Precision Rounding:**
   - If $C_i < 10.0\,\mu\text{s}$: rounded to **2 decimal places** (e.g., $1.43\,\mu\text{s}$) to preserve precision for fast control loops.
   - If $C_i \ge 10.0\,\mu\text{s}$: rounded to the **nearest integer** (e.g., $34\,\mu\text{s}$).

---

## 8. Multi-Core Asymmetric Frequency Handling

In heterogeneous multi-core architectures (e.g., STM32H745 / STM32H747):
* **Core 0 (Cortex-M7):** $f_0 = 480\text{ MHz} \implies t_{\text{cycle}} = 2.083\text{ ns}$, $BPI = 2.60$, $CPI = 0.85$
* **Core 1 (Cortex-M4):** $f_1 = 240\text{ MHz} \implies t_{\text{cycle}} = 4.167\text{ ns}$, $BPI = 2.50$, $CPI = 1.15$

EmbedSched inspects each task's `core_id`:
* Looks up `core_types[core_id]` to fetch the specific core's clock frequency and architecture profile.
* The exact same function binary running on Core 1 will correctly calculate a higher cycle count and a longer duration in $\mu\text{s}$ than on Core 0, accurately modeling asymmetric dual-core execution.

---

## 9. Concrete Walkthrough Example

Consider an AUTOSAR periodic task running on an **STM32F407 (Cortex-M4 @ 168 MHz)**:

### Specifications:
* Target: Cortex-M4 $\implies BPI = 2.50\text{ bytes/insn}$, $CPI = 1.15$
* Frequency: $f_{\text{core}} = 168\text{ MHz} \implies t_{\text{cycle}} = \frac{1000}{168} \approx 5.952\text{ ns}$
* Task: `Task_SpeedEstimate`
* Call hierarchy:
  * `Task_SpeedEstimate`: 200 bytes in `.text`
  * calls `filter_kalman`: 350 bytes in `.text`

### Step 1: Compute `filter_kalman` Cycles
$$\text{Instructions} = \frac{350}{2.50} = 140 \text{ instructions}$$
$$\text{Cycles}_{\text{filter}} = \lfloor 140 \times 1.15 \rfloor = 161 \text{ cycles}$$

### Step 2: Compute `Task_SpeedEstimate` Cycles
$$\text{Instructions} = \frac{200}{2.50} = 80 \text{ instructions}$$
$$\text{Cycles}_{\text{own}} = \lfloor 80 \times 1.15 \rfloor = 92 \text{ cycles}$$
$$\text{Total Cycles} = \text{Cycles}_{\text{own}} + \text{Cycles}_{\text{filter}} = 92 + 161 = 253 \text{ cycles}$$

### Step 3: Convert to Microseconds
$$C_i = \frac{253 \text{ cycles}}{168 \text{ MHz}} = 1.50595\,\mu\text{s} \xrightarrow{\text{round to 2 decimals}} \mathbf{1.51\,\mu\text{s}}$$
$$\text{Confidence Tag} = \mathbf{[CALCULATED]}$$
$$\text{Call Chain} = \mathbf{[\text{Task\_SpeedEstimate}, \text{filter\_kalman}]}$$

---

## 10. Downstream Integration in EmbedSched

Once derived, the task WCETs ($C_i$) feed directly into the real-time scheduling algorithms:

1. **CPU Utilization Analysis:**
   $$U = \sum_{i=1}^n \frac{C_i}{T_i} \le n(2^{1/n} - 1) \quad \text{(Liu \& Layland Bound)}$$
2. **Exact Response Time Analysis (Joseph \& Pandya RTA):**
   $$R_i^{(k+1)} = C_i + B_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil C_j$$
3. **Schedulability Verification:**
   Verifies whether $R_i \le D_i$ for all tasks. If $R_i > D_i$, flags a critical deadline miss.
4. **Gantt Chart & Timing Simulation:**
   Feeds into the discrete-event scheduler simulator (`scheduler_sim.py`) to generate execution timelines, response time plots, and start-time jitter charts.

