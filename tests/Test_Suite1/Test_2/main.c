/* main.c — Project 1: golden_baseline
 *
 * This firmware is deliberately correct in every way the analyzer checks.
 * It exercises all five rules and must pass each one cleanly.
 *
 * RULE CHECKLIST:
 *   Rule 1 — ISR placement        : ISRs are in flash (unavoidable on F407,
 *                                    no ITCM). Analyzer must emit INFO about
 *                                    ART accelerator, NOT a warning.
 *   Rule 2 — DMA bus contention   : DMA buffers in .dma_buffers section
 *                                    (SRAM1), stack in CCM. No false flag.
 *   Rule 3 — ITCM overflow        : N/A (F407 has no ITCM). No false flag.
 *   Rule 4 — Stack overflow risk  : Worst-case depth = 96B vs 2048B budget.
 *                                    Usage = 4.7%. Must NOT flag this.
 *   Rule 5 — DMA alignment        : Buffers have __attribute__((aligned(32))).
 *                                    Must NOT fire misalignment warning.
 *
 * STACK DEPTH ANALYSIS (matches golden.ld _Min_Stack_Size = 0x800 = 2048B):
 *   main            : 16B
 *     system_init   : 16B  (leaf after clock setup)
 *     uart_init     : 24B  (leaf)
 *     main_loop     : 24B
 *       sensor_read : 32B
 *         adc_sample: 16B  (leaf)
 *       process_frame:48B
 *         crc_compute:16B  (leaf)
 *         uart_tx_byte:8B  (leaf)
 *
 *   Worst-case simultaneous depth:
 *     main(16) + main_loop(24) + process_frame(48) + crc_compute(16) = 104B
 *   Budget: 2048B. Usage: 5.1%. Far below 80% warning threshold.
 *
 * NO RECURSION anywhere in this file — call graph is a strict DAG.
 *
 * MEMORY LAYOUT:
 *   .data   : ~40 bytes  (initialized globals in SRAM1)
 *   .bss    : ~16 bytes  (zero-init globals in SRAM1)
 *   .dma_buffers : 512 bytes (rx_dma_buf + tx_dma_buf, 32B aligned)
 *   .stack  : 2048 bytes (in CCM, explicitly sized)
 */

#include <stdint.h>

/* ── Register definitions (STM32F407, bare metal) ── */
#define RCC_BASE        0x40023800UL
#define GPIOA_BASE      0x40020000UL
#define ADC1_BASE       0x40012000UL
#define USART1_BASE     0x40011000UL
#define DMA2_BASE       0x40026400UL

#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x30))
#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x44))
#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00))
#define GPIOA_AFRL      (*(volatile uint32_t *)(GPIOA_BASE + 0x20))
#define USART1_SR       (*(volatile uint32_t *)(USART1_BASE + 0x00))
#define USART1_DR       (*(volatile uint32_t *)(USART1_BASE + 0x04))
#define USART1_BRR      (*(volatile uint32_t *)(USART1_BASE + 0x08))
#define USART1_CR1      (*(volatile uint32_t *)(USART1_BASE + 0x0C))
#define ADC1_SR         (*(volatile uint32_t *)(ADC1_BASE   + 0x00))
#define ADC1_CR2        (*(volatile uint32_t *)(ADC1_BASE   + 0x08))
#define ADC1_DR         (*(volatile uint32_t *)(ADC1_BASE   + 0x4C))

/* ── DMA buffer section placement macro ──
 * __attribute__((section(".dma_buffers"))) places the variable in the
 * dedicated .dma_buffers linker section (SRAM1, 32B aligned per golden.ld).
 * __attribute__((aligned(32))) ensures 32-byte cache-line alignment.
 *
 * CORRECT PATTERN: both attributes required.
 *   - section ensures the linker places it in the right region
 *   - aligned ensures the address is cache-line aligned within that region
 */
