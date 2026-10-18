/* startup.s — STM32F407 minimal startup
 * Deliberately omits _Min_Stack_Size and _Min_Heap_Size.
 * Stack exists only as the gap between __bss_end__ and SRAM top.
 * This is the bug Project 4 is designed to expose.
 */

    .syntax unified
    .cpu cortex-m4
    .fpu softvfp
    .thumb

/* ── External symbols defined by the linker script ── */
    .global  _sidata      /* LMA of .data section (in flash) */
    .global  _sdata       /* VMA start of .data in SRAM      */
    .global  _edata       /* VMA end of .data in SRAM        */
    .global  _sbss        /* start of .bss                   */
    .global  _ebss        /* end of .bss                     */

/* NOTE: _estack is NOT defined here — it comes from linker script.
 * In minimal.ld there is NO explicit stack section, so _estack
 * is set to the top of SRAM (ORIGIN(SRAM) + LENGTH(SRAM)).
 * The stack size is therefore SRAM_TOP - __bss_end__ — unknown statically.
 */

/* ── Vector Table ── */
    .section .isr_vector, "a", %progbits
    .type    g_pfnVectors, %object

g_pfnVectors:
    /* ARM Cortex-M core exceptions */
    .word   _estack                     /*  0: Initial Stack Pointer     */
    .word   Reset_Handler               /*  1: Reset                     */
    .word   NMI_Handler                 /*  2: NMI                       */
    .word   HardFault_Handler           /*  3: Hard Fault                */
    .word   MemManage_Handler           /*  4: MPU Fault                 */
    .word   BusFault_Handler            /*  5: Bus Fault                 */
    .word   UsageFault_Handler          /*  6: Usage Fault               */
    .word   0                           /*  7: Reserved                  */
    .word   0                           /*  8: Reserved                  */
    .word   0                           /*  9: Reserved                  */
    .word   0                           /* 10: Reserved                  */
    .word   SVC_Handler                 /* 11: SVCall                    */
    .word   DebugMon_Handler            /* 12: Debug Monitor             */
    .word   0                           /* 13: Reserved                  */
    .word   PendSV_Handler              /* 14: PendSV                    */
    .word   SysTick_Handler             /* 15: SysTick                   */

    /* STM32F407 peripheral IRQs */
    .word   WWDG_IRQHandler             /* 16: Window Watchdog           */
    .word   PVD_IRQHandler              /* 17: PVD via EXTI              */
    .word   TAMP_STAMP_IRQHandler       /* 18: Tamper and Timestamps     */
    .word   RTC_WKUP_IRQHandler         /* 19: RTC Wakeup                */
    .word   FLASH_IRQHandler            /* 20: Flash global              */
    .word   RCC_IRQHandler              /* 21: RCC global                */
    .word   EXTI0_IRQHandler            /* 22: EXTI Line 0               */
    .word   EXTI1_IRQHandler            /* 23: EXTI Line 1               */
    .word   EXTI2_IRQHandler            /* 24: EXTI Line 2               */
    .word   EXTI3_IRQHandler            /* 25: EXTI Line 3               */
    .word   EXTI4_IRQHandler            /* 26: EXTI Line 4               */
    .word   DMA1_Stream0_IRQHandler     /* 27: DMA1 Stream 0             */
    .word   DMA1_Stream1_IRQHandler     /* 28: DMA1 Stream 1             */
    .word   DMA1_Stream2_IRQHandler     /* 29: DMA1 Stream 2             */
    .word   DMA1_Stream3_IRQHandler     /* 30: DMA1 Stream 3             */
    .word   DMA1_Stream4_IRQHandler     /* 31: DMA1 Stream 4             */
    .word   DMA1_Stream5_IRQHandler     /* 32: DMA1 Stream 5             */
    .word   DMA1_Stream6_IRQHandler     /* 33: DMA1 Stream 6             */
    .word   ADC_IRQHandler              /* 34: ADC1, ADC2, ADC3 globals  */
    .word   0                           /* 35: Reserved (CAN1_TX on F4)  */
    .word   0                           /* 36: Reserved                  */
    .word   0                           /* 37: Reserved                  */
    .word   0                           /* 38: Reserved                  */
    .word   EXTI9_5_IRQHandler          /* 39: EXTI Lines 5-9            */
    .word   TIM1_BRK_TIM9_IRQHandler    /* 40: TIM1 Break + TIM9 global  */
    .word   TIM1_UP_TIM10_IRQHandler    /* 41: TIM1 Update + TIM10       */
    .word   TIM1_TRG_COM_TIM11_IRQHandler /* 42: TIM1 Trigger + TIM11   */
    .word   TIM1_CC_IRQHandler          /* 43: TIM1 Capture Compare      */
    .word   TIM2_IRQHandler             /* 44: TIM2 global               */
    .word   TIM3_IRQHandler             /* 45: TIM3 global               */
    .word   TIM4_IRQHandler             /* 46: TIM4 global               */
    .word   I2C1_EV_IRQHandler          /* 47: I2C1 Event                */
    .word   I2C1_ER_IRQHandler          /* 48: I2C1 Error                */
    .word   I2C2_EV_IRQHandler          /* 49: I2C2 Event                */
    .word   I2C2_ER_IRQHandler          /* 50: I2C2 Error                */
    .word   SPI1_IRQHandler             /* 51: SPI1 global               */
    .word   SPI2_IRQHandler             /* 52: SPI2 global               */
    .word   USART1_IRQHandler           /* 53: USART1 global             */
    .word   USART2_IRQHandler           /* 54: USART2 global             */
    .word   USART3_IRQHandler           /* 55: USART3 global             */
    .word   EXTI15_10_IRQHandler        /* 56: EXTI Lines 10-15          */
    .word   RTC_Alarm_IRQHandler        /* 57: RTC Alarm (A and B) EXTI  */
    .word   OTG_FS_WKUP_IRQHandler      /* 58: USB OTG FS Wakeup EXTI   */
    .word   TIM8_BRK_TIM12_IRQHandler   /* 59: TIM8 Break + TIM12        */
    .word   TIM8_UP_TIM13_IRQHandler    /* 60: TIM8 Update + TIM13       */
    .word   TIM8_TRG_COM_TIM14_IRQHandler /* 61: TIM8 Trigger + TIM14   */
    .word   TIM8_CC_IRQHandler          /* 62: TIM8 Capture Compare      */
    .word   DMA1_Stream7_IRQHandler     /* 63: DMA1 Stream 7             */
    .word   0                           /* 64: Reserved                  */
    .word   SDIO_IRQHandler             /* 65: SDIO global               */
    .word   TIM5_IRQHandler             /* 66: TIM5 global               */
    .word   SPI3_IRQHandler             /* 67: SPI3 global               */
    .word   UART4_IRQHandler            /* 68: UART4 global              */
    .word   UART5_IRQHandler            /* 69: UART5 global              */
    .word   TIM6_DAC_IRQHandler         /* 70: TIM6 global + DAC1&2 err  */
    .word   TIM7_IRQHandler             /* 71: TIM7 global               */
    .word   DMA2_Stream0_IRQHandler     /* 72: DMA2 Stream 0             */
    .word   DMA2_Stream1_IRQHandler     /* 73: DMA2 Stream 1             */
    .word   DMA2_Stream2_IRQHandler     /* 74: DMA2 Stream 2             */
    .word   DMA2_Stream3_IRQHandler     /* 75: DMA2 Stream 3             */
    .word   DMA2_Stream4_IRQHandler     /* 76: DMA2 Stream 4             */
    .word   0                           /* 77: Reserved                  */
    .word   0                           /* 78: Reserved                  */
    .word   0                           /* 79: Reserved                  */
    .word   0                           /* 80: Reserved                  */
    .word   0                           /* 81: Reserved                  */
    .word   0                           /* 82: Reserved                  */
    .word   OTG_FS_IRQHandler           /* 83: USB OTG FS global         */
    .word   DMA2_Stream5_IRQHandler     /* 84: DMA2 Stream 5             */
    .word   DMA2_Stream6_IRQHandler     /* 85: DMA2 Stream 6             */
    .word   DMA2_Stream7_IRQHandler     /* 86: DMA2 Stream 7             */
    .word   USART6_IRQHandler           /* 87: USART6 global             */
    .word   I2C3_EV_IRQHandler          /* 88: I2C3 Event                */
    .word   I2C3_ER_IRQHandler          /* 89: I2C3 Error                */
    .word   0                           /* 90: Reserved                  */
    .word   0                           /* 91: Reserved                  */
    .word   0                           /* 92: Reserved                  */
    .word   0                           /* 93: Reserved                  */
    .word   0                           /* 94: Reserved                  */
    .word   0                           /* 95: Reserved                  */
    .word   0                           /* 96: Reserved                  */
    .word   RNG_IRQHandler              /* 97: RNG global                */
    .word   FPU_IRQHandler              /* 98: FPU global                */

    .size g_pfnVectors, .-g_pfnVectors

