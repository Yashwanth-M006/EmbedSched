#include "tp.h"
#include "tpl_os.h"

#define APP_Task_blink_START_SEC_CODE
#include "tpl_memmap.h"

FUNC(int, OS_APPL_CODE) main(void)
{
  initBoard();
  StartOS(OSDEFAULTAPPMODE);
  return 0;
}

void _exit(int status)
{
  (void)status;
  while(1);
}

DeclareResource(led_resource);

TASK(blink)
{
  GetResource(led_resource);
  ledToggle(BLUE);
  ReleaseResource(led_resource);
  TerminateTask();
}
#define APP_Task_blink_STOP_SEC_CODE
#include "tpl_memmap.h"

#define APP_Task_read_button_START_SEC_CODE
#include "tpl_memmap.h"
TASK(read_button)
{
  volatile uint32_t count = 0;
  GetResource(led_resource);
  ledToggle(GREEN);
  for (count = 0; count < 1000; count++) {
    __asm__ volatile("nop");
  }
  ReleaseResource(led_resource);
  TerminateTask();
}
#define APP_Task_read_button_STOP_SEC_CODE
#include "tpl_memmap.h"

#define APP_ISR_isr_button_START_SEC_CODE
#include "tpl_memmap.h"
DeclareTask(read_button);

ISR(isr_button)
{
  ledToggle(RED);
  ActivateTask(read_button);
}
#define APP_ISR_isr_button_STOP_SEC_CODE
#include "tpl_memmap.h"

#define OS_START_SEC_CODE
#include "tpl_memmap.h"
FUNC(void, OS_CODE) assert_failed(uint8_t* file, uint32_t line)
{
  (void)file;
  (void)line;
}
#define OS_STOP_SEC_CODE
#include "tpl_memmap.h"
