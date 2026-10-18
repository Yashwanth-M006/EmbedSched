void vision_processing(void) {
    __asm__ volatile(".fill 10434782, 1, 0x00\n");
}
void object_detection(void) {
    __asm__ volatile(".fill 20869565, 1, 0x00\n");
}
void can_publish(void) {
    __asm__ volatile(".fill 2608695, 1, 0x00\n");
}
void safety_monitor(void) {
    __asm__ volatile(".fill 1043478, 1, 0x00\n");
}
int main(void) {
    vision_processing();
    object_detection();
    can_publish();
    safety_monitor();
    while(1);
    return 0;
}
