/* main.c — Project 2: isr_in_itcm (STM32F746, Cortex-M7)
 *
 * WHAT THIS FIRMWARE TESTS IN THE ANALYZER:
 *
 * Rule 1 — ISR placement (THE PRIMARY TEST):
 *   Three ISR handlers placed in .itcm_text section.
 *   Their linked addresses are in ITCM range [0x00000000, 0x00004000).
 *   Analyzer MUST NOT fire "isr_in_flash" warning for these.
 *   If it does → address-range discrimination is broken.
 *
 * Rule 2 — DMA bus contention (SECONDARY TEST):
 *   uart_tx_dma_buf → .dma_buffers_s2 → SRAM2 (AHB_S2) — CORRECT
 *   adc_dma_buf     → .dma_buffers_s2 → SRAM2 (AHB_S2) — CORRECT
 *   spi_rx_buf      → .dma_buffers_s1 → SRAM1 (AHB_S1) — WRONG (intentional)
 *   Analyzer MUST fire bus contention warning for spi_rx_buf only.
 *
 * Rule 3 — ITCM overflow:
 *   .itcm_text section will be ~4–6KB (well under 16KB limit).
 *   Analyzer MUST NOT fire ITCM overflow warning.
 *
 * Rule 4 — Stack depth:
 *   Worst-case: main(16) + control_loop(32) + pid_update(48)
 *               + filter_sample(24) = 120B vs 2048B budget (5.9%).
 *   Analyzer MUST NOT fire stack overflow warning.
 *
 * Rule 5 — DMA alignment:
 *   All DMA buffers have aligned(32). Analyzer MUST NOT fire.
 *
 * ITCM SECTION MACRO:
 *   __attribute__((section(".itcm_text"))) places a function into
 *   the .itcm_text input section, which the linker places in ITCM VMA.
 *   The copy loop in Reset_Handler copies it from flash LMA at boot.
 *
 * DMA SECTION MACROS:
 *   DMA_S2: correct placement in SRAM2 (AHB_S2, DMA-isolated from CPU)
 *   DMA_S1: intentionally wrong placement in SRAM1 (AHB_S1, same as CPU)
 */

#include <stdint.h>

/* ── Placement macros ── */
#define ITCM_FUNC   __attribute__((section(".itcm_text"), noinline))
#define DMA_S2      __attribute__((section(".dma_buffers_s2"), aligned(32)))
#define DMA_S1      __attribute__((section(".dma_buffers_s1"), aligned(32)))

/* ── STM32F746 register definitions ── */
#define RCC_BASE        0x40023800UL
#define GPIOA_BASE      0x40020000UL
#define GPIOB_BASE      0x40020400UL
#define USART1_BASE     0x40011000UL
#define SPI1_BASE       0x40013000UL
#define ADC1_BASE       0x40012000UL
#define TIM2_BASE       0x40000000UL
#define DMA2_BASE       0x40026400UL

#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x30))
#define RCC_APB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x40))
#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x44))
#define USART1_ISR      (*(volatile uint32_t *)(USART1_BASE + 0x1C))
#define USART1_TDR      (*(volatile uint32_t *)(USART1_BASE + 0x28))
#define USART1_BRR      (*(volatile uint32_t *)(USART1_BASE + 0x0C))
#define USART1_CR1      (*(volatile uint32_t *)(USART1_BASE + 0x00))
#define SPI1_SR         (*(volatile uint32_t *)(SPI1_BASE   + 0x08))
#define SPI1_DR         (*(volatile uint32_t *)(SPI1_BASE   + 0x0C))
#define SPI1_CR1        (*(volatile uint32_t *)(SPI1_BASE   + 0x00))
#define ADC1_SR         (*(volatile uint32_t *)(ADC1_BASE   + 0x00))
#define ADC1_DR         (*(volatile uint32_t *)(ADC1_BASE   + 0x4C))
#define ADC1_CR2        (*(volatile uint32_t *)(ADC1_BASE   + 0x08))
#define TIM2_SR         (*(volatile uint32_t *)(TIM2_BASE   + 0x10))
#define TIM2_CNT        (*(volatile uint32_t *)(TIM2_BASE   + 0x24))

