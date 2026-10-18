# Test Case 7: Stack Overflow Under Preemption — Cross-Domain Analysis

> **Status:** `WARNING` (Concurrent Stack Overflow Risk)  
> **Confidence:** `[STATIC]`  
> **Architecture:** STM32F407 (Cortex-M4, 168 MHz)  
> **Scheduler:** Single-Core Preemptive Rate Monotonic (RM)

---

## 1. What This Test Signifies

Test Case 7 demonstrates a critical capability of EmbedSched: **cross-domain synthesis** between **static memory/stack analysis** and **runtime preemption scheduling**.

In embedded systems with a shared execution stack (standard in RTOS ISR handling, bare-metal loops, or OSEK Basic Tasks BCC1 sharing an execution stack):
- Looking at each task's stack usage individually indicates that all tasks fit comfortably within the declared stack size.
- However, when scheduled under preemptive priority, **higher-priority tasks preempt lower-priority tasks at their deepest call frames**, causing their activation records to co-exist simultaneously in physical memory.

Test Case 7 proves that EmbedSched calculates the cumulative concurrent stack pressure across the preemption chain and flags potential stack overflows that neither a pure static stack analyzer nor a pure RTOS timing tool could detect alone.

---

## 2. Why It Was Performed

1. **The Most Feared Silent Embedded Bug:** Stack overflow into adjacent `.bss` or data structures causes non-deterministic system resets, memory corruption, and erratic behavior that is nearly impossible to reproduce in a lab.
2. **Exposing Single-Task Stack Fallacies:** A compiler tool that only reports individual task stack depths (e.g. GCC `-fstack-usage` reporting `max = 1808B`) provides a false sense of security when the declared stack is 4096B.
3. **Automated Linker Validation:** Cross-references the calculated concurrent stack pressure against `_Min_Stack_Size` parsed from `linker.ld`.

---

## 3. Configuration & Task Set

### Linker Script Configuration (`linker.ld`)
- **Declared Stack Size:** `_Min_Stack_Size = 0x1000` (4,096 bytes)
- **Stack Section Placement:** Placed in zero-wait-state DTCM (`0x10000000`).

### Tasks & Individual Stack Frame Allocations (`main.c`):

