/*
 * Test Case 11: WCET Confidence Propagation
 *
 * Three tasks — three confidence tiers:
 *
 *   Task_A  entry: task_a_body     → derived from Renode trace         → [SIMULATED]
 *   Task_B  entry: task_b_body     → derived from timing model formula → [CALCULATED]
 *   Task_C  entry: task_c_missing  → function missing from ELF / .su   → [HEURISTIC]  ← key
 *
 * task_a_body has an execution trace supplied via --renode-trace.
 * task_b_body is present in ELF and calculated from code size.
 * task_c_missing is referenced only in schedule.json, not compiled here,
 * so the WCET extractor falls back to its heuristic placeholder.
 *
 * Expected outcome:
 *   - Task_A: [SIMULATED]
 *   - Task_B: [CALCULATED]
 *   - Task_C: [HEURISTIC]   ← lowest confidence contaminates the verdict
 *   - VERDICT: SCHEDULABLE [HEURISTIC] (or PASS [HEURISTIC])
 *   - WARNING: autosar_heuristic_wcet fires for Task_C
 *   - Lowest confidence propagates to overall verdict
 */

/* ── Task A body: ~6 ms equivalent at 168 MHz ─────────────────────────── */
void task_a_body(void) {
    /* 25200 bytes = ~10080 Thumb-2 instrs × 1.15 penalty ≈ 11592 cycles
       at 168 MHz → ~69 µs. Kept small so we stay schedulable. */
    __asm__ volatile(".fill 1600, 1, 0x00\n");
}

/* ── Task B body: ~3 ms equivalent ────────────────────────────────────── */
void task_b_body(void) {
    __asm__ volatile(".fill 800, 1, 0x00\n");
}

/* ── task_c_missing is intentionally NOT defined here ─────────────────── */
/* The schedule.json refers to "task_c_missing" which has no ELF symbol.
   The WCET extractor will assign [HEURISTIC] and emit a WARNING.         */

int main(void) {
    task_a_body();
    task_b_body();
    while (1);
    return 0;
}
