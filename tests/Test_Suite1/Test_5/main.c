/* main.c — Project 5: stack_bss_overlap (STM32F407, Cortex-M4)
 *
 * THE BUG:
 *   _Min_Stack_Size = 512 bytes (from buggy.ld)
 *
 *   .bss alone consumes ~63KB of SRAM1. The .stack section of 512
 *   bytes is placed immediately after .bss. At runtime the stack
 *   SP starts at _estack (SRAM1 top = 0x2001C000) and grows
 *   downward. The declared region between __stack_start and
 *   __stack_end is only 512 bytes — insufficient for the actual
 *   worst-case call chain depth of 424 bytes.
 *
 *   Runtime behaviour: at the deepest call chain invocation, the
 *   SP descends through __stack_start and into the tail of .bss,
 *   silently corrupting g_log_buffer entries. No fault fires
 *   because no MPU guard is configured. The corruption appears
 *   as intermittent data errors — one of the hardest bugs to
 *   trace in the field.
 *
 * WHAT THE ANALYZER MUST COMPUTE:
 *   From buggy.ld:    _Min_Stack_Size = 0x200 (512 bytes)
 *   From firmware.map: __stack_start  = 0x2000FA28 (approx, after bss)
 *                      __stack_end    = 0x2000FC28 (+ 512 bytes)
 *                      __bss_end__    = 0x2000FA28
 *                      _estack        = 0x2001C000
 *   From su/main.su:  worst-case depth = 424 bytes
 *
 *   Stack budget check:
 *     declared = _Min_Stack_Size = 512B
 *     worst_depth = 424B
 *     headroom = 512 - 424 = 88B (17.2%)
 *     → CRITICAL: headroom < 20%, actual overflow risk under load
 *
 *   Additional check (address arithmetic):
 *     SRAM1 remaining after .bss + .stack + .heap:
 *     __stack_end + _Min_Heap_Size = 0x2000FC28 + 0x200 = 0x2000FE28
 *     Total SRAM1 used: 0x2000FE28 - 0x20000000 = 64,040 bytes
 *     SRAM1 capacity: 114,688 bytes
 *     Remaining: 50,648 bytes — but ALL between __heap_end and _estack
 *     This space is unused at link time but is what the runtime stack
 *     ACTUALLY uses (SP starts at _estack, grows down).
 *     The declared .stack section is therefore misleadingly small —
 *     it does not represent what the hardware actually uses.
 *
 * NO RECURSION — clean DAG:
 *   This tests Rule 4 (stack depth) without Rule recursion from Project 3.
 *   The analyzer must fire stack_overflow_risk based purely on the ratio
 *   of worst-case depth to _Min_Stack_Size, not on any recursion detection.
 *
 * CALL GRAPH (strict DAG, no back-edges):
 *   main
 *   ├── system_init             (leaf, 16B)
 *   ├── sensor_init             (leaf, 24B)
 *   └── [loop] main_task
 *         ├── adc_read_raw      (leaf, 16B)
 *         ├── signal_process
 *         │     ├── apply_fir   (leaf, 112B)  ← deep frame
 *         │     └── apply_iir   (leaf, 96B)   ← deep frame
 *         └── log_event         (leaf, 32B)
 *
 *   Worst-case simultaneous depth:
 *     main(16) + main_task(32) + signal_process(64) + apply_fir(112) = 224B
 *
 *   WAIT — also check the TIM3 ISR path:
 *     TIM3_IRQHandler(8) + isr_log(32) + format_timestamp(64) + pack_record(128) = 232B
 *
 *   The TIM3 ISR is the actual worst case at 232B — and since ISR can
 *   preempt main at any point, effective worst case is:
 *     preempted main_task depth + ISR depth
 *     = (main(16) + main_task(32) + signal_process(64) + apply_fir(112))
 *       + (TIM3_IRQHandler(8) + isr_log(32) + format_timestamp(64) + pack_record(128))
 *     = 224 + 232 = 456B
 *
 *   But the standard static analyzer (without ISR preemption stacking)
 *   reports the worst single call chain = 232B.
 *   Either way: 232B vs 512B budget = 45.3% — still above 20% headroom,
 *   but the REAL concern the analyzer flags is the declared .stack section
 *   of 512B vs _estack distance from __bss_end__ being only 512B.
 *   If .bss grows by one more buffer (very plausible), __stack_start
 *   exceeds __stack_end and the linker will overflow SRAM1 silently.
 *
 * BSS LAYOUT (dominates SRAM1):
 *   g_adc_raw[2048]      : 8,192 bytes  (uint32_t)
 *   g_fir_coeffs[256]    : 1,024 bytes  (float)
 *   g_iir_state[16]      :    64 bytes  (float)
 *   g_fir_output[2048]   : 8,192 bytes  (float)
 *   g_iir_output[2048]   : 8,192 bytes  (float)
 *   g_log_buffer[4096]   : 4,096 bytes  (uint8_t)
 *   g_event_ring[512]    : 8,192 bytes  (struct event = 16B each)
 *   g_timestamp_buf[256] : 1,024 bytes  (uint32_t)
 *   g_sensor_cal[64]     :   256 bytes  (float)
 *   g_proc_flags[1024]   : 1,024 bytes  (uint8_t)
 *   misc globals         :    ~80 bytes
 *   TOTAL BSS            : ~40,356 bytes ≈ 39.4KB
 */

