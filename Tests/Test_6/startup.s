/* startup.s — STM32F407 startup for Test_6: isr_calls_blocking_hal
 *
 * Standard two-phase init: copy .data, zero .bss, call main.
 * Key: TIM3_IRQHandler appears in the vector table at position 45 (IRQ28).
 * The analyzer must find this name here and cross-reference it with
 * the symbol in blocking_isr.txt to confirm it is an ISR handler.
 * Then it must walk the call graph:
 *   TIM3_IRQHandler -> HAL_Delay          (BLOCKING — busy-wait on SysTick)
 *   TIM3_IRQHandler -> HAL_UART_Transmit  (BLOCKING — polls UART SR register)
 *                                          ^^^^^^^^^
 *                                          BLOCKING CALLS
 */

    .syntax unified
    .cpu    cortex-m4
    .fpu    softvfp
    .thumb

    .global _sidata
    .global _sdata
    .global _edata
    .global _sbss
    .global _ebss

/* ── Vector Table ── */
    .section .isr_vector, "a", %progbits
    .type    g_pfnVectors, %object

g_pfnVectors:
    .word   _estack                         /*  0: Initial SP               */
    .word   Reset_Handler                   /*  1: Reset                    */
    .word   NMI_Handler                     /*  2: NMI                      */
    .word   HardFault_Handler               /*  3: HardFault                */
    .word   MemManage_Handler               /*  4: MemManage                */
    .word   BusFault_Handler                /*  5: BusFault                 */
    .word   UsageFault_Handler              /*  6: UsageFault               */
    .word   0                               /*  7: Reserved                 */
    .word   0                               /*  8: Reserved                 */
    .word   0                               /*  9: Reserved                 */
    .word   0                               /* 10: Reserved                 */
    .word   SVC_Handler                     /* 11: SVCall                   */
    .word   DebugMon_Handler                /* 12: DebugMon                 */
    .word   0                               /* 13: Reserved                 */
    .word   PendSV_Handler                  /* 14: PendSV                   */
    .word   SysTick_Handler                 /* 15: SysTick                  */
    /* STM32F407 peripheral IRQs */
    .word   WWDG_IRQHandler                 /* 16                           */
    .word   PVD_IRQHandler                  /* 17                           */
    .word   TAMP_STAMP_IRQHandler           /* 18                           */
    .word   RTC_WKUP_IRQHandler             /* 19                           */
    .word   FLASH_IRQHandler                /* 20                           */
    .word   RCC_IRQHandler                  /* 21                           */
    .word   EXTI0_IRQHandler                /* 22                           */
    .word   EXTI1_IRQHandler                /* 23                           */
    .word   EXTI2_IRQHandler                /* 24                           */
    .word   EXTI3_IRQHandler                /* 25                           */
    .word   EXTI4_IRQHandler                /* 26                           */
    .word   DMA1_Stream0_IRQHandler         /* 27                           */
    .word   DMA1_Stream1_IRQHandler         /* 28                           */
    .word   DMA1_Stream2_IRQHandler         /* 29                           */
    .word   DMA1_Stream3_IRQHandler         /* 30                           */
    .word   DMA1_Stream4_IRQHandler         /* 31                           */
    .word   DMA1_Stream5_IRQHandler         /* 32                           */
    .word   DMA1_Stream6_IRQHandler         /* 33                           */
    .word   ADC_IRQHandler                  /* 34                           */
    .word   0                               /* 35: Reserved                 */
    .word   0                               /* 36: Reserved                 */
    .word   0                               /* 37: Reserved                 */
    .word   0                               /* 38: Reserved                 */
    .word   EXTI9_5_IRQHandler              /* 39                           */
    .word   TIM1_BRK_TIM9_IRQHandler        /* 40                           */
    .word   TIM1_UP_TIM10_IRQHandler        /* 41                           */
    .word   TIM1_TRG_COM_TIM11_IRQHandler   /* 42                           */
    .word   TIM1_CC_IRQHandler              /* 43                           */
    .word   TIM2_IRQHandler                 /* 44                           */
    .word   TIM3_IRQHandler                 /* 45 ← THE ISR UNDER TEST      */
    .word   TIM4_IRQHandler                 /* 46                           */
    .word   I2C1_EV_IRQHandler              /* 47                           */
    .word   I2C1_ER_IRQHandler              /* 48                           */
    .word   I2C2_EV_IRQHandler              /* 49                           */
    .word   I2C2_ER_IRQHandler              /* 50                           */
    .word   SPI1_IRQHandler                 /* 51                           */
    .word   SPI2_IRQHandler                 /* 52                           */
    .word   USART1_IRQHandler               /* 53                           */
    .word   USART2_IRQHandler               /* 54                           */
    .word   USART3_IRQHandler               /* 55                           */

    .size g_pfnVectors, .-g_pfnVectors

/* ── Reset Handler ── */
    .section .text.Reset_Handler
    .weak    Reset_Handler
    .type    Reset_Handler, %function

Reset_Handler:
    ldr     r0, =_sdata
    ldr     r1, =_edata
    ldr     r2, =_sidata
    movs    r3, #0
    b       RL1

BL1: ldr     r4, [r2, r3]
    str     r4, [r0, r3]
    adds    r3, r3, #4
RL1: adds    r4, r0, r3
    cmp     r4, r1
    bcc     BL1

    ldr     r2, =_sbss
    ldr     r4, =_ebss
    movs    r3, #0
    b       RL2