/* ── DMA buffers ──────────────────────────────────────────────────────
 *
 *  uart_tx_dma_buf: SRAM2 via .dma_buffers_s2
 *    DMA2 Stream 7 (USART1_TX) uses this buffer.
 *    SRAM2 is on AHB_S2 — separate bus port from CPU accesses (AHB_S1).
 *    DMA transfer runs on AHB_S2 while CPU runs on AHB_S1 = zero contention.
 *    Analyzer: must NOT fire bus contention for this buffer.
 *
 *  adc_dma_buf: SRAM2 via .dma_buffers_s2
 *    DMA2 Stream 0 (ADC1) writes ADC conversions here in background.
 *    Same isolation benefit as uart_tx_dma_buf.
 *    Analyzer: must NOT fire bus contention for this buffer.
 *
 *  spi_rx_buf: SRAM1 via .dma_buffers_s1  ← DELIBERATELY WRONG
 *    SPI1 RX DMA (DMA2 Stream 2) writes incoming bytes here.
 *    SRAM1 is on AHB_S1 — SAME bus port as CPU D-bus accesses.
 *    When CPU reads from SRAM1 while DMA writes spi_rx_buf,
 *    the AHB arbiter serializes them → ~30% CPU bandwidth loss.
 *    FIX: move spi_rx_buf to SRAM2 (.dma_buffers_s2).
 *    Analyzer: MUST fire dma_bus_contention WARNING for this buffer.
 * ──────────────────────────────────────────────────────────────────── */
#define UART_TX_BUF_SIZE   256
#define ADC_DMA_BUF_SIZE   128
#define SPI_RX_BUF_SIZE    256

static uint8_t  DMA_S2 uart_tx_dma_buf[UART_TX_BUF_SIZE];
static uint16_t DMA_S2 adc_dma_buf[ADC_DMA_BUF_SIZE];
static uint8_t  DMA_S1 spi_rx_buf[SPI_RX_BUF_SIZE];   /* misplaced — Rule 2 trigger */

/* ── Regular globals (DTCM via .data / .bss) ── */
static uint32_t g_system_hz   = 216000000UL;
static uint32_t g_uart_baud   = 1000000UL;    /* 1 Mbaud */
static uint8_t  g_node_id     = 0x10;
static uint32_t g_tick        = 0;
static uint32_t g_isr_count   = 0;
static uint32_t g_spi_rx_head = 0;
static float    g_setpoint    = 100.0f;
static float    g_kp          = 0.5f;
static float    g_ki          = 0.01f;
static float    g_integrator  = 0.0f;
static uint16_t g_adc_last    = 0;
static uint8_t  g_ctrl_active = 0;

/* ── Forward declarations ── */
static void     system_init(void);
static void     uart_init(void);
static uint16_t filter_sample(uint16_t raw);
static float    pid_update(float measured);
static void     control_loop(void);

/* ══════════════════════════════════════════════════════════════════════
 * ISR HANDLERS — ALL IN ITCM
 *
 * The ITCM_FUNC macro expands to:
 *   __attribute__((section(".itcm_text"), noinline))
 *
 * 'noinline' is required: without it the compiler may inline these
 * into callers in flash, effectively moving the code out of ITCM
 * despite the section attribute. 'noinline' forces the linker to
 * preserve them as independent symbols in .itcm_text.
 *
 * WHAT THE ANALYZER MUST DO:
 *   1. Find these symbols in firmware.map
 *   2. See addresses in range [0x00000000, 0x00004000) = ITCM
 *   3. Cross-reference against vector table in startup.s:
 *        TIM2_IRQHandler, DMA2_Stream0_IRQHandler, SPI1_IRQHandler
 *        all appear in g_pfnVectors → confirmed ISRs
 *   4. Classify: ISR in ITCM → CORRECT → must NOT fire Rule 1 warning
 *
 * ADDRESS DISCRIMINATION (the core test):
 *   Flash range: [0x08000000, 0x08100000)
 *   ITCM range:  [0x00000000, 0x00004000)
 *   DTCM range:  [0x20000000, 0x20010000)
 *   SRAM1 range: [0x20010000, 0x2004C000)
 *   SRAM2 range: [0x2004C000, 0x20050000)
 *
 *   Rule 1 must fire ONLY when ISR address is in Flash range.
 *   Rule 1 must NOT fire when ISR address is in ITCM range.
 * ══════════════════════════════════════════════════════════════════════ */

