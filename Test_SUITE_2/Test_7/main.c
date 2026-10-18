void motor_control_loop(void) {
    volatile char buf[1800];
    buf[0] = 0;
    __asm__ volatile(".fill 29218, 1, 0x00\n");
}

void sensor_aggregate(void) {
    volatile char buf[1400];
    buf[0] = 0;
    __asm__ volatile(".fill 14608, 1, 0x00\n");
}

void can_transmit_handler(void) {
    volatile char buf[900];
    buf[0] = 0;
    __asm__ volatile(".fill 7304, 1, 0x00\n");
}

int main(void) {
    motor_control_loop();
    sensor_aggregate();
    can_transmit_handler();
    while (1);
    return 0;
}
