# Test Case 5: Multicore Partitioned — Asymmetric Cores & Cross-Core IPC

> **Status:** `PASS`  
> **Confidence:** `[CALCULATED]`  
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
| Task Name | Period ($T$) | Deadline ($D$) | Priority | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_VisionProc` | 33,000 µs (33 ms) | 33,000 µs (33 ms) | `null` (EDF) | 10,000 µs (10.0 ms) | 30.30% |
| `Task_ObjectDetect` | 100,000 µs (100 ms) | **80,000 µs (80 ms)** | `null` (EDF) | 20,000 µs (20.0 ms) | 20.00% |
| **Core 0 Total** | — | — | — | — | **50.30%** |

#### Core 1 — Fixed-Priority Rate Monotonic (RM):
| Task Name | Period ($T$) | Deadline ($D$) | Priority | WCET ($C$) | Utilization ($C/T$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `Task_SafetyMonitor` | 10,000 µs (10 ms) | 10,000 µs (10 ms) | 1 (Highest) | 2,000 µs (2.0 ms) | 20.00% |
| `Task_CANPublish` | 50,000 µs (50 ms) | 50,000 µs (50 ms) | 2 (Lowest) | 5,000 µs (5.0 ms) | 10.00% |
| **Core 1 Total** | — | — | — | — | **30.00%** |

#### Cross-Core IPC Channel (`inter_core_channels`):
- **Sender:** `Task_ObjectDetect` (Core 0) $\rightarrow$ **Receiver:** `Task_CANPublish` (Core 1)
- **Shared Region:** `SRAM3`
- **Synchronization Mechanism:** Spinlock (8 cycles) + Write Latency ($1000.0\text{ µs}$)

---

## 4. Step-by-Step Mathematical Calculations

### A. Binary Artifact Inspection & Asymmetric Clock WCET Derivation
The static analyzer inspects [firmware.map](file:///e:/firmware_analyzer/Test_SUITE_2/Test_5/firmware.map). Tasks on Core 0 run at 480 MHz; tasks on Core 1 run at 240 MHz.

#### Core 0 Tasks ($f_0 = 480\text{ MHz}$):

1. **`Task_VisionProc` (`vision_processing`):**
   * Symbol size in `.text.vision_processing`: `0x9f38ea` bytes = $10,434,794\text{ bytes}$
   $$\text{Instructions} = \frac{10,434,794}{2.5} = 4,173,917.6\text{ instructions}$$
   $$\text{Cycles} = 4,173,917.6 \times 1.15 = 4,800,005.24\text{ cycles}$$
   $$C_{\text{Vision}} = \frac{4,800,005.24}{480\text{ MHz}} \approx 10,000.00\text{ µs} \quad (10.0\text{ ms})$$

2. **`Task_ObjectDetect` (`object_detection`):**
   * Symbol size in `.text.object_detection`: `0x13e71ca` bytes = $20,869,578\text{ bytes}$
   $$\text{Instructions} = \frac{20,869,578}{2.5} = 8,347,831.2\text{ instructions}$$
   $$\text{Cycles} = 8,347,831.2 \times 1.15 = 9,600,005.88\text{ cycles}$$
   $$C_{\text{Object}} = \frac{9,600,005.88}{480\text{ MHz}} \approx 20,000.00\text{ µs} \quad (20.0\text{ ms})$$

#### Core 1 Tasks ($f_1 = 240\text{ MHz}$):

3. **`Task_SafetyMonitor` (`safety_monitor`):**
   * Symbol size in `.text.safety_monitor`: `0xfec22` bytes = $1,043,490\text{ bytes}$
   $$\text{Instructions} = \frac{1,043,490}{2.5} = 417,396.0\text{ instructions}$$
   $$\text{Cycles} = 417,396.0 \times 1.15 = 480,005.40\text{ cycles}$$
   $$C_{\text{Safety}} = \frac{480,005.40}{240\text{ MHz}} \approx 2,000.00\text{ µs} \quad (2.0\text{ ms})$$

4. **`Task_CANPublish` (`can_publish`):**
   * Symbol size in `.text.can_publish`: `0x27ce44` bytes = $2,608,708\text{ bytes}$
   $$\text{Instructions} = \frac{2,608,708}{2.5} = 1,043,483.2\text{ instructions}$$
   $$\text{Cycles} = 1,043,483.2 \times 1.15 = 1,200,005.68\text{ cycles}$$
   $$C_{\text{CAN}} = \frac{1,200,005.68}{240\text{ MHz}} \approx 5,000.00\text{ µs} \quad (5.0\text{ ms})$$

---

### B. Inter-Core IPC Spinlock Latency Derivation

`Task_CANPublish` reads cross-core messages written by `Task_ObjectDetect` in `SRAM3`:
* Configured write latency: $1000.0\text{ µs}$
* Hardware spinlock test-and-set cost on Cortex-M4 (Core 1 @ 240 MHz):
  $$\Delta t_{\text{spin}} = \frac{8\text{ cycles}}{240 \times 10^6\text{ cycles/sec}} = 3.333 \times 10^{-8}\text{ sec} = 0.0333\text{ µs}$$
* Total IPC delay / blocking term added to `Task_CANPublish`:
  $$B_{\text{CAN}} = 1000.0\text{ µs} + 0.0333\text{ µs} = 1000.0333\text{ µs} \quad (1.000033\text{ ms})$$

---

### C. Core 0: Dynamic EDF & Processor Demand Analysis (PDA)

Total Core 0 utilization:
$$U_0 = \frac{10,000}{33,000} + \frac{20,000}{100,000} = 0.30303 + 0.20000 = 0.50303 \quad (50.30\%) \le 1.0$$

Because `Task_ObjectDetect` has a constrained deadline ($D_{\text{Object}} = 80\text{ ms} < T_{\text{Object}} = 100\text{ ms}$), simple utilization $U \le 1$ is necessary but insufficient. Schedulability is proven using the **Demand Bound Function (DBF)** $h(L)$:
$$h(L) = \sum_{i=1}^{n} \max\left(0, \left\lfloor \frac{L - D_i}{T_i} \right\rfloor + 1\right) C_i \le L$$

Evaluated at all deadline points $L \in \{33\text{ ms}, 66\text{ ms}, 80\text{ ms}, 99\text{ ms}\}$:

1. **At $L = 33,000\text{ µs}$:**
   $$h(33000) = \left(\left\lfloor \frac{33 - 33}{33} \right\rfloor + 1\right)(10000) + \max\left(0, \left\lfloor \frac{33 - 80}{100} \right\rfloor + 1\right)(20000) = (1)(10000) + 0 = 10,000\text{ µs}$$
   $$\text{Slack} = 33,000 - 10,000 = +23,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

2. **At $L = 66,000\text{ µs}$:**
   $$h(66000) = \left(\left\lfloor \frac{66 - 33}{33} \right\rfloor + 1\right)(10000) + 0 = (2)(10000) = 20,000\text{ µs}$$
   $$\text{Slack} = 66,000 - 20,000 = +46,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

3. **At $L = 80,000\text{ µs}$:**
   $$h(80000) = \left(\left\lfloor \frac{80 - 33}{33} \right\rfloor + 1\right)(10000) + \left(\left\lfloor \frac{80 - 80}{100} \right\rfloor + 1\right)(20000) = (2)(10000) + (1)(20000) = 40,000\text{ µs}$$
   $$\text{Slack} = 80,000 - 40,000 = +40,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

4. **At $L = 99,000\text{ µs}$:**
   $$h(99000) = \left(\left\lfloor \frac{99 - 33}{33} \right\rfloor + 1\right)(10000) + (1)(20000) = (3)(10000) + 20000 = 50,000\text{ µs}$$
   $$\text{Slack} = 99,000 - 50,000 = +49,000\text{ µs} \quad (h(L) \le L \implies \mathbf{PASS})$$

The tightest demand margin occurs at $L = 33,000\text{ µs}$ ($+23,000\text{ µs}$). Core 0 is guaranteed schedulable.
- Worst-Case Response Times on Core 0:
  - `Task_VisionProc`: $R_{\text{Vision}} = 10,000.00\text{ µs} \le 33,000\text{ µs}$ (margin $+23,000\text{ µs}$)
  - `Task_ObjectDetect`: $R_{\text{Object}} = C_{\text{Vision}} + C_{\text{Object}} = 10,000 + 20,000 = 30,000.00\text{ µs} \le 80,000\text{ µs}$ (margin $+50,000\text{ µs}$)

---

### D. Core 1: Rate Monotonic Analysis with IPC Blocking

Core 1 Utilization:
$$U_1 = \frac{2,000}{10,000} + \frac{5,000}{50,000} = 0.20 + 0.10 = 0.3000 \quad (30.00\%) \le U_{\text{bound}} = 2(2^{1/2} - 1) \approx 82.84\%$$

#### 1. Task_SafetyMonitor (Priority 1, $T = 10,000\text{ µs}, D = 10,000\text{ µs}$):
* $\text{hp}(\text{Safety}) = \emptyset, B = 0$
* $R_{\text{Safety}} = C_{\text{Safety}} = 2,000.00\text{ µs} \le 10,000\text{ µs}$  
* **Margin:** $10,000 - 2,000 = +8,000.00\text{ µs}$ (`PASS`)

#### 2. Task_CANPublish (Priority 2, $T = 50,000\text{ µs}, D = 50,000\text{ µs}$):
* $\text{hp}(\text{CAN}) = \{\text{Task\_SafetyMonitor}\}$
* IPC Delay: $B_{\text{CAN}} = 1,000.0333\text{ µs}$
* Recurrence evaluation:
  $$R_{\text{CAN}}^{(0)} = C_{\text{CAN}} + B_{\text{CAN}} = 5,000 + 1,000.0333 = 6,000.0333\text{ µs}$$
  $$R_{\text{CAN}}^{(1)} = 5,000 + 1,000.0333 + \left\lceil \frac{6,000.0333}{10,000} \right\rceil \times 2,000 = 6,000.0333 + (1 \times 2,000) = 8,000.0333\text{ µs}$$
  $$R_{\text{CAN}}^{(2)} = 5,000 + 1,000.0333 + \left\lceil \frac{8,000.0333}{10,000} \right\rceil \times 2,000 = 8,000.0333\text{ µs} \quad (\text{Converged})$$
* **Worst-Case Response Time:** $R_{\text{CAN}} = 8,000.03\text{ µs} \le 50,000\text{ µs}$  
* **Margin:** $50,000 - 8,000.03 = +41,999.97\text{ µs}$ (`PASS`)

---

### E. Hyperperiod Calculation
$$\text{Hyperperiod} = \text{LCM}(33, 100, 10, 50) = \text{LCM}(33, 100) = 3,300\text{ ms} = 3,300,000\text{ µs}$$
Because hyperperiod exceeds 200 ms, the tool emits warning `autosar_hyperperiod_explosion` and renders a clean representative 30 ms timeline window.

---

## 5. Expected vs Actual Tool Output

```
====================================================================================
RESPONSE TIME ANALYSIS (RTA) & SCHEDULABILITY VERDICT
====================================================================================
Task                    Core  Prio  Period µs   WCET µs  Blk µs       Source   WCRT µs  Deadline µs  Margin µs   Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Task_VisionProc            0   EDF      33000  10000.00    0.00   CALCULATED  10000.00        33000   23000.00      PASS
Task_ObjectDetect          0   EDF     100000  20000.00    0.00   CALCULATED  30000.00        80000   50000.00      PASS
Task_SafetyMonitor         1     1      10000   2000.00    0.00   CALCULATED   2000.00        10000    8000.00      PASS
Task_CANPublish            1     2      50000   5000.00 1000.03   CALCULATED   8000.03        50000   41999.97      PASS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Overall: PASS [CALCULATED] — all tasks meet timing deadlines
```

- **Dashboard:** Generates independent horizontal utilization bars for Core 0 ($50.3\%$) and Core 1 ($30.0\%$).
- **Gantt Chart:** Plots parallel timelines for Core 0 and Core 1 over a representative 30 ms window.

---

## 6. How to Run

```bash
python main.py \
  --elf Test_SUITE_2/Test_5/firmware.elf \
  --map Test_SUITE_2/Test_5/firmware.map \
  --ld  Test_SUITE_2/Test_5/linker.ld \
  --chip Test_SUITE_2/Test_5/stm32h745.yaml \
  --autosar-config Test_SUITE_2/Test_5/schedule.json \
  --charts-dir Test_SUITE_2/Test_5/charts/
```