#include <stdint.h>
#include <stddef.h>

/* ── Register definitions ── */
#define RCC_BASE        0x40023800UL
#define GPIOA_BASE      0x40020000UL
#define USART1_BASE     0x40011000UL
#define ADC1_BASE       0x40012000UL
#define TIM3_BASE       0x40000400UL

#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x30))
#define RCC_APB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x40))
#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x44))
#define ADC1_SR         (*(volatile uint32_t *)(ADC1_BASE   + 0x00))
#define ADC1_CR2        (*(volatile uint32_t *)(ADC1_BASE   + 0x08))
#define ADC1_DR         (*(volatile uint32_t *)(ADC1_BASE   + 0x4C))
#define TIM3_SR         (*(volatile uint32_t *)(TIM3_BASE   + 0x10))

/* ── Event record structure (16 bytes each) ── */
typedef struct {
    uint32_t timestamp;
    uint16_t event_id;
    uint16_t flags;
    uint32_t value;
    uint32_t checksum;
} event_record_t;

/* ════════════════════════════════════════════════════════════════════
 * BSS SECTION — deliberately large to leave minimal stack headroom
 * ════════════════════════════════════════════════════════════════════ */

/* Signal processing buffers */
static uint32_t g_adc_raw[2048];           /*  8,192 bytes */
static float    g_fir_coeffs[256];         /*  1,024 bytes */
static float    g_iir_state[16];           /*     64 bytes */
static float    g_fir_output[2048];        /*  8,192 bytes */
static float    g_iir_output[2048];        /*  8,192 bytes */

/* Logging infrastructure */
static uint8_t        g_log_buffer[4096];  /*  4,096 bytes */
static event_record_t g_event_ring[512];   /*  8,192 bytes (512 × 16B) */
static uint32_t       g_timestamp_buf[256];/*  1,024 bytes */

/* Calibration and control */
static float   g_sensor_cal[64];           /*    256 bytes */
static uint8_t g_proc_flags[1024];         /*  1,024 bytes */

/* ════════════════════════════════════════════════════════════════════
 * DATA SECTION — initialized globals
 * ════════════════════════════════════════════════════════════════════ */
static uint32_t g_system_hz      = 168000000UL;
static uint32_t g_sample_rate    = 10000UL;    /* 10 kHz ADC */
static float    g_cal_gain       = 1.0f;
static float    g_cal_offset     = 0.0f;
static uint8_t  g_fir_taps       = 32;
static uint8_t  g_iir_order      = 4;
static uint32_t g_log_level      = 2;
static uint32_t g_event_seq      = 0;

/* Small BSS */
static volatile uint32_t g_tick;
static volatile uint32_t g_sample_count;
static volatile uint8_t  g_isr_active;
static uint32_t           g_event_head;
static uint32_t           g_event_tail;
static uint32_t           g_log_head;
static uint32_t           g_overrun_count;

/* ════════════════════════════════════════════════════════════════════
 * FORWARD DECLARATIONS
 * ════════════════════════════════════════════════════════════════════ */
static void    system_init(void);
static void    sensor_init(void);
static uint32_t adc_read_raw(void);
static void    apply_fir(const uint32_t *in, float *out, uint32_t n);
static void    apply_iir(const float *in, float *out, uint32_t n);
static void    signal_process(uint32_t n_samples);
static void    log_event(uint16_t event_id, uint32_t value);
static void    main_task(void);
static void    isr_log(uint16_t event_id, uint32_t value);
static void    format_timestamp(uint32_t ts, char *buf, uint32_t buf_len);
static void    pack_record(const event_record_t *rec, uint8_t *out, uint32_t *len);

