/* main.c — Project 3: recursive_isr (STM32F407, Cortex-M4)
 *
 * THE BUG:
 *   USART1_IRQHandler calls uart_rx_dispatch().
 *   uart_rx_dispatch() calls parse_packet().
 *   parse_packet() calls itself recursively when it encounters a
 *   nested sub-packet marker (0xBB) in the data stream.
 *
 *   At runtime on real hardware, a pathological input stream with
 *   deeply nested sub-packets will exhaust the 1KB stack and
 *   trigger a HardFault with no warning.
 *
 *   At static analysis time, your analyzer must:
 *   (a) Build the call graph from objdump disassembly
 *   (b) Detect the back-edge: parse_packet → parse_packet
 *   (c) Trace the ISR path to the recursion:
 *         USART1_IRQHandler → uart_rx_dispatch → parse_packet → [CYCLE]
 *   (d) Emit CRITICAL: recursion detected in ISR call chain, stack UNBOUNDED
 *
 * CALL GRAPH (with the bug):
 *
 *   main
 *   ├── system_init          (leaf)
 *   ├── uart_init            (leaf)
 *   └── [loop] idle_task     (leaf)
 *
 *   USART1_IRQHandler        ← ISR entry point (vector table position 53)
 *   └── uart_rx_dispatch
 *       ├── checksum_verify  (leaf — no recursion here, do not false flag)
 *       └── parse_packet     ← RECURSIVE
 *           ├── emit_token   (leaf)
 *           └── parse_packet ← BACK-EDGE (self-call on sub-packet detection)
 *
 *   TIM2_IRQHandler          ← Clean ISR, no recursion, for contrast
 *
 * KEY SUBTLETIES FOR THE CALL GRAPH BUILDER:
 *
 *   [1] parse_packet calls itself conditionally:
 *         if (buf[i] == SUBPACKET_MARKER) {
 *             result = parse_packet(buf + i + 1, remaining, depth + 1);
 *         }
 *       GCC compiles this as a 'bl parse_packet' inside parse_packet.
 *       This IS a back-edge. Your DFS must detect it.
 *
 *   [2] checksum_verify is called before parse_packet in uart_rx_dispatch.
 *       It has an inner loop — compiled as 'b' (branch), not 'bl'.
 *       The analyzer MUST NOT flag checksum_verify as recursive.
 *       Same as crc_compute in Project 1 — the critical 'b' vs 'bl' test.
 *
 *   [3] TIM2_IRQHandler also calls a function (tick_update).
 *       tick_update is a leaf. TIM2's call chain is clean — no recursion.
 *       The analyzer must only flag USART1's chain, not TIM2's.
 *       This tests that the recursion detection is path-specific,
 *       not global (i.e. finding recursion in one ISR must not corrupt
 *       the analysis of a clean ISR).
 *
 *   [4] The 'depth' parameter is not used to limit recursion at runtime.
 *       This is intentional: real buggy firmware doesn't always have
 *       guards. The analyzer should not assume depth-limiting is present
 *       just because a depth counter is passed as a parameter.
 *
 * EXPECTED ANALYZER OUTPUT:
 *   Score: 55 / 100
 *   [CRITICAL] [STATIC] recursion_detected
 *     Path: USART1_IRQHandler → uart_rx_dispatch → parse_packet → parse_packet
 *     Stack: UNBOUNDED. _Min_Stack_Size = 1024B cannot guarantee safety.
 *   [WARNING]  [CALCULATED] isr_in_flash
 *     USART1_IRQHandler at 0x080001xx — Flash (no ITCM on F407).
 *   [INFO]     [STATIC] stack_not_in_ccm
 *     Stack top = SRAM1 (0x2001C000). CCM available at 0x10000000.
 */

#include <stdint.h>
#include <stddef.h>

/* ── Register definitions (STM32F407) ── */
#define RCC_BASE        0x40023800UL
#define GPIOA_BASE      0x40020000UL
#define USART1_BASE     0x40011000UL
#define TIM2_BASE       0x40000000UL