#define DMA_BUF __attribute__((section(".dma_buffers"), aligned(32)))

/* ── DMA buffers: in .dma_buffers section, SRAM1 ── */
#define RX_DMA_BUF_SIZE  256
#define TX_DMA_BUF_SIZE  256

static uint8_t DMA_BUF g_rx_dma_buf[RX_DMA_BUF_SIZE];
static uint8_t DMA_BUF g_tx_dma_buf[TX_DMA_BUF_SIZE];

/* ── .data: initialized globals ── */
static uint32_t g_system_clock  = 16000000UL;
static uint32_t g_uart_baud     = 115200UL;
static uint8_t  g_node_addr     = 0x01;
static uint8_t  g_initialized   = 0;
static uint32_t g_frame_count   = 0;
static uint32_t g_error_count   = 0;
static uint32_t g_adc_threshold = 2048;  /* mid-scale 12-bit ADC */

/* ── .bss: zero-initialized globals ── */
static volatile uint32_t g_tick;
static volatile uint8_t  g_dma_complete;
static uint16_t           g_last_adc;
static uint8_t            g_tx_busy;

/* ── Forward declarations ── */
static void    system_init(void);
static void    uart_init(uint32_t baud);
static void    uart_tx_byte(uint8_t byte);
static uint16_t adc_sample(void);
static uint32_t crc_compute(const uint8_t *data, uint32_t len);
static void    sensor_read(uint8_t *out_buf, uint32_t *out_len);
static void    process_frame(const uint8_t *frame, uint32_t len);
static void    main_loop(void);

/* ─────────────────────────────────────────────────────────────────────
 * ISR HANDLERS
 *
 * On STM32F407 (Cortex-M4), there is no ITCM. All ISR handlers execute
 * from Flash via the AHB bus. The ART accelerator (8x128-bit prefetch
 * buffer) reduces effective latency for sequential accesses but cannot
 * eliminate cold-entry jitter on random vector dispatch.
 *
 * CORRECT BEHAVIOR OF ANALYZER:
 *   - Must NOT fire "ISR in SRAM (suspicious)" — they are in Flash, correct.
 *   - Must NOT fire "move ISR to ITCM" — no ITCM on F407.
 *   - Should emit INFO: "ISRs in Flash — verify ART accelerator enabled."
 *
 * ISR design is also correct:
 *   - No blocking calls (no HAL_Delay, no busy-wait loops)
 *   - No heap allocation
 *   - Minimal frame size (set flag + return)
 * ──────────────────────────────────────────────────────────────────── */

/* DMA2 Stream 0 — ADC1 DMA complete (Rule 2 test: correct DMA ISR) */
void DMA2_Stream0_IRQHandler(void)
{
    /* Clear transfer-complete flag (bit 5 of LISR) */
    *(volatile uint32_t *)(DMA2_BASE + 0x08) = (1UL << 5);
    g_dma_complete = 1;
}

/* TIM2 — periodic 1ms tick (clean ISR, no blocking) */
void TIM2_IRQHandler(void)
{
    /* Clear update interrupt flag */
    *(volatile uint32_t *)(0x40000000UL + 0x10) &= ~(1UL);
    g_tick++;
}