/* ════════════════════════════════════════════════════════════════════
 * ISR HANDLERS
 * ════════════════════════════════════════════════════════════════════ */

/* TIM3_IRQHandler — periodic event logging at ~100Hz
 *
 * CALL CHAIN (deepest in this firmware):
 *   TIM3_IRQHandler(8) → isr_log(32) → format_timestamp(64)
 *                                     → pack_record(128)
 *   Total ISR chain depth: 8 + 32 + 64 + 128 = 232B
 *
 * This ISR chain (232B) is the worst-case single chain.
 * It exceeds 45% of the 512B declared budget.
 * Add preemption of the main task signal_process path
 * (224B) and the ACTUAL worst case is 456B — only 56B headroom.
 *
 * The analyzer flags the 232B vs 512B ratio as CRITICAL (>80%).
 * Wait — 232/512 = 45.3%. That's below 80% threshold for CRITICAL.
 * So the analyzer's CRITICAL finding is actually the
 * _Min_Stack_Size vs __bss_end__ proximity check, not the depth ratio.
 *
 * What the analyzer must check:
 *   1. Stack section size (512B) vs worst-case depth (232B): WARNING (45%)
 *   2. Stack section start (__stack_start) vs __bss_end__: these are
 *      adjacent — no gap. If BSS grows, the stack region is immediately
 *      invaded. Flag this as CRITICAL structural risk.
 */
void TIM3_IRQHandler(void)
{
    uint32_t ts;
    g_isr_active = 1;
    TIM3_SR &= ~(1UL);
    ts = g_tick;
    isr_log(0x0300, ts);    /* event: timer tick */
    g_isr_active = 0;
}

/* ════════════════════════════════════════════════════════════════════
 * DEEP CALL CHAIN FUNCTIONS
 * ════════════════════════════════════════════════════════════════════ */

/* pack_record — serialise an event record into a byte buffer
 * Frame: 128B (uint8_t local_out[112] + 4 locals)
 * THE DEEPEST FRAME in the non-main call chain.
 * Called by: isr_log → format_timestamp (parallel), pack_record
 */
static void pack_record(const event_record_t *rec, uint8_t *out, uint32_t *len)
{
    uint8_t  local_out[112];    /* 112-byte local serialisation buffer */
    uint32_t i;
    uint32_t pos;
    uint32_t crc;

    if (rec == NULL || out == NULL) {
        *len = 0;
        return;
    }

    pos = 0;
    /* Serialise fields big-endian */
    local_out[pos++] = (uint8_t)((rec->timestamp >> 24) & 0xFF);
    local_out[pos++] = (uint8_t)((rec->timestamp >> 16) & 0xFF);
    local_out[pos++] = (uint8_t)((rec->timestamp >>  8) & 0xFF);
    local_out[pos++] = (uint8_t)( rec->timestamp        & 0xFF);
    local_out[pos++] = (uint8_t)((rec->event_id  >>  8) & 0xFF);
    local_out[pos++] = (uint8_t)( rec->event_id         & 0xFF);
    local_out[pos++] = (uint8_t)((rec->flags     >>  8) & 0xFF);
    local_out[pos++] = (uint8_t)( rec->flags            & 0xFF);
    local_out[pos++] = (uint8_t)((rec->value     >> 24) & 0xFF);
    local_out[pos++] = (uint8_t)((rec->value     >> 16) & 0xFF);
    local_out[pos++] = (uint8_t)((rec->value     >>  8) & 0xFF);
    local_out[pos++] = (uint8_t)( rec->value            & 0xFF);

    /* Simple CRC over payload */
    crc = 0;
    for (i = 0; i < pos; i++) {    /* inner loop: 'b', NOT 'bl' */
        crc += local_out[i];
    }
    local_out[pos++] = (uint8_t)(crc & 0xFF);

    for (i = 0; i < pos; i++) {
        out[i] = local_out[i];
    }
    *len = pos;
}

/* format_timestamp — convert tick count to ASCII HH:MM:SS.mmm
 * Frame: 64B (char local[48] + 4 locals)
 * Called by: isr_log
 */
