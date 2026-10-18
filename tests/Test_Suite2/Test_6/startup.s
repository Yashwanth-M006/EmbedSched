g_pfnVectors:
    .word _estack
    .word Reset_Handler
    .word adc_dma_isr

Reset_Handler:
    ldr r0, =main
    bx r0