BL2: str     r3, [r2]
    adds    r2, r2, #4
RL2: cmp     r2, r4
    bcc     BL2

    bl      main
    bx      lr
    .size Reset_Handler, .-Reset_Handler

/* ── Default Handler ── */
    .section .text.Default_Handler, "ax", %progbits
Default_Handler:
    b       Default_Handler
    .size Default_Handler, .-Default_Handler

/* ── Weak aliases ── */
    .weak NMI_Handler
    .thumb_set NMI_Handler,Default_Handler
    .weak HardFault_Handler
    .thumb_set HardFault_Handler,Default_Handler
    .weak MemManage_Handler
    .thumb_set MemManage_Handler,Default_Handler
    .weak BusFault_Handler
    .thumb_set BusFault_Handler,Default_Handler
    .weak UsageFault_Handler
    .thumb_set UsageFault_Handler,Default_Handler
    .weak SVC_Handler
    .thumb_set SVC_Handler,Default_Handler
    .weak DebugMon_Handler
    .thumb_set DebugMon_Handler,Default_Handler
    .weak PendSV_Handler
    .thumb_set PendSV_Handler,Default_Handler
    .weak SysTick_Handler
    .thumb_set SysTick_Handler,Default_Handler
    .weak WWDG_IRQHandler
    .thumb_set WWDG_IRQHandler,Default_Handler
    .weak PVD_IRQHandler
    .thumb_set PVD_IRQHandler,Default_Handler
    .weak TAMP_STAMP_IRQHandler
    .thumb_set TAMP_STAMP_IRQHandler,Default_Handler
    .weak RTC_WKUP_IRQHandler
    .thumb_set RTC_WKUP_IRQHandler,Default_Handler
    .weak FLASH_IRQHandler
    .thumb_set FLASH_IRQHandler,Default_Handler
    .weak RCC_IRQHandler
    .thumb_set RCC_IRQHandler,Default_Handler
    .weak EXTI0_IRQHandler
    .thumb_set EXTI0_IRQHandler,Default_Handler
    .weak EXTI1_IRQHandler
    .thumb_set EXTI1_IRQHandler,Default_Handler
    .weak EXTI2_IRQHandler
    .thumb_set EXTI2_IRQHandler,Default_Handler
    .weak EXTI3_IRQHandler
    .thumb_set EXTI3_IRQHandler,Default_Handler
    .weak EXTI4_IRQHandler
    .thumb_set EXTI4_IRQHandler,Default_Handler
    .weak DMA1_Stream0_IRQHandler
    .thumb_set DMA1_Stream0_IRQHandler,Default_Handler
    .weak DMA1_Stream1_IRQHandler
    .thumb_set DMA1_Stream1_IRQHandler,Default_Handler
    .weak DMA1_Stream2_IRQHandler
    .thumb_set DMA1_Stream2_IRQHandler,Default_Handler
    .weak DMA1_Stream3_IRQHandler
    .thumb_set DMA1_Stream3_IRQHandler,Default_Handler
    .weak DMA1_Stream4_IRQHandler
    .thumb_set DMA1_Stream4_IRQHandler,Default_Handler
    .weak DMA1_Stream5_IRQHandler
    .thumb_set DMA1_Stream5_IRQHandler,Default_Handler
    .weak DMA1_Stream6_IRQHandler
    .thumb_set DMA1_Stream6_IRQHandler,Default_Handler
    .weak ADC_IRQHandler
    .thumb_set ADC_IRQHandler,Default_Handler
    .weak EXTI9_5_IRQHandler
    .thumb_set EXTI9_5_IRQHandler,Default_Handler
    .weak TIM1_BRK_TIM9_IRQHandler
    .thumb_set TIM1_BRK_TIM9_IRQHandler,Default_Handler
    .weak TIM1_UP_TIM10_IRQHandler
    .thumb_set TIM1_UP_TIM10_IRQHandler,Default_Handler
    .weak TIM1_TRG_COM_TIM11_IRQHandler
    .thumb_set TIM1_TRG_COM_TIM11_IRQHandler,Default_Handler
    .weak TIM1_CC_IRQHandler
    .thumb_set TIM1_CC_IRQHandler,Default_Handler
    .weak TIM2_IRQHandler
    .thumb_set TIM2_IRQHandler,Default_Handler
    .weak TIM3_IRQHandler
    .thumb_set TIM3_IRQHandler,Default_Handler
    .weak TIM4_IRQHandler
    .thumb_set TIM4_IRQHandler,Default_Handler
    .weak I2C1_EV_IRQHandler
    .thumb_set I2C1_EV_IRQHandler,Default_Handler
    .weak I2C1_ER_IRQHandler
    .thumb_set I2C1_ER_IRQHandler,Default_Handler
    .weak I2C2_EV_IRQHandler
    .thumb_set I2C2_EV_IRQHandler,Default_Handler
    .weak I2C2_ER_IRQHandler
    .thumb_set I2C2_ER_IRQHandler,Default_Handler
    .weak SPI1_IRQHandler
    .thumb_set SPI1_IRQHandler,Default_Handler
    .weak SPI2_IRQHandler
    .thumb_set SPI2_IRQHandler,Default_Handler
    .weak USART1_IRQHandler
    .thumb_set USART1_IRQHandler,Default_Handler
    .weak USART2_IRQHandler
    .thumb_set USART2_IRQHandler,Default_Handler
    .weak USART3_IRQHandler
    .thumb_set USART3_IRQHandler,Default_Handler