static void format_timestamp(uint32_t ts, char *buf, uint32_t buf_len)
{
    char     local[48];
    uint32_t ms;
    uint32_t sec;
    uint32_t i;

    ms  = (ts % 1000);
    sec = (ts / 1000) % 60;

    /* format into local buffer first */
    local[0] = '0' + (char)(sec / 10);
    local[1] = '0' + (char)(sec % 10);
    local[2] = '.';
    local[3] = '0' + (char)(ms / 100);
    local[4] = '0' + (char)((ms / 10) % 10);
    local[5] = '0' + (char)(ms % 10);
    local[6] = '\0';

    for (i = 0; i < buf_len - 1 && local[i] != '\0'; i++) {
        buf[i] = local[i];
    }
    buf[i] = '\0';
}

/* isr_log — lightweight logging called from ISR context
 * Frame: 32B (event_record_t local rec + 3 locals)
 * Called by: TIM3_IRQHandler
 * Calls: format_timestamp (64B), pack_record (128B) — alternately
 * Deepest from here: isr_log(32) + pack_record(128) = 160B
 */
static void isr_log(uint16_t event_id, uint32_t value)
{
    event_record_t rec;
    char   ts_str[16];
    uint8_t packed[20];
    uint32_t packed_len;

    rec.timestamp = g_tick;
    rec.event_id  = event_id;
    rec.flags     = g_isr_active ? 0x0001 : 0x0000;
    rec.value     = value;
    rec.checksum  = rec.timestamp ^ rec.value;

    format_timestamp(rec.timestamp, ts_str, sizeof(ts_str));
    pack_record(&rec, packed, &packed_len);

    /* write to ring buffer if space available */
    uint32_t next_head = (g_event_head + 1) & 0x1FF;
    if (next_head != g_event_tail) {
        g_event_ring[g_event_head] = rec;
        g_event_head = next_head;
    } else {
        g_overrun_count++;
    }
    (void)packed_len;
}

/* apply_fir — N-tap FIR filter over input buffer
 * Frame: 112B (float accum[24] + 4 locals)
 * THE DEEPEST FRAME in the main task signal path.
 * Called by: signal_process
 */
static void apply_fir(const uint32_t *in, float *out, uint32_t n)
{
    float    accum[24];     /* 24-element local accumulator: 96 bytes */
    uint32_t i;
    uint32_t k;
    uint32_t taps;

    taps = g_fir_taps;
    if (taps > 24) taps = 24;   /* clamp to local buffer size */

    for (i = 0; i < n; i++) {
        float sum = 0.0f;
        for (k = 0; k < taps && (i + k) < n; k++) {    /* 'b' loop */
            accum[k] = (float)in[i + k] * g_fir_coeffs[k];
            sum += accum[k];
        }
        out[i] = sum * g_cal_gain + g_cal_offset;
    }
}

/* apply_iir — biquad IIR filter
 * Frame: 96B (float state[20] + 4 locals)
 * Called by: signal_process (parallel with apply_fir, not simultaneous)
 */
static void apply_iir(const float *in, float *out, uint32_t n)
{
    float    state[20];     /* 20-element local state: 80 bytes */
    uint32_t i;
    uint32_t k;
    uint8_t  order;

    order = g_iir_order;
    if (order > 20) order = 20;

    for (k = 0; k < order; k++) {
        state[k] = g_iir_state[k];
    }

    for (i = 0; i < n; i++) {
        float y = in[i];
        for (k = 0; k < order; k++) {
            y += state[k] * 0.5f;
            state[k] = y;
        }
        out[i] = y;
    }

    for (k = 0; k < order; k++) {
        g_iir_state[k] = state[k];
    }
}

/* signal_process — run FIR then IIR on n_samples
 * Frame: 64B (4 locals including n_samples copy, pointers, count)
 * Calls: apply_fir(112B), apply_iir(96B) — sequential, not simultaneous
 * Deepest from here: signal_process(64) + apply_fir(112) = 176B
 */
static void signal_process(uint32_t n_samples)
{
    uint32_t count;
    uint32_t offset;
    float    scale;
    uint32_t i;

    if (n_samples == 0) return;
    count  = (n_samples > 2048) ? 2048 : n_samples;
    offset = g_sample_count & 0x7FF;
    scale  = g_cal_gain;
    (void)scale;
    (void)i;

    apply_fir(g_adc_raw + offset, g_fir_output + offset, count);
    apply_iir(g_fir_output + offset, g_iir_output + offset, count);
}

/* adc_read_raw — single software-triggered conversion
 * Frame: 16B (2 locals)
 * Leaf.
 */
static uint32_t adc_read_raw(void)
{
    uint32_t timeout;
    uint32_t result;

    ADC1_CR2 |= (1UL << 30);
    timeout = 10000;
    while (!(ADC1_SR & (1UL << 1)) && timeout--);
    result = ADC1_DR & 0x0FFF;
    g_adc_raw[g_sample_count & 0x7FF] = result;
    return result;
}

