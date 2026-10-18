# Buttazzo Test Suite — Test Case 10: Stack Overflow Exactly at Boundary (Buttazzo §5.1)

> **Source:** Giorgio Buttazzo, *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*, Section 5.1 (Shared Stack and Memory Models).  
> **Status:** `WARNING (Boundary & Overflow Detection)`  
> **Declared Stack Size:** `2,400 Bytes (_Min_Stack_Size in linker.ld)`  
> **Case 1 (Exact Boundary):** `800 + 800 + 800 = 2,400B = declared size (WARNING, 0 Margin, NOT CRITICAL)`  
> **Case 2 (Off-by-One Overflow):** `801 + 800 + 800 = 2,401B > 2,400B declared size (WARNING, Stack Overflow)`  
> **Algorithm:** `Concurrent Preemptive Stack Analysis`  
> **Confidence:** `[STATIC]`  
> **Scheduler:** Single-Core Preemptive Fixed-Priority (RM)

---

## 1. What This Test Signifies

Test Case 10 in the `buttazo_test` suite evaluates the **exact boundary and off-by-one behavior** of concurrent stack depth analysis under full preemptive execution:
1. **The Shared-Stack Preemption Model:** Under single-stack embedded OS architectures (e.g. OSEK/AUTOSAR Basic Tasks or single interrupt/main stacks), tasks execute on a shared stack area. Under worst-case preemption:
   - Lowest priority task $\tau_3$ is activated and allocates its stack ($800\text{ B}$).
   - $\tau_3$ is preempted by medium priority task $\tau_2$, which allocates its stack ($800\text{ B}$).
   - $\tau_2$ is preempted by highest priority task $\tau_1$, which allocates its stack ($800\text{ B}$ / $801\text{ B}$).
   - Total concurrent stack depth equals the sum: $\sum_{i=1}^n \text{Stack}_i$.
2. **Boundary Testing ($2,400\text{ B} = 2,400\text{ B}$):**
   - When the cumulative stack depth exactly equals the declared stack size ($2,400\text{ B}$ declared via `_Min_Stack_Size`), the condition for overflow ($> 2,400\text{ B}$) is strictly **not met** ($2,400 > 2,400 \implies \text{FALSE}$).
   - The tool emits a **WARNING (not CRITICAL)** identifying that the stack depth reaches capacity with zero headroom.
3. **Off-by-One Overflow Testing ($2,401\text{ B} > 2,400\text{ B}$):**
   - Increasing $\tau_1$'s stack by a single byte ($801\text{ B}$) pushes total concurrent stack depth to $2,401\text{ B}$.
   - The overflow condition ($2,401 > 2,400$) evaluates to **TRUE**, triggering the warning `Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B)`.

---

## 2. Theoretical Background & Specification

Three periodic tasks on Core 0 sharing a single stack allocation declared in `linker.ld` (`_Min_Stack_Size = 2400`):

| Task | Priority | Period ($T_i$) | Deadline ($D_i$) | Stack Usage (Case 1) | Stack Usage (Case 2) | Preemption Role |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\tau_1$ | **1 (Highest)** | $10\text{ ms}$ | $10\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{801\text{ B}}$ | Preempts $\tau_2$ and $\tau_3$ |
| $\tau_2$ | **2 (Medium)** | $15\text{ ms}$ | $15\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{800\text{ B}}$ | Preempts $\tau_3$, preempted by $\tau_1$ |
| $\tau_3$ | **3 (Lowest)** | $20\text{ ms}$ | $20\text{ ms}$ | $\mathbf{800\text{ B}}$ | $\mathbf{800\text{ B}}$ | Preempted by $\tau_2$ and $\tau_1$ |

**Declared Stack Size in Linker Script:**
$$\text{Declared Capacity} = \text{\_Min\_Stack\_Size} = 2,400\text{ Bytes}\ (0\text{x}0960)$$

---

## 3. Step-by-Step Mathematical Calculations

### Case 1: Exact Boundary ($2,400\text{ B} = 2,400\text{ B}$)