#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x30))
#define RCC_APB1ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x40))
#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE   + 0x44))
#define USART1_SR       (*(volatile uint32_t *)(USART1_BASE + 0x00))
#define USART1_DR       (*(volatile uint32_t *)(USART1_BASE + 0x04))
#define USART1_BRR      (*(volatile uint32_t *)(USART1_BASE + 0x08))
#define USART1_CR1      (*(volatile uint32_t *)(USART1_BASE + 0x0C))
#define TIM2_SR         (*(volatile uint32_t *)(TIM2_BASE   + 0x10))
#define TIM2_CNT        (*(volatile uint32_t *)(TIM2_BASE   + 0x24))

/* ── Protocol constants ── */
#define START_MARKER      0xAA
#define END_MARKER        0x55
#define SUBPACKET_MARKER  0xBB   /* triggers recursive parse — THE BUG */
#define MAX_TOKEN_LEN     32
#define RX_BUF_SIZE       256

/* ── Globals ── */
static uint32_t g_system_hz  = 16000000UL;
static uint32_t g_uart_baud  = 115200UL;
static uint32_t g_tick       = 0;
static uint32_t g_rx_errors  = 0;
static uint32_t g_packets_ok = 0;
static uint8_t  g_rx_buf[RX_BUF_SIZE];
static uint32_t g_rx_head    = 0;
static uint32_t g_rx_tail    = 0;
static volatile uint8_t g_rx_ready = 0;

/* ── Forward declarations ── */
static void    system_init(void);
static void    uart_init(void);
static void    idle_task(void);
static void    tick_update(void);
static uint8_t checksum_verify(const uint8_t *buf, uint32_t len);
static int     parse_packet(const uint8_t *buf, uint32_t len, uint32_t depth);
static void    emit_token(const uint8_t *token, uint32_t token_len);
static void    uart_rx_dispatch(void);

/* ══════════════════════════════════════════════════════════════════════
 * ISR HANDLERS
 * ══════════════════════════════════════════════════════════════════════ */

/* TIM2_IRQHandler — 1ms system tick, CLEAN ISR
 *
 * Call chain: TIM2_IRQHandler → tick_update (leaf)
 * No recursion. No blocking. Stack depth: ISR(8B) + tick_update(8B) = 16B.
 *
 * PURPOSE IN PROJECT 3:
 *   Provides a contrast against USART1_IRQHandler.
 *   Analyzer must flag USART1's chain, NOT TIM2's.
 *   Tests that recursion detection is per-ISR, not global.
 */
void TIM2_IRQHandler(void)
{
    TIM2_SR &= ~(1UL);    /* clear UIF flag */
    tick_update();
}

/* USART1_IRQHandler — receive byte, dispatch to protocol parser
 *
 * Call chain: USART1_IRQHandler → uart_rx_dispatch → parse_packet → parse_packet
 *                                                                     ^^^^^^^^^^^
 *                                                                     RECURSION
 *
 * This ISR is at vector table position 53 (startup.s line: .word USART1_IRQHandler)
 * The analyzer finds it in the vector table, traces its call chain,
 * and must detect the recursive back-edge in parse_packet.
 *
 * Frame: 8B (ISR minimal frame — sets g_rx_ready, calls dispatcher)
 */
void USART1_IRQHandler(void)
{
    uint8_t byte;

    if (USART1_SR & (1UL << 5)) {    /* RXNE: receive not empty */
        byte = (uint8_t)(USART1_DR & 0xFF);
        g_rx_buf[g_rx_head & (RX_BUF_SIZE - 1)] = byte;
        g_rx_head++;

        if (byte == END_MARKER) {
            g_rx_ready = 1;
            uart_rx_dispatch();   /* ← calls into recursive parse chain */
        }
    }
}

/* ══════════════════════════════════════════════════════════════════════
 * PROTOCOL IMPLEMENTATION
 * ══════════════════════════════════════════════════════════════════════ */

/* tick_update — increment tick counter and clear overflow flag
 * Frame: 8B
 * Leaf function — no callees.
 * Called ONLY by TIM2_IRQHandler. Clean path.
 */
static void tick_update(void)
{
    uint32_t current;
    current = g_tick + 1;
    if (current == 0) current = 1;   /* prevent zero tick */
    g_tick = current;
}

/* checksum_verify — additive checksum over a buffer
 * Frame: 24B (i, sum, expected — all local)
 * Leaf function — no callees.
 *
 * CONTAINS AN INNER LOOP compiled to 'b' instruction (not 'bl').
 * The analyzer call graph builder MUST NOT treat this as recursion.
 * This is the same 'b' vs 'bl' trap as in Projects 1 and 2.
 *
 * Called by uart_rx_dispatch. Does NOT call parse_packet or anything
 * that leads to recursion. Analyzer must not flag this path.
 */