/* ── Reset Handler ── */
    .section .text.Reset_Handler
    .weak    Reset_Handler
    .type    Reset_Handler, %function

Reset_Handler:
    /* Copy .data from flash (LMA) to SRAM (VMA) */
    ldr     r0, =_sdata
    ldr     r1, =_edata
    ldr     r2, =_sidata
    movs    r3, #0
    b       copy_data_loop

copy_data_body:
    ldr     r4, [r2, r3]
    str     r4, [r0, r3]
    adds    r3, r3, #4

copy_data_loop:
    adds    r4, r0, r3
    cmp     r4, r1
    bcc     copy_data_body

    /* Zero-fill .bss */
    ldr     r2, =_sbss
    ldr     r4, =_ebss
    movs    r3, #0
    b       zero_bss_loop

zero_bss_body:
    str     r3, [r2]
    adds    r2, r2, #4

zero_bss_loop:
    cmp     r2, r4
    bcc     zero_bss_body

    /* Call main */
    bl      main
    bx      lr
    .size   Reset_Handler, .-Reset_Handler

/* ── Default Handler (infinite loop) ── */
    .section .text.Default_Handler, "ax", %progbits

Default_Handler:
Infinite_Loop:
    b       Infinite_Loop
    .size   Default_Handler, .-Default_Handler

