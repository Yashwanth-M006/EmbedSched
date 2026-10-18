void task1(void) {
    __asm__ volatile(".fill 365214, 1, 0x00\n");
}

void task2(void) {
    __asm__ volatile(".fill 730430, 1, 0x00\n");
}

void task3(void) {
    __asm__ volatile(".fill 730430, 1, 0x00\n");
}

int main(void) {
    task1();
    task2();
    task3();
    while (1);
    return 0;
}