static uint8_t checksum_verify(const uint8_t *buf, uint32_t len)
{
    uint32_t i;
    uint32_t sum;
    uint8_t  expected;

    if (len < 2) return 0;

    sum = 0;
    for (i = 0; i < len - 1; i++) {    /* inner loop → 'b', not 'bl' */
        sum += buf[i];
    }
    expected = buf[len - 1];
    return ((sum & 0xFF) == expected) ? 1 : 0;
}

/* emit_token — output a parsed token over UART
 * Frame: 16B (i, timeout — locals)
 * Leaf function — no callees.
 * Called by parse_packet. Clean termination.
 */
static void emit_token(const uint8_t *token, uint32_t token_len)
{
    uint32_t i;
    uint32_t timeout;

    for (i = 0; i < token_len; i++) {
        timeout = 10000;
        while (!(USART1_SR & (1UL << 7)) && timeout--);
        USART1_DR = token[i];
    }
}

/* parse_packet — recursive protocol parser
 *
 * THIS IS THE BUG.
 *
 * When the parser encounters SUBPACKET_MARKER (0xBB) in the byte
 * stream, it calls itself to parse the nested sub-packet. There is
 * no depth limit enforced. A crafted input can nest arbitrarily
 * deeply, consuming stack until HardFault.
 *
 * Frame: 48B (token[MAX_TOKEN_LEN=32] + i + token_len + result = 32+4+4+4+4 = 48B)
 * Callees: emit_token (leaf, 16B), parse_packet (SELF — back-edge)
 *
 * THE CALL GRAPH EDGE YOUR ANALYZER MUST FIND:
 *   In the disassembly of parse_packet, there will be:
 *     bl  parse_packet    ← self-call inside the SUBPACKET_MARKER branch
 *   This 'bl' with the callee == caller is the back-edge.
 *   Your DFS must detect this as a cycle and return has_recursion=True.
 *
 * NOTE: 'depth' parameter is passed through but NOT used to limit recursion.
 * A naive analyzer might look at the parameter name and assume depth-
 * limiting is happening. The correct approach is to inspect the actual
 * call instruction — if bl parse_packet exists, recursion exists.
 */
static int parse_packet(const uint8_t *buf, uint32_t len, uint32_t depth)
{
    uint8_t  token[MAX_TOKEN_LEN];
    uint32_t i;
    uint32_t token_len;
    int      result;

    if (len == 0 || buf == NULL) {
        return -1;
    }

    /* depth is tracked but NOT used to terminate recursion — this is the bug */
    (void)depth;

    i = 0;
    token_len = 0;
    result = 0;

    while (i < len) {
        if (buf[i] == END_MARKER) {
            /* emit whatever token we have accumulated */
            if (token_len > 0) {
                emit_token(token, token_len);
                token_len = 0;
            }
            result = (int)i;
            break;

        } else if (buf[i] == SUBPACKET_MARKER) {
            /* ── RECURSIVE CALL ── */
            /* Sub-packet detected: recursively parse the nested content.
             * No depth limit — any input can drive this arbitrarily deep.
             * At runtime: stack overflow on deeply nested input.
             * At analysis time: back-edge parse_packet → parse_packet.
             */
            uint32_t remaining = (i + 1 < len) ? (len - i - 1) : 0;
            result = parse_packet(buf + i + 1, remaining, depth + 1);
            if (result < 0) {
                g_rx_errors++;
                return -1;
            }
            i += (uint32_t)result + 2;  /* skip past sub-packet */

        } else {
            /* accumulate token byte */
            if (token_len < MAX_TOKEN_LEN) {
                token[token_len++] = buf[i];
            }
            i++;
        }
    }

    return result;
}

/* uart_rx_dispatch — called from USART1_IRQHandler when END_MARKER received
 * Frame: 32B (local frame_start + frame_len + tail_snapshot + csum_ok)
 * Callees: checksum_verify (leaf, 24B), parse_packet (recursive, 48B+)
 *
 * This function is the BRIDGE between the ISR and the recursive parser.
 * It is reachable from USART1_IRQHandler and calls parse_packet.
 * The critical path the analyzer must trace:
 *   USART1_IRQHandler(8B) → uart_rx_dispatch(32B) → parse_packet(48B+) → [CYCLE]
 */
