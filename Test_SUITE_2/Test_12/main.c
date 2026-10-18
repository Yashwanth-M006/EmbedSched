/*
 * Test Case 12: Firmware vs Schedule Mismatch — Entry Function Not Found
 *
 * Purpose:
 *   User typos or renames a function.
 *   The schedule.json defines:
 *     "Task_MotorControl" with "entry_function": "motor_controll_loop" (typo — double 'l')
 *   The firmware C code defines:
 *     "motor_control_loop" (correct spelling)
 *
 * Expected behavior:
 *   - Error: "Task_MotorControl: entry function 'motor_controll_loop' not found in firmware symbols"
 *   - Tool suggests closest match by edit distance: "Did you mean 'motor_control_loop'? (Levenshtein distance: 1)"
 *   - Task_MotorControl is excluded from schedulability analysis
 *   - Remaining tasks (Task_SensorAgg, Task_CANTransmit) are still analyzed (partial report)
 *   - Exit code non-zero so CI pipelines catch it
 */

void motor_control_loop(void) {
    __asm__ volatile(".fill 29218, 1, 0x00\n");
}

void sensor_aggregate(void) {
    __asm__ volatile(".fill 14608, 1, 0x00\n");
}

void can_transmit_handler(void) {
    __asm__ volatile(".fill 7304, 1, 0x00\n");
}

int main(void) {
    motor_control_loop();
    sensor_aggregate();
    can_transmit_handler();
    while (1);
    return 0;
}
