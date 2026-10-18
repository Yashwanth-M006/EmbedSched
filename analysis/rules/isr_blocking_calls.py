"""
isr_blocking_calls.py — Detects ISRs that call known-blocking functions.

Rule: isr_calls_blocking_function  WARNING (-25)

A blocking function is one that busy-waits or polls a hardware register in
a loop (e.g. HAL_Delay, HAL_UART_Transmit in polling mode). Calling such
a function from inside an ISR:

  1. Holds the CPU inside the ISR for the entire blocking duration.
  2. Prevents all lower-priority interrupts from running.
  3. Can cause deadlock if the blocking call depends on a SysTick/RTOS
     tick that is itself at a lower or equal priority than the ISR.

Detection:
  - DFS from each ISR entry point through the call graph.
  - At each node, check if the function name appears in BLOCKING_FUNCTIONS.
  - Report every ISR that reaches at least one blocking callee.

The blocklist is hardcoded here and can be extended by parsing a
hal_stubs/*.map file passed via --hal-map argument (future extension).
"""

from typing import List, Dict, Set, Tuple
from models.finding import Finding

# ── Hardcoded blocklist ──────────────────────────────────────────────────────
# Functions that are KNOWN to be blocking (poll/busy-wait) and MUST NOT be
# called from ISR context. Matched by exact function name (case-sensitive).
BLOCKING_FUNCTIONS: Dict[str, str] = {
    # STM32 HAL polling-mode functions
    "HAL_Delay":                "Busy-wait on SysTick counter; deadlocks if SysTick <= ISR priority",
    "HAL_UART_Transmit":        "Polls USART_SR_TXE/TC bits until TX complete or timeout",
    "HAL_UART_Receive":         "Polls USART_SR_RXNE bit until data received or timeout",
    "HAL_SPI_Transmit":         "Polls SPI_SR_TXE and BSY bits",
    "HAL_SPI_Receive":          "Polls SPI_SR_RXNE and BSY bits",
    "HAL_SPI_TransmitReceive":  "Polls SPI_SR_TXE, RXNE, BSY bits",
    "HAL_I2C_Master_Transmit":  "Polls I2C_SR1_TXE/BTF; holds bus for full transfer",
    "HAL_I2C_Master_Receive":   "Polls I2C_SR1_RXNE/BTF",
    "HAL_I2C_Slave_Transmit":   "Polls I2C status registers",
    "HAL_I2C_Slave_Receive":    "Polls I2C status registers",
    "HAL_I2C_Mem_Write":        "Polls I2C for each byte and ACK",
    "HAL_I2C_Mem_Read":         "Polls I2C for each byte and ACK",
    "HAL_ADC_PollForConversion":"Polls ADC_SR_EOC bit",
    "HAL_FLASH_Program":        "Polls FLASH_SR_BSY; up to 16 byte write time",
    "HAL_FLASH_Erase":          "Polls FLASH_SR_BSY; sector erase can take 1-4 seconds",
    "HAL_FLASHEx_Erase":        "Polls FLASH_SR_BSY; sector erase can take 1-4 seconds",
    "HAL_RTC_WaitForSynchro":   "Polls RTC_ISR_RSF; up to 2 RTC clock cycles",
    "HAL_SD_WriteBlocks":       "Polls SDIO data transfer status",
    "HAL_SD_ReadBlocks":        "Polls SDIO data transfer status",
    # FreeRTOS / CMSIS-RTOS
    "osDelay":                  "CMSIS-RTOS: suspends task; ISR context forbidden",
    "vTaskDelay":               "FreeRTOS: suspends calling task; ISR context forbidden",
    "xQueueSend":               "FreeRTOS: may block if queue full (use xQueueSendFromISR)",
    "xQueueReceive":            "FreeRTOS: may block waiting for item (use xQueueReceiveFromISR)",
    "osMutexAcquire":           "CMSIS-RTOS: can block indefinitely; ISR context forbidden",
    # stdlib (newlib-nano)
    "printf":                   "Calls vfprintf -> _write; may block on internal locks",
    "fprintf":                  "Same as printf — may block on file locks",
    "malloc":                   "newlib: takes __malloc_lock; not reentrant from ISR",
    "free":                     "newlib: takes __malloc_lock; not reentrant from ISR",
    "puts":                     "Calls _write; may block on stdout lock",
}


