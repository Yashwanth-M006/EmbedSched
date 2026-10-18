void task1(void) {
    __asm__ volatile(".fill 730424, 1, 0x00\n");
}

void task2(void) {
    __asm__ volatile(".fill 1095642, 1, 0x00\n");
}

void task3(void) {
    __asm__ volatile(".fill 1460858, 1, 0x00\n");
}

int main(void) {
    task1();
    task2();
    task3();
    while (1);
    return 0;
}
