void task_h(void) {
    __asm__ volatile(".fill 1095652, 1, 0x00\n");
}
void task_m(void) {
    __asm__ volatile(".fill 730435, 1, 0x00\n");
}
void task_l(void) {
    __asm__ volatile(".fill 2921739, 1, 0x00\n");
}
int main(void) {
    task_h();
    task_m();
    task_l();
    while (1);
    return 0;
}
