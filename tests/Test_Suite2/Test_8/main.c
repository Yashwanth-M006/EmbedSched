void task_a(void) {
    __asm__ volatile(".fill 1095652, 1, 0x00\n");
}

void task_b(void) {
    __asm__ volatile(".fill 1826086, 1, 0x00\n");
}

void task_c(void) {
    __asm__ volatile(".fill 2921739, 1, 0x00\n");
}

int main(void) {
    task_a();
    task_b();
    task_c();
    while (1);
    return 0;
}