/* USART1 — TX complete flag (used by uart_tx_byte) */
void USART1_IRQHandler(void)
{
    uint32_t sr = USART1_SR;
    if (sr & (1UL << 6)) {   /* TC: transmission complete */
        g_tx_busy = 0;
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * IMPLEMENTATION
 * ──────────────────────────────────────────────────────────────────── */

/* system_init — enable GPIO, USART1, ADC1 clocks
 * Frame: 16B (2 locals + alignment pad)
 * No callees.
 */
static void system_init(void)
{
    uint32_t tmp;
    uint32_t delay;

    RCC_AHB1ENR |= (1UL << 0);   /* GPIOA */
    RCC_APB2ENR |= (1UL << 4);   /* USART1 */
    RCC_APB2ENR |= (1UL << 8);   /* ADC1 */
    RCC_APB2ENR |= (1UL << 14);  /* DMA2 — not a real register, illustrative */

    for (delay = 0; delay < 500; delay++) {
        tmp = RCC_AHB1ENR;
        (void)tmp;
    }

    g_initialized = 1;
}

/* uart_init — configure USART1 on PA9/PA10
 * Frame: 24B (3 locals)
 * No callees.
 */
static void uart_init(uint32_t baud)
{
    uint32_t mantissa;
    uint32_t fraction;
    uint32_t brr;

    GPIOA_MODER &= ~((3UL << 18) | (3UL << 20));
    GPIOA_MODER |=  ((2UL << 18) | (2UL << 20));
    GPIOA_AFRL  &= ~((0xFUL << 4) | (0xFUL << 8));
    GPIOA_AFRL  |=  ((7UL << 4) | (7UL << 8));

    mantissa  = g_system_clock / baud;
    fraction  = ((g_system_clock % baud) * 16) / baud;
    brr       = (mantissa << 4) | (fraction & 0xF);
    USART1_BRR = brr;
    USART1_CR1 = (1UL << 3) | (1UL << 2) | (1UL << 13);

    g_uart_baud = baud;
}

/* uart_tx_byte — blocking byte transmit (only called outside ISR)
 * Frame: 8B (1 local)
 * No callees.
 */
static void uart_tx_byte(uint8_t byte)
{
    uint32_t timeout = 10000;
    while (!(USART1_SR & (1UL << 7)) && timeout--);
    USART1_DR = byte;
}

/* adc_sample — single software-triggered ADC conversion
 * Frame: 16B (2 locals)
 * No callees.
 */
static uint16_t adc_sample(void)
{
    uint32_t timeout;
    uint16_t result;

    ADC1_CR2 |= (1UL << 30);   /* SWSTART */
    timeout = 10000;
    while (!(ADC1_SR & (1UL << 1)) && timeout--);  /* wait EOC */
    result = (uint16_t)(ADC1_DR & 0x0FFF);
    g_last_adc = result;
    return result;
}

/* crc_compute — software CRC-8 over a buffer
 * Frame: 16B (3 locals: i, crc, byte)
 * No callees. Strict DAG — does NOT call itself.
 *
 * NOTE: This is NOT recursive. It is a plain loop.
 * Your call graph builder must correctly identify this as a leaf
 * and must NOT falsely detect recursion here.
 */
static uint32_t crc_compute(const uint8_t *data, uint32_t len)
{
    uint32_t crc = 0xFFFFFFFFUL;
    uint32_t i;
    uint8_t  byte;

    for (i = 0; i < len; i++) {
        byte = data[i];
        crc ^= ((uint32_t)byte << 24);
        /* 8 rounds — NOT recursion, just a loop */
        uint32_t j;
        for (j = 0; j < 8; j++) {
            if (crc & 0x80000000UL) {
                crc = (crc << 1) ^ 0x04C11DB7UL;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc ^ 0xFFFFFFFFUL;
}

/* sensor_read — read ADC, packetize into output buffer
 * Frame: 32B (local frame[16] + 3 locals)
 * Callees: adc_sample (leaf, 16B)
 * Max depth from here: 32 + 16 = 48B
 */
static void sensor_read(uint8_t *out_buf, uint32_t *out_len)
{
    uint8_t  frame[16];
    uint16_t raw;
    uint32_t scaled;
    uint32_t idx;

    raw    = adc_sample();
    scaled = ((uint32_t)raw * 3300) / 4095;   /* mV */

    idx = 0;
    frame[idx++] = 0x02;                       /* STX */
    frame[idx++] = g_node_addr;
    frame[idx++] = 0x01;                       /* cmd: sensor data */
    frame[idx++] = (uint8_t)((scaled >> 8) & 0xFF);
    frame[idx++] = (uint8_t)(scaled & 0xFF);
    frame[idx++] = 0x03;                       /* ETX */

    for (uint32_t i = 0; i < idx; i++) {
        out_buf[i] = frame[i];
    }
    *out_len = idx;
}

/* process_frame — validate CRC, dispatch command
 * Frame: 48B (local buf[32] + 4 locals)
 * Callees: crc_compute (leaf, 16B), uart_tx_byte (leaf, 8B)
 * Max depth from here: 48 + 16 = 64B
 */
static void process_frame(const uint8_t *frame, uint32_t len)
{
    uint8_t  local_copy[32];
    uint32_t crc_expected;
    uint32_t crc_actual;
    uint32_t i;
    uint8_t  cmd;

    if (len == 0 || len > 30) {
        g_error_count++;
        return;
    }

    for (i = 0; i < len; i++) {
        local_copy[i] = frame[i];
    }

    /* CRC covers all bytes except the last 4 (which hold the CRC) */
    if (len >= 4) {
        crc_expected = ((uint32_t)local_copy[len-4] << 24) |
                       ((uint32_t)local_copy[len-3] << 16) |
                       ((uint32_t)local_copy[len-2] << 8)  |
                        (uint32_t)local_copy[len-1];
        crc_actual = crc_compute(local_copy, len - 4);

        if (crc_actual != crc_expected) {
            g_error_count++;
            uart_tx_byte(0x15);   /* NAK */
            return;
        }
    }

    cmd = (len > 0) ? local_copy[2] : 0;
    switch (cmd) {
        case 0x01:  uart_tx_byte(0xAC); break;
        case 0x02:  uart_tx_byte(0xAC); g_frame_count++; break;
        case 0xFF:  uart_tx_byte(0xAC); break;
        default:    uart_tx_byte(0x15); g_error_count++; break;
    }
}

/* main_loop — poll sensor, transmit frame
 * Frame: 24B (local buf[16] + len + iter)
 * Callees: sensor_read(32B+adc_sample(16B)), process_frame(48B+crc_compute(16B))
 *
 * Worst-case call depth from main_loop:
 *   main_loop(24) + process_frame(48) + crc_compute(16) = 88B
 *   (sensor_read and process_frame not simultaneously on stack)
 */
static void main_loop(void)
{
    uint8_t  tx_buf[16];
    uint32_t tx_len;
    uint32_t iter;

    iter = 0;
    while (1) {
        /* Read sensor every 256 iterations */
        if ((iter & 0xFF) == 0) {
            sensor_read(tx_buf, &tx_len);
            process_frame(tx_buf, tx_len);
        }

        /* Copy DMA RX buffer to local for processing when DMA complete */
        if (g_dma_complete) {
            g_dma_complete = 0;
            if (g_rx_dma_buf[0] == 0x02) {   /* valid frame start */
                process_frame(g_rx_dma_buf, RX_DMA_BUF_SIZE);
            }
        }

        iter++;
    }
}

/* main — top level
 * Frame: 16B (2 locals)
 * Callees: system_init, uart_init, main_loop
 *
 * TOTAL worst-case stack depth:
 *   main(16) + main_loop(24) + process_frame(48) + crc_compute(16) = 104B
 *   Budget: 2048B  (golden.ld _Min_Stack_Size = 0x800)
 *   Usage:  104 / 2048 = 5.1%  → well below 80% warning threshold
 */
int main(void)
{
    uint32_t dummy;
    uint8_t  banner;

    system_init();
    uart_init(g_uart_baud);

    /* Send startup banner */
    banner = 'G';
    uart_tx_byte(banner);
    uart_tx_byte('O');
    uart_tx_byte('\r');
    uart_tx_byte('\n');

    dummy = g_adc_threshold;
    (void)dummy;

    main_loop();

    return 0;
}
