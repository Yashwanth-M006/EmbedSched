/*
 * main.c — Project 4: no_stack_section
 *
 * Realistic bare-metal STM32F407 firmware stub.
 * Compiles without HAL — all register access is direct.
 *
 * Memory layout intent:
 *   .data  ~128 bytes  (initialized globals)
 *   .bss   ~4352 bytes (uninit globals, including rx/tx buffers)
 *   Stack: implicit — _estack(0x20020000) - __bss_end__
 *
 * The call chain:
 *   main()
 *     └─ system_init()         frame: 16B
 *     └─ uart_init()           frame: 24B
 *     └─ loop:
 *           uart_poll()        frame: 32B
 *             └─ process_rx()  frame: 48B
 *
 * Worst-case depth: 16 + 24 + 32 + 48 = 120 bytes (modest, deliberate).
 * The bug is NOT the call depth — it's that the tool can't verify
 * stack headroom without an explicit _Min_Stack_Size.
 */

#include <stdint.h>
#include <stddef.h>

/* ── Register base addresses (STM32F407, no HAL) ── */
#define RCC_BASE        0x40023800UL
#define GPIOA_BASE      0x40020000UL
#define USART1_BASE     0x40011000UL

#define RCC_AHB1ENR     (*((volatile uint32_t *)(RCC_BASE   + 0x30)))
#define RCC_APB2ENR     (*((volatile uint32_t *)(RCC_BASE   + 0x44)))
#define GPIOA_MODER     (*((volatile uint32_t *)(GPIOA_BASE + 0x00)))
#define GPIOA_AFRL      (*((volatile uint32_t *)(GPIOA_BASE + 0x20)))
#define USART1_SR       (*((volatile uint32_t *)(USART1_BASE + 0x00)))
#define USART1_DR       (*((volatile uint32_t *)(USART1_BASE + 0x04)))
#define USART1_BRR      (*((volatile uint32_t *)(USART1_BASE + 0x08)))
#define USART1_CR1      (*((volatile uint32_t *)(USART1_BASE + 0x0C)))

/* ── .data section: initialized globals ── */
/* These land in .data — copied from flash to SRAM at startup.
 * Contributes to __bss_end__ displacement from SRAM base. */
static uint32_t g_uart_baud      = 115200;
static uint32_t g_system_clock   = 16000000;   /* HSI default, Hz */
static uint8_t  g_tx_ready       = 0;
static uint8_t  g_initialized    = 0;
static uint32_t g_tick_count     = 0;
static uint32_t g_rx_count       = 0;
static uint32_t g_tx_count       = 0;
static uint32_t g_error_count    = 0;
static uint8_t  g_protocol_ver   = 1;
static uint8_t  g_node_id        = 0xA1;

/* ── .bss section: zero-initialized globals ── */
/* Deliberately sized to consume a meaningful chunk of SRAM,
 * making the implicit stack headroom calculation non-trivial.
 *
 * Total .bss target: ~4352 bytes
 *   rx_buffer:        256 bytes
 *   tx_buffer:        256 bytes
 *   frame_buffer:    1024 bytes
 *   sensor_buf:       512 bytes
 *   log_buffer:      2048 bytes  ← dominant contributor
 *   misc:             256 bytes
 */

#define RX_BUF_SIZE     256
#define TX_BUF_SIZE     256
#define FRAME_BUF_SIZE  1024
#define SENSOR_BUF_SIZE 512
#define LOG_BUF_SIZE    2048

static uint8_t  g_rx_buffer[RX_BUF_SIZE];
static uint8_t  g_tx_buffer[TX_BUF_SIZE];
static uint8_t  g_frame_buffer[FRAME_BUF_SIZE];
static uint16_t g_sensor_data[SENSOR_BUF_SIZE / 2];  /* 256 uint16_t = 512 bytes */
static uint8_t  g_log_buffer[LOG_BUF_SIZE];

/* Smaller misc BSS */
static volatile uint32_t g_irq_count;
static volatile uint8_t  g_overflow_flag;
static uint32_t          g_checksum;
static uint8_t           g_state_machine;
static uint32_t          g_timeout_ticks;

/* ── Forward declarations ── */
static void system_init(void);
static void uart_init(uint32_t baud);
static void uart_send_byte(uint8_t byte);
static int  uart_poll(void);
static void process_rx(uint8_t *buf, uint32_t len);

/* ── system_init: enable clocks, minimal RCC config ──
 * Stack frame: 16 bytes (2 local uint32_t + alignment)
 */
static void system_init(void)
{
    uint32_t tmp;
    uint32_t delay;

    /* Enable GPIOA clock (bit 0 of AHB1ENR) */
    RCC_AHB1ENR |= (1UL << 0);

    /* Enable USART1 clock (bit 4 of APB2ENR) */
    RCC_APB2ENR |= (1UL << 4);

    /* Short delay for clock stabilisation */
    for (delay = 0; delay < 1000; delay++) {
        tmp = RCC_AHB1ENR;  /* dummy read to prevent optimisation */
        (void)tmp;
    }

    g_initialized = 1;
}

/* ── uart_init: configure PA9 (TX) / PA10 (RX) as AF7, set baud ──
 * Stack frame: 24 bytes (3 locals + alignment)
 */
