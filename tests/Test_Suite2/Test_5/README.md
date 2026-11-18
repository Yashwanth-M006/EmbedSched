# Test Case 5: Multicore Partitioned — Asymmetric Cores & Cross-Core IPC

> **Status:** `PASS`  
> **Confidence:** `[IPET]`  
> **Architecture:** STM32H745 (Dual-Core: Cortex-M7 @ 480 MHz + Cortex-M4 @ 240 MHz)  
> **Schedulers:** Core 0 = Earliest Deadline First (EDF) | Core 1 = Rate Monotonic (RM)

---

## 1. What This Test Signifies

Modern automotive Domain Control Units (DCUs) and advanced MCUs (like the STM32H7, NXP S32K3, or Infineon AURIX TC3xx) execute software partitioned across multiple asymmetric physical cores.

Test Case 5 verifies that EmbedSched:
1. **Enforces Strict Core Partitioning:** Tasks assigned to Core 0 do not create false preemptive interference on Core 1 tasks.
2. **Supports Heterogeneous Per-Core Scheduling Algorithms:** Concurrently evaluates dynamic-priority **Earliest Deadline First (EDF)** on Core 0 alongside fixed-priority **Rate Monotonic (RM)** on Core 1.
3. **Accounts for Asymmetric Core Frequencies:** Converts cycles to time using the specific clock speed of each core (480 MHz for M7 vs. 240 MHz for M4).
4. **Calculates Inter-Core IPC Latency & Spinlock Overhead:** Automatically injects hardware bus latencies and spinlock contention cycles from shared SRAM3 memory into cross-core receiver tasks.

---

## 2. Why It Was Performed

1. **Dual-Core Isolation:** A defect in multi-core schedulability tools is assuming a global priority space or accidentally accumulating preemption across distinct CPU cores. EmbedSched proves complete architectural partition independence.
2. **EDF Processor Demand Analysis on Constrained Deadlines:** Simple utilization checks ($U \le 1.0$) only prove EDF schedulability if deadlines equal periods ($D = T$). Core 0 contains `Task_ObjectDetect` with a constrained deadline ($D = 80\text{ ms} < T = 100\text{ ms}$). EmbedSched switches to Baruah's **Processor Demand Analysis (PDA)**.
3. **Cross-Core Synchronization Overhead:** Tasks that exchange data across cores (e.g. vision results to CAN transmission) incur hardware spinlock hold times and AHB bus bridge delays. EmbedSched models these delays directly into response time margins.

---

## 3. Configuration & Task Set

### Hardware Definition (`stm32h745.yaml`)
- **Core 0:** Cortex-M7 running at $f_0 = 480\text{ MHz}$ ($t_{\text{cycle}, 0} \approx 2.0833\text{ ns}$).
- **Core 1:** Cortex-M4 running at $f_1 = 240\text{ MHz}$ ($t_{\text{cycle}, 1} \approx 4.1667\text{ ns}$).
- **Shared Memory:** `SRAM3` (32 KB @ `0x30040000`), spinlock overhead = 8 hardware clock cycles on Core 1.

### Task Set (`schedule.json`)