Under worst-case preemption ($\tau_3$ preempted by $\tau_2$ preempted by $\tau_1$):
$$\text{Total Stack Depth} = \text{Stack}(\tau_3) + \text{Stack}(\tau_2) + \text{Stack}(\tau_1) = 800 + 800 + 800 = \mathbf{2,400\text{ Bytes}}$$

**Comparison:**
$$\text{Total Depth} = 2,400\text{ B} \le \text{Declared Capacity} = 2,400\text{ B}$$
- Condition for overflow ($2,400 > 2,400$) is **FALSE**.
- Severity: **`WARNING` (not `CRITICAL`)** since $2,400 = 2,400$, not greater than.
- Diagnostic finding:
  ```text
  [WARNING] [STATIC] autosar_concurrent_stack
    Concurrent worst-case stack depth (2400B) reaches declared stack size (2400B) with zero margin under full preemption [STATIC]
  ```

---

### Case 2: Off-by-One Overflow ($2,401\text{ B} > 2,400\text{ B}$)

Changing $\tau_1$'s stack usage from $800\text{ B}$ to $801\text{ B}$:
$$\text{Total Stack Depth} = \text{Stack}(\tau_3) + \text{Stack}(\tau_2) + \text{Stack}(\tau_1) = 800 + 800 + 801 = \mathbf{2,401\text{ Bytes}}$$

**Comparison:**
$$\text{Total Depth} = 2,401\text{ B} > \text{Declared Capacity} = 2,400\text{ B} \implies \mathbf{TRUE\ (+1\text{ Byte Overflow})}$$
- Condition for overflow ($2,401 > 2,400$) is **TRUE**.
- Severity: **`WARNING`**
- Diagnostic finding:
  ```text
  [WARNING] [STATIC] autosar_concurrent_stack
    Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B) — stack overflow possible under full preemption [STATIC]
  ```

---

## 4. Comparison of Expected vs. Actual Tool Output

| Test Scenario | Evaluated Stack Expression | Expected Tool Output | Actual Tool Output (`results.md`) | Match Status |
|:---|:---:|:---:|:---:|:---:|
| **Case 1: Exact Boundary** | $800 + 800 + 800 = 2,400\text{B} = 2,400\text{B}$ | `WARNING (not CRITICAL)` | `[WARNING] Concurrent worst-case stack depth (2400B) reaches declared stack size (2400B) with zero margin` | **EXACT MATCH** |
| **Case 2: Off-by-One** | $801 + 800 + 800 = 2,401\text{B} > 2,400\text{B}$ | `WARNING fires` | `[WARNING] Concurrent worst-case stack depth (2401B) exceeds declared stack size (2400B) — stack overflow possible` | **EXACT MATCH** |

---

## 5. Firmware Implementation Details

- **Hardware Architecture:** STM32F407 Cortex-M4
- **Linker Configuration (`linker.ld`):**
  - Declared stack symbol: `_Min_Stack_Size = 2400;` ($0\text{x}0960$)
  - Placed in DTCM RAM: `.stack : { . = . + _Min_Stack_Size; } >DTCM`
- **Firmware Functions:**
  - `task1`: Entry for $\tau_1$
  - `task2`: Entry for $\tau_2$
  - `task3`: Entry for $\tau_3$

---

## 6. How to Reproduce

1. **Compile ARM Firmware:**
   ```powershell
   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O0 -g -ffunction-sections -T linker.ld "-Wl,-Map=firmware.map" -nostartfiles -o firmware.elf main.c
   ```
2. **Execute Boundary Analysis (Case 1: 2,400B):**
   - Ensure `schedule.json` has `tau1` `stack_bytes: 800`.
   ```powershell
   python run.py
   ```
3. **Execute Off-by-One Overflow Analysis (Case 2: 2,401B):**
   - Update `schedule.json` to set `tau1` `stack_bytes: 801`.
   ```powershell
   python run.py
   ```
4. **Inspect Generated Reports:**
   - Case 1 Report: [`results_boundary_2400.md`](file:///e:/firmware_analyzer/buttazo_test/Test_10/results_boundary_2400.md)
   - Case 2 Report: [`results.md`](file:///e:/firmware_analyzer/buttazo_test/Test_10/results.md)
