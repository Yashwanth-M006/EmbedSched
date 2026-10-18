/*
 * Test Case 10: Cross-Core Deadlock Risk
 *
 * Two tasks on different cores. They both use mutex_A and mutex_B, but
 * in opposite acquisition order — a classic AB/BA deadlock pattern.
 *
 *   Core 0 — Task_Core0_Alpha: acquires mutex_A first, then mutex_B
 *   Core 1 — Task_Core1_Beta:  acquires mutex_B first, then mutex_A
 *
 * The tool must detect this purely from schedule.json's resource graph.
 * No firmware instrumentation required — this is a [STATIC] analysis.
 */

/* Stub mutex primitives (no real OS here) */
typedef volatile int mutex_t;
static mutex_t mutex_A = 0;
static mutex_t mutex_B = 0;

static void lock(mutex_t *m)   { while (*m) {} *m = 1; }
static void unlock(mutex_t *m) { *m = 0; }

void task_core0_alpha(void) {
    /* Core 0: acquires mutex_A first, then mutex_B (order: A → B) */
    lock(&mutex_A);
    /* ... critical work on shared resource A ... */
    lock(&mutex_B);
    /* ... critical work on shared resource B ... */
    unlock(&mutex_B);
    unlock(&mutex_A);
}

void task_core1_beta(void) {
    /* Core 1: acquires mutex_B first, then mutex_A (order: B → A)  ← INVERSION */
    lock(&mutex_B);
    /* ... critical work on shared resource B ... */
    lock(&mutex_A);
    /* ... critical work on shared resource A ... */
    unlock(&mutex_A);
    unlock(&mutex_B);
}

int main(void) {
    task_core0_alpha();
    task_core1_beta();
    while (1);
    return 0;
}