/* ── Weak aliases for all handlers → Default_Handler ── */
    .weak   NMI_Handler
    .thumb_set NMI_Handler, Default_Handler

    .weak   HardFault_Handler
    .thumb_set HardFault_Handler, Default_Handler

    .weak   MemManage_Handler
    .thumb_set MemManage_Handler, Default_Handler

    .weak   BusFault_Handler
    .thumb_set BusFault_Handler, Default_Handler

    .weak   UsageFault_Handler
    .thumb_set UsageFault_Handler, Default_Handler

    .weak   SVC_Handler
    .thumb_set SVC_Handler, Default_Handler

    .weak   DebugMon_Handler
    .thumb_set DebugMon_Handler, Default_Handler

    .weak   PendSV_Handler
    .thumb_set PendSV_Handler, Default_Handler

    .weak   SysTick_Handler
    .thumb_set SysTick_Handler, Default_Handler

    .weak   WWDG_IRQHandler
    .thumb_set WWDG_IRQHandler, Default_Handler

    .weak   PVD_IRQHandler
    .thumb_set PVD_IRQHandler, Default_Handler

    .weak   TAMP_STAMP_IRQHandler
    .thumb_set TAMP_STAMP_IRQHandler, Default_Handler

    .weak   RTC_WKUP_IRQHandler
    .thumb_set RTC_WKUP_IRQHandler, Default_Handler

    .weak   FLASH_IRQHandler
    .thumb_set FLASH_IRQHandler, Default_Handler

    .weak   RCC_IRQHandler
    .thumb_set RCC_IRQHandler, Default_Handler

    .weak   EXTI0_IRQHandler
    .thumb_set EXTI0_IRQHandler, Default_Handler

    .weak   EXTI1_IRQHandler
    .thumb_set EXTI1_IRQHandler, Default_Handler

    .weak   EXTI2_IRQHandler
    .thumb_set EXTI2_IRQHandler, Default_Handler

    .weak   EXTI3_IRQHandler
    .thumb_set EXTI3_IRQHandler, Default_Handler

    .weak   EXTI4_IRQHandler
    .thumb_set EXTI4_IRQHandler, Default_Handler

    .weak   DMA1_Stream0_IRQHandler
    .thumb_set DMA1_Stream0_IRQHandler, Default_Handler

    .weak   DMA1_Stream1_IRQHandler
    .thumb_set DMA1_Stream1_IRQHandler, Default_Handler

    .weak   DMA1_Stream2_IRQHandler
    .thumb_set DMA1_Stream2_IRQHandler, Default_Handler

    .weak   DMA1_Stream3_IRQHandler
    .thumb_set DMA1_Stream3_IRQHandler, Default_Handler

    .weak   DMA1_Stream4_IRQHandler
    .thumb_set DMA1_Stream4_IRQHandler, Default_Handler

    .weak   DMA1_Stream5_IRQHandler
    .thumb_set DMA1_Stream5_IRQHandler, Default_Handler

    .weak   DMA1_Stream6_IRQHandler
    .thumb_set DMA1_Stream6_IRQHandler, Default_Handler

    .weak   ADC_IRQHandler
    .thumb_set ADC_IRQHandler, Default_Handler

    .weak   EXTI9_5_IRQHandler
    .thumb_set EXTI9_5_IRQHandler, Default_Handler

    .weak   TIM1_BRK_TIM9_IRQHandler
    .thumb_set TIM1_BRK_TIM9_IRQHandler, Default_Handler

    .weak   TIM1_UP_TIM10_IRQHandler
    .thumb_set TIM1_UP_TIM10_IRQHandler, Default_Handler

    .weak   TIM1_TRG_COM_TIM11_IRQHandler
    .thumb_set TIM1_TRG_COM_TIM11_IRQHandler, Default_Handler

    .weak   TIM1_CC_IRQHandler
    .thumb_set TIM1_CC_IRQHandler, Default_Handler

    .weak   TIM2_IRQHandler
    .thumb_set TIM2_IRQHandler, Default_Handler

    .weak   TIM3_IRQHandler
    .thumb_set TIM3_IRQHandler, Default_Handler

    .weak   TIM4_IRQHandler
    .thumb_set TIM4_IRQHandler, Default_Handler

    .weak   I2C1_EV_IRQHandler
    .thumb_set I2C1_EV_IRQHandler, Default_Handler

    .weak   I2C1_ER_IRQHandler
    .thumb_set I2C1_ER_IRQHandler, Default_Handler

    .weak   I2C2_EV_IRQHandler
    .thumb_set I2C2_EV_IRQHandler, Default_Handler

    .weak   I2C2_ER_IRQHandler
    .thumb_set I2C2_ER_IRQHandler, Default_Handler

    .weak   SPI1_IRQHandler
    .thumb_set SPI1_IRQHandler, Default_Handler

    .weak   SPI2_IRQHandler
    .thumb_set SPI2_IRQHandler, Default_Handler

    .weak   USART1_IRQHandler
    .thumb_set USART1_IRQHandler, Default_Handler

    .weak   USART2_IRQHandler
    .thumb_set USART2_IRQHandler, Default_Handler

    .weak   USART3_IRQHandler
    .thumb_set USART3_IRQHandler, Default_Handler

    .weak   EXTI15_10_IRQHandler
    .thumb_set EXTI15_10_IRQHandler, Default_Handler

    .weak   RTC_Alarm_IRQHandler
    .thumb_set RTC_Alarm_IRQHandler, Default_Handler

    .weak   OTG_FS_WKUP_IRQHandler
    .thumb_set OTG_FS_WKUP_IRQHandler, Default_Handler

    .weak   TIM8_BRK_TIM12_IRQHandler
    .thumb_set TIM8_BRK_TIM12_IRQHandler, Default_Handler

    .weak   TIM8_UP_TIM13_IRQHandler
    .thumb_set TIM8_UP_TIM13_IRQHandler, Default_Handler

    .weak   TIM8_TRG_COM_TIM14_IRQHandler
    .thumb_set TIM8_TRG_COM_TIM14_IRQHandler, Default_Handler

    .weak   TIM8_CC_IRQHandler
    .thumb_set TIM8_CC_IRQHandler, Default_Handler

    .weak   DMA1_Stream7_IRQHandler
    .thumb_set DMA1_Stream7_IRQHandler, Default_Handler

    .weak   SDIO_IRQHandler
    .thumb_set SDIO_IRQHandler, Default_Handler

    .weak   TIM5_IRQHandler
    .thumb_set TIM5_IRQHandler, Default_Handler

    .weak   SPI3_IRQHandler
    .thumb_set SPI3_IRQHandler, Default_Handler

    .weak   UART4_IRQHandler
    .thumb_set UART4_IRQHandler, Default_Handler

    .weak   UART5_IRQHandler
    .thumb_set UART5_IRQHandler, Default_Handler

    .weak   TIM6_DAC_IRQHandler
    .thumb_set TIM6_DAC_IRQHandler, Default_Handler

    .weak   TIM7_IRQHandler
    .thumb_set TIM7_IRQHandler, Default_Handler

    .weak   DMA2_Stream0_IRQHandler
    .thumb_set DMA2_Stream0_IRQHandler, Default_Handler

    .weak   DMA2_Stream1_IRQHandler
    .thumb_set DMA2_Stream1_IRQHandler, Default_Handler

    .weak   DMA2_Stream2_IRQHandler
    .thumb_set DMA2_Stream2_IRQHandler, Default_Handler

    .weak   DMA2_Stream3_IRQHandler
    .thumb_set DMA2_Stream3_IRQHandler, Default_Handler

    .weak   DMA2_Stream4_IRQHandler
    .thumb_set DMA2_Stream4_IRQHandler, Default_Handler

    .weak   OTG_FS_IRQHandler
    .thumb_set OTG_FS_IRQHandler, Default_Handler

    .weak   DMA2_Stream5_IRQHandler
    .thumb_set DMA2_Stream5_IRQHandler, Default_Handler

    .weak   DMA2_Stream6_IRQHandler
    .thumb_set DMA2_Stream6_IRQHandler, Default_Handler

    .weak   DMA2_Stream7_IRQHandler
    .thumb_set DMA2_Stream7_IRQHandler, Default_Handler

    .weak   USART6_IRQHandler
    .thumb_set USART6_IRQHandler, Default_Handler

    .weak   I2C3_EV_IRQHandler
    .thumb_set I2C3_EV_IRQHandler, Default_Handler

    .weak   I2C3_ER_IRQHandler
    .thumb_set I2C3_ER_IRQHandler, Default_Handler

    .weak   RNG_IRQHandler
    .thumb_set RNG_IRQHandler, Default_Handler

    .weak   FPU_IRQHandler
    .thumb_set FPU_IRQHandler, Default_Handler