static void uart_rx_dispatch(void)
{
    uint32_t tail_snapshot;
    uint32_t frame_start;
    uint32_t frame_len;
    uint8_t  csum_ok;

    tail_snapshot = g_rx_tail;
    frame_start   = tail_snapshot;
    frame_len     = g_rx_head - tail_snapshot;

    if (frame_len < 2 || frame_len > RX_BUF_SIZE) {
        g_rx_errors++;
        g_rx_tail = g_rx_head;
        g_rx_ready = 0;
        return;
    }

    /* Verify checksum before parsing.
     * checksum_verify: leaf, no recursion — must NOT be flagged.
     */
    csum_ok = checksum_verify(&g_rx_buf[frame_start & (RX_BUF_SIZE - 1)],
                               frame_len);
    if (!csum_ok) {
        g_rx_errors++;
        g_rx_tail = g_rx_head;
        g_rx_ready = 0;
        return;
    }

    /* parse_packet: RECURSIVE — will be flagged by analyzer */
    parse_packet(&g_rx_buf[frame_start & (RX_BUF_SIZE - 1)],
                 frame_len,
                 0);       /* depth=0 at top-level call */

    g_rx_tail = g_rx_head;
    g_rx_ready = 0;
    g_packets_ok++;
}

/* ══════════════════════════════════════════════════════════════════════
 * NON-ISR CODE
 * ══════════════════════════════════════════════════════════════════════ */

/* system_init — clock and peripheral enable
 * Frame: 16B
 * Leaf.
 */
static void system_init(void)
{
    uint32_t delay;
    uint32_t tmp;

    RCC_AHB1ENR |= (1UL << 0);  /* GPIOA */
    RCC_APB1ENR |= (1UL << 0);  /* TIM2  */
    RCC_APB2ENR |= (1UL << 4);  /* USART1 */

    for (delay = 0; delay < 500; delay++) {
        tmp = RCC_AHB1ENR;
        (void)tmp;
    }
}

/* uart_init — configure USART1
 * Frame: 24B
 * Leaf.
 */
static void uart_init(void)
{
    uint32_t mantissa;
    uint32_t fraction;
    uint32_t brr;

    /* PA9 = TX, PA10 = RX, AF7 */
    *(volatile uint32_t *)(GPIOA_BASE + 0x00) &= ~((3UL << 18) | (3UL << 20));
    *(volatile uint32_t *)(GPIOA_BASE + 0x00) |=  ((2UL << 18) | (2UL << 20));
    *(volatile uint32_t *)(GPIOA_BASE + 0x20) &= ~((0xFUL << 4) | (0xFUL << 8));
    *(volatile uint32_t *)(GPIOA_BASE + 0x20) |=  ((7UL << 4) | (7UL << 8));

    mantissa = g_system_hz / g_uart_baud;
    fraction = ((g_system_hz % g_uart_baud) * 16) / g_uart_baud;
    brr = (mantissa << 4) | (fraction & 0xF);

    USART1_BRR = brr;
    /* Enable RXNEIE (bit 5) + TE + RE + UE */
    USART1_CR1 = (1UL << 5) | (1UL << 3) | (1UL << 2) | (1UL << 13);
}

/* idle_task — background low-priority work
 * Frame: 16B
 * Leaf. Only runs when no ISR is active.
 */
static void idle_task(void)
{
    uint32_t last_tick;
    last_tick = g_tick;
    /* sleep-like spin — would use WFI in production */
    while (g_tick == last_tick) {
        __asm volatile ("nop");
    }
}

/* main — initialise and loop
 * Frame: 8B
 * Callees: system_init (16B), uart_init (24B), idle_task (16B)
 * Worst-case bounded depth (non-ISR): main(8) + uart_init(24) = 32B
 *
 * NOTE: The ISR path is separate from the main call chain.
 *       The analyzer must handle both independently.
 */
int main(void)
{
    uint32_t dummy;

    system_init();
    uart_init();

    dummy = g_tick;
    (void)dummy;

    while (1) {
        idle_task();
    }

    return 0;
}