/* TIM2_IRQHandler — 1ms periodic control tick
 * In ITCM → zero wait state, deterministic 12-cycle entry + 0 fetch penalty.
 * Analyzer target: address ~0x00000xxx → ITCM → no warning.
 */
ITCM_FUNC void TIM2_IRQHandler(void)
{
    TIM2_SR &= ~(1UL);          /* clear update interrupt flag */
    g_tick++;
    g_isr_count++;
}

/* DMA2_Stream0_IRQHandler — ADC1 DMA transfer complete
 * In ITCM. Reads DMA LISR, clears flags, sets g_adc_last.
 * Analyzer target: address ~0x00000xxx → ITCM → no warning.
 */
ITCM_FUNC void DMA2_Stream0_IRQHandler(void)
{
    volatile uint32_t *dma_lisr = (volatile uint32_t *)(DMA2_BASE + 0x00);
    volatile uint32_t *dma_lifcr= (volatile uint32_t *)(DMA2_BASE + 0x08);

    if (*dma_lisr & (1UL << 5)) {       /* TCIF0: transfer complete */
        *dma_lifcr = (1UL << 5);        /* clear CTCIF0 */
        g_adc_last = adc_dma_buf[0];    /* latch latest conversion */
    }
    g_isr_count++;
}

/* SPI1_IRQHandler — SPI receive not-empty
 * In ITCM. Reads byte from SPI DR into the misplaced spi_rx_buf.
 * Note: the ISR placement is correct (ITCM).
 *       The BUFFER it writes to (spi_rx_buf) is misplaced (SRAM1).
 *       These are two separate findings — the analyzer must not conflate them.
 * Analyzer target: ISR address ~0x00000xxx → ITCM → no Rule 1 warning.
 *                  spi_rx_buf at 0x20010xxx → SRAM1 → Rule 2 warning.
 */
ITCM_FUNC void SPI1_IRQHandler(void)
{
    if (SPI1_SR & (1UL << 0)) {         /* RXNE: rx buffer not empty */
        uint8_t byte = (uint8_t)(SPI1_DR & 0xFF);
        spi_rx_buf[g_spi_rx_head & (SPI_RX_BUF_SIZE - 1)] = byte;
        g_spi_rx_head++;
    }
    g_isr_count++;
}

/* ══════════════════════════════════════════════════════════════════════
 * NON-ISR HOT FUNCTION IN ITCM
 *
 * control_loop is called at ~1kHz from main. It benefits from ITCM
 * placement because it runs frequently and its cache eviction between
 * calls would add jitter. Placing in ITCM gives guaranteed 0-cycle
 * fetch latency regardless of what else has run in the cache.
 *
 * Analyzer: should note this as a positive hot-path placement decision.
 * ══════════════════════════════════════════════════════════════════════ */

/* filter_sample — single-pole IIR, alpha=0.125
 * Frame: 24B
 * Leaf function — no callees.
 */
ITCM_FUNC uint16_t filter_sample(uint16_t raw)
{
    static uint32_t filtered = 0;
    uint32_t alpha_inv = 8;       /* 1/alpha = 8 → alpha = 0.125 */
    uint32_t new_raw   = (uint32_t)raw;
    filtered = filtered - (filtered / alpha_inv) + (new_raw / alpha_inv);
    return (uint16_t)(filtered & 0x0FFF);
}

/* pid_update — proportional-integral controller
 * Frame: 48B (5 floats + 2 locals)
 * Callees: none (leaf after inlining disabled).
 * noinline via ITCM_FUNC ensures this stays a separate symbol.
 */