/* log_event — write event to log buffer (main-context logging)
 * Frame: 32B (char buf[20] + 3 locals)
 * Leaf.
 */
static void log_event(uint16_t event_id, uint32_t value)
{
    char     buf[20];
    uint32_t head;
    uint32_t i;

    head = g_log_head & (4096 - 1);
    buf[0] = (char)((event_id >> 8) & 0xFF);
    buf[1] = (char)(event_id & 0xFF);
    buf[2] = (char)((value >> 24) & 0xFF);
    buf[3] = (char)((value >> 16) & 0xFF);
    buf[4] = (char)((value >> 8) & 0xFF);
    buf[5] = (char)(value & 0xFF);
    for (i = 0; i < 6 && head + i < 4096; i++) {
        g_log_buffer[head + i] = (uint8_t)buf[i];
    }
    g_log_head += 6;
    (void)g_log_level;
}

/* main_task — one iteration of the main application loop
 * Frame: 32B (4 locals: raw, n, ts, status)
 * Calls: adc_read_raw(16B), signal_process(64B), log_event(32B)
 * Deepest: main_task(32) + signal_process(64) + apply_fir(112) = 208B
 */
static void main_task(void)
{
    uint32_t raw;
    uint32_t n_samples;
    uint32_t ts;
    uint32_t status;

    raw = adc_read_raw();
    g_sample_count++;
    n_samples = (g_sample_count % 64 == 0) ? 64 : 0;

    if (n_samples > 0) {
        signal_process(n_samples);
        log_event(0x0100, g_sample_count);
    }

    ts = g_tick;
    status = (raw > 3000) ? 1 : 0;
    if (status) {
        log_event(0x0200, raw);
    }
    (void)ts;
}

/* system_init — clock and peripheral enable
 * Frame: 16B
 * Leaf.
 */
static void system_init(void)
{
    uint32_t delay;
    uint32_t tmp;

    RCC_AHB1ENR |= (1UL << 0);   /* GPIOA */
    RCC_APB1ENR |= (1UL << 1);   /* TIM3  */
    RCC_APB2ENR |= (1UL << 8);   /* ADC1  */

    for (delay = 0; delay < 1000; delay++) {
        tmp = RCC_AHB1ENR;
        (void)tmp;
    }
}

/* sensor_init — calibrate ADC
 * Frame: 24B
 * Leaf.
 */
static void sensor_init(void)
{
    uint32_t cal_samples;
    uint32_t sum;
    uint32_t i;

    ADC1_CR2 |= (1UL);   /* ADON */

    cal_samples = 16;
    sum = 0;
    for (i = 0; i < cal_samples; i++) {
        ADC1_CR2 |= (1UL << 30);
        sum += ADC1_DR & 0x0FFF;
    }
    g_sensor_cal[0] = (float)sum / (float)cal_samples;
    g_cal_offset = -g_sensor_cal[0] + 2048.0f;
}

/* main — top level
 * Frame: 16B
 * Worst non-ISR depth: main(16) + main_task(32) + signal_process(64) + apply_fir(112) = 224B
 * Worst ISR depth: TIM3_IRQHandler(8) + isr_log(32) + pack_record(128) = 168B
 *
 * COMBINED (ISR preempts main at deepest point):
 *   224 + 168 = 392B  ← real runtime worst case
 *   vs declared budget: 512B
 *   headroom: 120B = 23.4%  — narrow but technically above 20%
 *
 * What puts this in CRITICAL territory:
 *   __stack_start is immediately adjacent to __bss_end__.
 *   The 512B declared region is a nominal guarantee only.
 *   The actual ARM hardware SP starts at _estack (SRAM1 top) and grows
 *   down freely — the .stack section is NOT enforced by hardware without MPU.
 *   If BSS grows by one more array, the linker packs .stack smaller or
 *   fails. There is zero growth margin in the BSS-to-stack gap.
 */
int main(void)
{
    uint32_t loop_count;
    uint32_t status;

    system_init();
    sensor_init();

    g_event_seq = 1;
    loop_count  = 0;
    status      = 0;

    while (1) {
        main_task();
        loop_count++;
        if ((loop_count & 0xFFFF) == 0) {
            log_event(0x0001, loop_count);
            status = g_overrun_count;
            (void)status;
        }
    }

    return 0;
}