#### Core 0 — Dynamic Earliest Deadline First (EDF):
| Task Name | Entry Function | Period ($T$) | Deadline ($D$) | Priority | Memory Placement |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_VisionProc` | `vision_processing` | 33,000 µs (33 ms) | 33,000 µs (33 ms) | `null` (EDF) | AXI-SRAM |
| `Task_ObjectDetect` | `object_detection` | 100,000 µs (100 ms) | **80,000 µs (80 ms)** | `null` (EDF) | AXI-SRAM |

#### Core 1 — Fixed-Priority Rate Monotonic (RM):
| Task Name | Entry Function | Period ($T$) | Deadline ($D$) | Priority | Memory Placement |
|:---|:---|:---:|:---:|:---:|:---:|
| `Task_SafetyMonitor` | `safety_monitor` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | SRAM1 |
| `Task_CANPublish` | `can_publish` | 50,000 µs (50 ms) | 50,000 µs (50 ms) | 2 (Lowest) | SRAM1 |

#### Cross-Core IPC Channel (`inter_core_channels`):
- **Sender:** `Task_ObjectDetect` (Core 0) $\rightarrow$ **Receiver:** `Task_CANPublish` (Core 1)
- **Shared Region:** `SRAM3`
- **Synchronization Mechanism:** Spinlock (8 cycles) + Write Latency ($1000.0\text{ µs}$)

---

## 4. Step-by-Step Mathematical Calculations

### A. IPET WCET Derivation from Binary Artifacts
EmbedSched disassembles the firmware binary and runs microarchitectural pipeline analysis for each core:

1. **`Task_VisionProc` (Core 0, Cortex-M7 @ 480 MHz):**
   * Disassembled basic blocks in AXI-SRAM:
   * Worst-case execution cycles: $8,478,240\text{ cycles}$
   * $\text{WCET} = \frac{8,478,240}{480\text{ MHz}} = \mathbf{17,663.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

2. **`Task_ObjectDetect` (Core 0, Cortex-M7 @ 480 MHz):**
   * Worst-case execution cycles: $16,956,480\text{ cycles}$
   * $\text{WCET} = \frac{16,956,480}{480\text{ MHz}} = \mathbf{35,326.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

3. **`Task_SafetyMonitor` (Core 1, Cortex-M4 @ 240 MHz):**
   * Worst-case execution cycles: $847,920\text{ cycles}$
   * $\text{WCET} = \frac{847,920}{240\text{ MHz}} = \mathbf{3,533.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

4. **`Task_CANPublish` (Core 1, Cortex-M4 @ 240 MHz):**
   * Worst-case execution cycles: $2,119,680\text{ cycles}$
   * $\text{WCET} = \frac{2,119,680}{240\text{ MHz}} = \mathbf{8,832.00\text{ µs}} \quad (\text{Confidence: } [\text{IPET}])$

---

### B. Core 0: Dynamic EDF & Processor Demand Analysis (PDA)
Because `Task_ObjectDetect` has a constrained deadline ($D = 80\text{ ms} < T = 100\text{ ms}$), EmbedSched evaluates Baruah's demand bound function:
$$h(t) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{t - D_i}{T_i} \right\rfloor + 1\right) C_i \le t$$

Total Core 0 Utilization:
$$U_0 = \frac{17,663}{33,000} + \frac{35,326}{100,000} = 53.52\% + 35.33\% = \mathbf{88.8\%} \le 100\%$$

Exact EDF Response Times on Core 0:
- `Task_VisionProc`: $R_{\text{Vision}} = \mathbf{22,315.00\text{ µs}} \le 33,000\text{ µs} \implies \text{Slack Margin: } \mathbf{+10,685.00\text{ µs}}$ (`PASS`)
- `Task_ObjectDetect`: $R_{\text{Object}} = \mathbf{70,652.00\text{ µs}} \le 80,000\text{ µs} \implies \text{Slack Margin: } \mathbf{+9,348.00\text{ µs}}$ (`PASS`)

---

### C. Core 1: Rate Monotonic Analysis with Cross-Core IPC Blocking
Total Core 1 Utilization:
$$U_1 = \frac{3,533}{10,000} + \frac{8,832}{50,000} = 35.33\% + 17.66\% = \mathbf{53.0\%} \le U_{\text{bound}}(2) \approx 82.84\%$$

1. **`Task_SafetyMonitor` (Priority 1):**
   * Preempting tasks: None ($\text{hp} = \emptyset$)
   * $R_{\text{Safety}} = C_{\text{Safety}} = \mathbf{3,533.00\text{ µs}} \le 10,000\text{ µs}$
   * Slack Margin: $10,000 - 3,533 = \mathbf{+6,467.00\text{ µs}}$ (`PASS`)

2. **`Task_CANPublish` (Priority 2):**
   * Preempting tasks: `Task_SafetyMonitor` ($C = 3,533\text{ µs}, T = 10,000\text{ µs}$)
   * Cross-Core IPC Delay from Core 0:
     $$B_{\text{IPC}} = \text{Write Latency} + \frac{\text{Spinlock Cycles}}{f_1} = 1,000.0\text{ µs} + \frac{8}{240\text{ MHz}} = \mathbf{1,000.0333\text{ µs}}$$
   * Recurrence evaluation:
     $$R_{\text{CAN}}^{(0)} = C_{\text{CAN}} + B_{\text{IPC}} = 8,832 + 1,000.0333 = 9,832.0333\text{ µs}$$
     $$R_{\text{CAN}}^{(1)} = 9,832.0333 + \left\lceil \frac{9,832.0333}{10,000} \right\rceil \times 3,533 = 9,832.0333 + 3,533 = 13,365.0333\text{ µs}$$
     $$R_{\text{CAN}}^{(2)} = 9,832.0333 + \left\lceil \frac{13,365.0333}{10,000} \right\rceil \times 3,533 = 9,832.0333 + (2 \times 3,533) = \mathbf{16,898.03\text{ µs}}\quad (\text{Converged})$$
   * Slack Margin: $50,000 - 16,898.03 = \mathbf{+33,101.97\text{ µs}}$ (`PASS`)

---

## 5. Expected vs Actual Tool Output

```
==============================================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
==============================================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_VisionProc            0   EDF      33000  17663.00    0.00         IPET  22315.00        33000   10685.00
Task_ObjectDetect          0   EDF     100000  35326.00    0.00         IPET  70652.00        80000    9348.00
Task_SafetyMonitor         1     1      10000   3533.00    0.00         IPET   3533.00        10000    6467.00
Task_CANPublish            1     2      50000   8832.00 1000.03         IPET  16898.03        50000   33101.97
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [IPET] — all tasks meet deadlines
```

- **Health Score:** 90 / 100
- **Schedulability Dashboard:**
  - Core 0 (EDF): 88.8% duty
  - Core 1 (RM): 53.0% duty (guaranteed below RM bound)
- **Overall Verdict:** `PASS [IPET]`

---

## 6. How to Run

```bash
python main.py \
  --elf tests/Test_Suite2/Test_5/firmware.elf \
  --map tests/Test_Suite2/Test_5/firmware.map \
  --ld  tests/Test_Suite2/Test_5/linker.ld \
  --chip tests/Test_Suite2/Test_5/stm32h745.yaml \
  --autosar-config tests/Test_Suite2/Test_5/schedule.json \
  --charts-dir tests/Test_Suite2/Test_5/charts/
```
