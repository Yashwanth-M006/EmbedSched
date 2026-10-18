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

void adc_dma_isr(void) {
    __asm__ volatile(".fill 100, 1, 0x00\n");
}