def _dfs_find_blocking(
    func: str,
    call_graph: Dict[str, Set[str]],
    visited: Set[str],
) -> List[Tuple[str, str]]:
    """
    DFS from 'func' through call_graph. Returns list of (callee_name, reason)
    for every blocking function reachable from 'func' (including direct calls).
    Visited set prevents infinite loops on cyclic graphs.
    """
    if func in visited:
        return []
    visited = visited | {func}

    found = []
    for callee in call_graph.get(func, set()):
        if callee in BLOCKING_FUNCTIONS:
            found.append((callee, BLOCKING_FUNCTIONS[callee]))
        # Recurse into callee (to catch indirect calls: ISR -> helper -> HAL_Delay)
        found.extend(_dfs_find_blocking(callee, call_graph, visited))

    return found


def check_isr_blocking_calls(
    isr_names: List[str],
    call_graph: Dict[str, Set[str]],
) -> List[Finding]:
    """
    For each ISR entry point, DFS the call graph and flag any that
    reach a known-blocking function. One finding per offending ISR,
    listing all blocking callees found.
    """
    findings = []

    for isr in isr_names:
        # Only analyse ISRs that appear in the call graph
        if isr not in call_graph:
            continue

        blocking_hits = _dfs_find_blocking(isr, call_graph, set())
        if not blocking_hits:
            continue

        # Deduplicate (same callee may be reached via multiple paths)
        seen: Set[str] = set()
        unique_hits: List[Tuple[str, str]] = []
        for name, reason in blocking_hits:
            if name not in seen:
                seen.add(name)
                unique_hits.append((name, reason))

        # Build the finding message
        callee_lines = []
        for name, reason in unique_hits:
            callee_lines.append(
                f"{name}\n"
                f"      Mechanism: {reason}\n"
                f"      Risk: CPU held in ISR for the full blocking duration."
            )
        callees_str = "\n    - ".join(callee_lines)

        msg = (
            f"ISR '{isr}' calls known-blocking function(s) in its call graph:\n"
            f"    - {callees_str}\n"
            f"\n"
            f"  Blocking calls inside an ISR:\n"
            f"    1. Hold the CPU for the entire blocking duration.\n"
            f"    2. Block ALL interrupts at equal or lower priority.\n"
            f"    3. Risk deadlock if the blocking function depends on a lower-priority\n"
            f"       interrupt (e.g. HAL_Delay needs SysTick to fire)."
        )

        fix_suggestions = []
        for name, _ in unique_hits:
            if "HAL_Delay" in name:
                fix_suggestions.append(
                    "Replace HAL_Delay() with a non-blocking timer flag: "
                    "set a flag in the ISR and handle delay logic in main-loop context."
                )
            elif "HAL_UART_Transmit" in name or "HAL_UART_Receive" in name:
                fix_suggestions.append(
                    f"Replace {name}() with {name}_IT() (interrupt-driven) "
                    "or the DMA variant and handle completion in a callback."
                )
            elif "HAL_SPI" in name:
                fix_suggestions.append(
                    f"Replace {name}() with {name}_IT() or {name}_DMA()."
                )
            elif "HAL_I2C" in name:
                fix_suggestions.append(
                    f"Replace {name}() with {name}_IT() (interrupt-driven variant)."
                )
            elif name in ("printf", "fprintf", "puts"):
                fix_suggestions.append(
                    f"Replace {name}() with a lockless ring buffer; "
                    "drain buffer from main-loop context."
                )
            elif name in ("malloc", "free"):
                fix_suggestions.append(
                    "Pre-allocate buffers statically. "
                    "Dynamic memory allocation from ISR context is undefined behaviour in newlib."
                )
            elif "vTaskDelay" in name or "osDelay" in name:
                fix_suggestions.append(
                    f"Replace {name}() with xQueueSendFromISR() or "
                    "a FreeRTOS software timer callback."
                )
            else:
                fix_suggestions.append(
                    f"Replace {name}() with a non-blocking interrupt-driven alternative."
                )

        fix_str = " ".join(fix_suggestions)

        findings.append(Finding(
            rule="isr_calls_blocking_function",
            severity="WARNING",
            tag="[STATIC]",
            message=msg,
            fix=fix_str,
        ))

    return findings