| Task Name | Entry Function | Priority | Period ($T$) | Buffer Allocation | Total Stack Frame (with ABI Alignment) |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_MotorControl` | `motor_control_loop` | 1 (Highest) | 1,000 µs (1 ms) | `volatile char buf[1800]` | **1,808 bytes** |
| `Task_SensorAgg` | `sensor_aggregate` | 2 | 20,000 µs (20 ms) | `volatile char buf[1400]` | **1,408 bytes** |
| `Task_CANTransmit` | `can_transmit_handler` | 3 (Lowest) | 100,000 µs (100 ms) | `volatile char buf[900]` | **912 bytes** |

---

## 4. Step-by-Step Mathematical Calculations

### A. Static Stack Analysis & Concurrent Preemption Chain

#### 1. Individual Task Frame Analysis:
Under ARM AAPCS (ARM Architecture Procedure Call Standard), stack frames must be 8-byte aligned at public interfaces, and compiler prologue instructions (`push {r4, lr}`) reserve frame space:
- `can_transmit_handler`: $900\text{ bytes (buf)} + 12\text{ bytes (frame/alignment)} = 912\text{ bytes}$
- `sensor_aggregate`: $1,400\text{ bytes (buf)} + 8\text{ bytes (frame/alignment)} = 1,408\text{ bytes}$
- `motor_control_loop`: $1,800\text{ bytes (buf)} + 8\text{ bytes (frame/alignment)} = 1,808\text{ bytes}$

Each individual task comfortably fits within the 4,096-byte stack limit:
- $\Delta_{\text{CAN}} = 4,096 - 912 = +3,184\text{ bytes free}$
- $\Delta_{\text{Sensor}} = 4,096 - 1,408 = +2,688\text{ bytes free}$
- $\Delta_{\text{Motor}} = 4,096 - 1,808 = +2,288\text{ bytes free}$

#### 2. Worst-Case Preemption Chain Math:
Because the tasks are scheduled under preemptive Rate Monotonic priority ($P_{\text{Motor}} > P_{\text{Sensor}} > P_{\text{CAN}}$):
1. Lowest-priority `Task_CANTransmit` is active at its deepest frame $\implies 912\text{ bytes}$ on stack.
2. `Task_SensorAgg` releases and preempts `Task_CANTransmit` $\implies 912 + 1,408 = 2,320\text{ bytes}$.
3. Highest-priority `Task_MotorControl` releases and preempts `Task_SensorAgg` $\implies 2,320 + 1,808 = 4,128\text{ bytes}$.

$$\text{Stack}_{\text{concurrent}} = \sum_{i=1}^{3} \text{Stack}(\tau_i) = 912 + 1,408 + 1,808 = \mathbf{4,128\text{ bytes}}$$

#### 3. Stack Overflow Margin Evaluation:
$$\text{Margin}_{\text{stack}} = \text{\_Min\_Stack\_Size} - \text{Stack}_{\text{concurrent}} = 4,096\text{ B} - 4,128\text{ B} = \mathbf{-32\text{ bytes}}$$

The concurrent worst-case stack depth **exceeds declared stack capacity by 32 bytes**. Under worst-case scheduling alignment, the stack pointer decrements below the DTCM stack boundary, corrupting adjacent memory. The analyzer flags warning `autosar_concurrent_stack` (-20 points deduction).

---

### B. Timing & Schedulability Verification

In parallel with stack analysis, the tool verifies task execution timing from [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_7/firmware.map) at $168\text{ MHz}$:
- `motor_control_loop`: $29,230\text{ bytes} \implies C = 80.00\text{ µs}$ ($T = 1,000\text{ µs}, U = 8.00\%$)
- `sensor_aggregate`: $14,620\text{ bytes} \implies C = 40.00\text{ µs}$ ($T = 20,000\text{ µs}, U = 0.20\%$)
- `can_transmit_handler`: $7,316\text{ bytes} \implies C = 20.00\text{ µs}$ ($T = 100,000\text{ µs}, U = 0.02\%$)

Total system utilization:
$$U = 8.00\% + 0.20\% + 0.02\% = 8.22\% \ll U_{\text{bound}} = 77.98\%$$

RTA recurrence:
- $R_{\text{Motor}} = 80.00\text{ µs} \le 1,000\text{ µs}$ (`PASS`, margin $+920\text{ µs}$)
- $R_{\text{Sensor}} = 40 + \lceil 40/1000 \rceil \times 80 = 120.00\text{ µs} \le 20,000\text{ µs}$ (`PASS`, margin $+19,880\text{ µs}$)
- $R_{\text{CAN}} = 20 + \lceil 20/1000 \rceil \times 80 + \lceil 20/20000 \rceil \times 40 = 140.00\text{ µs} \le 100,000\text{ µs}$ (`PASS`, margin $+99,860\text{ µs}$)

**Engineering Takeaway:** All tasks meet their real-time timing deadlines with massive margins (Score: 80/100), yet the firmware will fail catastrophically in production due to concurrent stack overflow. Only a unified timing and memory analyzer can detect this.

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_CANTransmit           0     3     100000     20.00    0.00   CALCULATED    140.00       100000   99860.00      PASS
Task_SensorAgg             0     2      20000     40.00    0.00   CALCULATED    120.00        20000   19880.00      PASS
Task_MotorControl          0     1       1000     80.00    0.00   CALCULATED     80.00         1000     920.00      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

### Generated Findings:
- **`[WARNING] autosar_concurrent_stack` (-20 points):**  
  *Concurrent worst-case stack depth (4128B) exceeds declared stack size (4096B) — stack overflow possible under full preemption [STATIC].*  
  *Fix: Increase `_Min_Stack_Size` in `linker.ld` to at least `0x1100` (4352 bytes) or reduce local buffer allocations.*
- **`[INFO] explicit_stack_found`:**  
  *Explicit stack reservation found. `_Min_Stack_Size` = 0x1000 (4096 bytes).*

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_7/firmware.elf \
  --map Test_SUITE_2/Test_7/firmware.map \
  --ld  Test_SUITE_2/Test_7/linker.ld \
  --chip chips/stm32f407.yaml \
  --autosar-config Test_SUITE_2/Test_7/schedule.json \
  --charts-dir Test_SUITE_2/Test_7/charts/
```
