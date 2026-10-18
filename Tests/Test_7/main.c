/**
 * main.c — Project 7: fragmented_flash
 *
 * Intentional linker fragmentation for cache locality analysis.
 *
 * This firmware is compiled with -ffunction-sections and --gc-sections,
 * which causes each function to be placed in its own .text.* section.
 * The linker then scatters these sections across flash memory, creating
 * non-contiguous code layout.
 *
 * Impact:
 *   - I-cache misses on transition between hot functions
 *   - Instruction prefetch stalls
 *   - TLBP penalties on some ARM variants
 *
 * Hot functions (defined in hot_functions.txt):
 *   1. main           @ 0x08001000  (44 bytes)
 *   2. sensor_read    @ 0x080015C0  (32 bytes)    ← 0x5C0 byte gap
 *   3. uart_tx        @ 0x08002800  (80 bytes)    ← 0x1240 byte gap
 *
 * Cache line: 32 bytes (STM32F4 I-cache)
 * Ideal: hot functions within same cache line (within 32B)
 * Reality: functions separated by 1400+ bytes → multiple misses
 *
 * Compiler: arm-none-eabi-gcc 12.x with -ffunction-sections
 * Linker: arm-none-eabi-ld with --gc-sections
 *
 * Fix:
 *   1. Use -fno-function-sections or group hot functions
 *   2. Add link-time grouping directives in linker script
 *   3. Profile cache behavior to identify colocate candidates
 */

#include <stdint.h>
#include <string.h>

/* ---- Minimal stubs (avoid full HAL) -------------------------------------- */

typedef enum {
    SENSOR_OK      = 0x00U,
    SENSOR_ERROR   = 0x01U,
    SENSOR_TIMEOUT = 0x02U
} SensorStatus;

typedef struct {
    uint32_t temperature;
    uint32_t humidity;
    uint32_t pressure;
} SensorData;

/* ---- Global state in .bss ------------------------------------------------- */

static volatile uint32_t sensor_state = 0;
static volatile uint32_t uart_state   = 0;
static uint8_t tx_buffer[16];

/* ---- Sensor functions (fragmented across flash) -------------------------- */

/* @0x08001000 — 0x44 bytes — .text.main */
int main(void)
{
    /* Initialize system */
    system_init();
    uart_init();

    /* Check sensor state */
    if (sensor_state == 0) {
        main_loop();
    }

    /* Read sensor (calls sensor_read @ 0x080015C0 — 0x5C0 byte gap!)
     * This triggers I-cache miss: 0x08001000 → 0x080015C0 */
    SensorData data;
    data.temperature = sensor_read();

    if (data.temperature == 0) {
        return 1;
    }

    /* Transmit result via UART (calls uart_tx @ 0x08002800 — 0x1240 byte gap!)
     * Another I-cache miss: 0x080015C0 → 0x08002800 */
    uart_tx();

    if (uart_state != 0) {
        return 1;
    }

    return 0;
}

/* @0x08001044 — 0x0C bytes — .text.main_loop */
void main_loop(void)
{
    for (;;) {
        /* Spin */
    }
}

/* @0x08001050 — 0x0A bytes — .text.idle_task */
void idle_task(void)
{
    /* Spin down */
}

/* @0x080010...  — sensor initialization functions — */

void config_sensor(uint32_t mode, uint32_t rate, uint32_t thresh)
{
    /* Configure sensor hardware */
}

void calibrate_sensor(uint32_t factory_cal)
{
    /* Load calibration data */
}

void temp_sensor_init(void)
{
    /* Initialize temp sensor */
}

void humidity_sensor_init(void)
{
    /* Initialize humidity sensor */
}

void pressure_sensor_init(void)
{
    /* Initialize pressure sensor */
}

void read_adc(void)
{
    /* Raw ADC read */
}

void filter_data(void)
{
    /* Low-pass filter */
}

void apply_calibration(void)
{
    /* Post-process with calibration */
}

/* @0x080015C0 — 0x20 bytes — .text.sensor_read
 * HOT FUNCTION #2 — called from main (0x5C0 byte gap to main)
 */
uint32_t sensor_read(void)
{
    /* Read sensor data via I2C / SPI / ADC
     * Called frequently from main
     * GAP: 0x08001000 (main) → 0x080015C0 (sensor_read)
     *      Delta: 0x5C0 bytes = 1472 bytes
     *      At 32-byte I-cache lines: 1472 / 32 = 46 cache lines
     *      Multiple misses on transition.
     */
    read_adc();
    filter_data();
    apply_calibration();

    if (sensor_state == 0) {
        return 0;
    }

    return sensor_state;
}

/* @0x08002800 — 0x50 bytes — .text.uart_tx
 * HOT FUNCTION #3 — called from main
 * GAP: 0x080015C0 (sensor_read) → 0x08002800 (uart_tx)
 *      Delta: 0x1240 bytes = 4672 bytes = 146 cache lines
 */
void uart_tx(void)
{
    /* Transmit sensor data via USART
     * Blocks on USART_SR_TXE
     * Large gap from sensor_read causes I-cache thrashing.
     */
    uart_state = 1;

    for (int i = 0; i < 16; i++) {
        tx_buffer[i] = 0x30 + (i % 10);
    }

    /* Poll USART status — busy-wait (bad in ISR, OK in main) */
    volatile uint32_t *usart_dr = (uint32_t *)0x40004404UL;
    for (int i = 0; i < 16; i++) {
        *usart_dr = tx_buffer[i];
        while ((*usart_dr & 0x40) == 0) {
            /* Wait for TXE */
        }
    }

    uart_state = 0;
}

/* Supporting UART functions — also fragmented */

void uart_rx(void)
{
    /* Receive mode */
}

void uart_flush(void)
{
    /* Clear buffers */
}

void uart_set_baudrate(uint32_t baud)
{
    /* Reconfigure baud rate */
}

void error_handler(void)
{
    /* Handle errors */
}

void log_event(const char *msg)
{
    /* Log an event */
}

uint32_t get_timestamp(void)
{
    /* Get current timestamp */
    return 0;
}

void format_data(void)
{
    /* Format sensor data for transmission */
}

/* ---- System init (minimal stub) ------------------------------------------ */

void system_init(void)
{
    /* In real code: configure clocks, Flash latency, MPU, etc. */
}

void uart_init(void)
{
    /* In real code: configure USART2 GPIO, baud rate, etc. */
}