ITCM_FUNC float pid_update(float measured)
{
    float error;
    float p_term;
    float i_term;
    float output;
    float integrator_limit = 500.0f;

    error  = g_setpoint - measured;
    p_term = g_kp * error;

    g_integrator += g_ki * error;
    if (g_integrator >  integrator_limit) g_integrator = integrator_limit;
    if (g_integrator < -integrator_limit) g_integrator = -integrator_limit;

    i_term = g_integrator;
    output = p_term + i_term;

    return output;
}

/* control_loop — main control body, called every tick
 * Frame: 32B (local measured + output + iter + tick_last)
 * Callees: filter_sample (24B, ITCM), pid_update (48B, ITCM)
 * Worst-case depth from here: 32 + 48 = 80B
 */
ITCM_FUNC void control_loop(void)
{
    uint16_t raw;
    uint16_t filtered;
    float    measured;
    float    output;
    uint32_t tick_snapshot;

    tick_snapshot = g_tick;
    (void)tick_snapshot;

    raw      = g_adc_last;
    filtered = filter_sample(raw);
    measured = (float)filtered * (3300.0f / 4095.0f);   /* convert to mV */
    output   = pid_update(measured);

    /* Clamp output to DAC range */
    if (output < 0.0f)    output = 0.0f;
    if (output > 3300.0f) output = 3300.0f;

    /* Write to DAC (register stub — address illustrative) */
    *(volatile uint32_t *)0x40007420UL = (uint32_t)(output * 4095.0f / 3300.0f);

    g_ctrl_active = 1;
}

/* ══════════════════════════════════════════════════════════════════════
 * NON-ITCM FUNCTIONS (in flash, lower priority)
 * ══════════════════════════════════════════════════════════════════════ */

/* system_init — called once at startup, never in the hot path
 * Frame: 16B
 * Does NOT need ITCM — cold startup path.
 */
static void system_init(void)
{
    uint32_t delay;
    uint32_t tmp;

    RCC_AHB1ENR |= (1UL << 0) | (1UL << 1);  /* GPIOA, GPIOB */
    RCC_APB1ENR |= (1UL << 0);                /* TIM2 */
    RCC_APB2ENR |= (1UL << 4) | (1UL << 8) | (1UL << 12);  /* USART1, ADC1, SPI1 */

    for (delay = 0; delay < 1000; delay++) {
        tmp = RCC_AHB1ENR;
        (void)tmp;
    }
}

/* uart_init — called once, stays in flash
 * Frame: 24B
 */
static void uart_init(void)
{
    uint32_t brr;
    uint32_t mantissa;
    uint32_t fraction;

    mantissa = g_system_hz / g_uart_baud;
    fraction = ((g_system_hz % g_uart_baud) * 16) / g_uart_baud;
    brr = (mantissa << 4) | (fraction & 0xF);

    USART1_BRR = brr;
    USART1_CR1 = (1UL << 3) | (1UL << 2) | (1UL << 0);  /* TE, RE, UE */
}

/* main — top level, calls into ITCM functions
 * Frame: 16B
 * Worst-case call chain:
 *   main(16) + control_loop(32) + pid_update(48) = 96B
 *   main(16) + control_loop(32) + filter_sample(24) = 72B
 *   Worst: main(16) + control_loop(32) + pid_update(48) = 96B
 *   + system_init(16): simultaneous? NO — sequential. Max = 96B.
 * Budget: 2048B. Usage: 96/2048 = 4.7% → PASS.
 */
int main(void)
{
    uint32_t last_tick;
    uint8_t  banner;

    system_init();
    uart_init();

    /* UART banner using USART1 (F746 uses different SR register) */
    banner = 'F';
    while (!(USART1_ISR & (1UL << 7)));  /* wait TXE */
    USART1_TDR = banner;

    last_tick = 0;
    g_ctrl_active = 0;

    while (1) {
        if (g_tick != last_tick) {
            last_tick = g_tick;
            control_loop();
        }

        /* Idle: spin until next tick */
        if (!g_ctrl_active) {
            /* Could enter SLEEP here in production */
            __asm volatile ("nop");
        }
    }

    return 0;
}
