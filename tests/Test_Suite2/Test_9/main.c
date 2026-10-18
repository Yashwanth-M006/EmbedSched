void task_a(void) {
    __asm__ volatile(".fill 21739, 1, 0x00\n");
}

void task_b(void) {
    __asm__ volatile(".fill 21739, 1, 0x00\n");
}

void task_c(void) {
    __asm__ volatile(".fill 21739, 1, 0x00\n");
}

void task_d(void) {
    __asm__ volatile(".fill 21739, 1, 0x00\n");
}

void task_e(void) {
    __asm__ volatile(".fill 21739, 1, 0x00\n");
}

int main(void) {
    task_a();
    task_b();
    task_c();
    task_d();
    task_e();
    while (1);
    return 0;
}