static void uart_init(uint32_t baud)
{
    uint32_t mantissa;
    uint32_t fraction;
    uint32_t brr_val;

    /* PA9, PA10 → Alternate Function mode (MODER bits = 0b10) */
    GPIOA_MODER &= ~((3UL << 18) | (3UL << 20));
    GPIOA_MODER |=  ((2UL << 18) | (2UL << 20));

    /* Set AF7 (USART1) for PA9 and PA10 in AFRL */
    GPIOA_AFRL &= ~((0xFUL << 4) | (0xFUL << 8));
    GPIOA_AFRL |=  ((7UL  << 4) | (7UL  << 8));

    /* BRR calculation: USARTDIV = f_CLK / baud
     * mantissa = integer part, fraction = (fractional * 16)
     * Using HSI at 16 MHz */
    mantissa = g_system_clock / baud;
    fraction = ((g_system_clock % baud) * 16) / baud;
    brr_val  = (mantissa << 4) | (fraction & 0xF);

    USART1_BRR = brr_val;

    /* Enable USART1: TE + RE + UE */
    USART1_CR1 = (1UL << 3) | (1UL << 2) | (1UL << 13);

    g_uart_baud = baud;
    g_tx_ready  = 1;
}

/* ── uart_send_byte: blocking byte transmit ──
 * Stack frame: 8 bytes
 */
static void uart_send_byte(uint8_t byte)
{
    /* Wait for TXE (bit 7) */
    while (!(USART1_SR & (1UL << 7)));
    USART1_DR = byte;
    g_tx_count++;
}

/* ── process_rx: validate and handle a received frame ──
 * Stack frame: 48 bytes (local buf[32] + 4 locals)
 * This is the deepest frame in the call chain.
 */
static void process_rx(uint8_t *buf, uint32_t len)
{
    uint8_t  local_frame[32];   /* 32-byte local copy */
    uint32_t i;
    uint32_t checksum;
    uint8_t  cmd;

    if (len == 0 || len > 32) {
        g_error_count++;
        return;
    }

    /* Copy into local frame */
    for (i = 0; i < len; i++) {
        local_frame[i] = buf[i];
    }

    /* Compute simple additive checksum */
    checksum = 0;
    for (i = 0; i < len - 1; i++) {
        checksum += local_frame[i];
    }

    if ((checksum & 0xFF) != local_frame[len - 1]) {
        g_error_count++;
        return;
    }

    cmd = local_frame[0];
    g_checksum = checksum;

    /* Dispatch on command byte */
    switch (cmd) {
        case 0x01:
            g_state_machine = 1;
            uart_send_byte(0xAC);  /* ACK */
            break;
        case 0x02:
            g_state_machine = 2;
            uart_send_byte(0xAC);
            break;
        case 0xFF:
            g_state_machine = 0;
            uart_send_byte(0xAC);
            break;
        default:
            g_error_count++;
            uart_send_byte(0x15);  /* NAK */
            break;
    }

    g_rx_count++;
}

/* ── uart_poll: check for received bytes, assemble frame ──
 * Stack frame: 32 bytes (local rx_byte + head + tail + len + timeout)
 */
static int uart_poll(void)
{
    uint8_t  rx_byte;
    uint32_t head;
    uint32_t tail;
    uint32_t len;
    uint32_t timeout;

    /* Check RXNE (bit 5) */
    if (!(USART1_SR & (1UL << 5))) {
        return 0;
    }

    rx_byte = (uint8_t)(USART1_DR & 0xFF);
    g_irq_count++;

    /* Simple ring-buffer head tracking */
    head = g_rx_count % RX_BUF_SIZE;
    g_rx_buffer[head] = rx_byte;

    /* Check for frame delimiter (0x0A = newline) */
    if (rx_byte == 0x0A) {
        tail = 0;
        len  = head;
        timeout = 0;
        (void)tail;
        (void)timeout;

        if (len > 0) {
            process_rx(g_rx_buffer, len);
        }
        return 1;
    }

    return 0;
}

/* ── main: top-level application loop ──
 * Stack frame: 16 bytes (loop counter + status)
 * Worst-case call chain: main(16) → uart_poll(32) → process_rx(48)
 *   = 96 bytes of stack frames
 *   + system_init(16) and uart_init(24) called once at startup
 *   max simultaneous depth = 96 bytes
 */
int main(void)
{
    uint32_t loop_count;
    int      status;

    system_init();
    uart_init(g_uart_baud);

    /* Send startup banner */
    uart_send_byte('O');
    uart_send_byte('K');
    uart_send_byte('\r');
    uart_send_byte('\n');

    loop_count = 0;
    while (1) {
        status = uart_poll();
        (void)status;
        loop_count++;

        /* Every 65536 loops, log tick */
        if ((loop_count & 0xFFFF) == 0) {
            g_tick_count++;
            if (g_tick_count % 100 == 0) {
                uart_send_byte('.');
            }
        }

        /* Overflow detection (deliberate: never clears g_overflow_flag) */
        if (g_rx_count > 0xFFFFFFF0UL) {
            g_overflow_flag = 1;
        }
    }

    return 0;  /* never reached */
}
