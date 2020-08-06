#ifndef MAX44009_h
#define MAX44009_h
#include "stm32f1xx_hal.h"

#define MAX44009_ADDR 0x4A<<1 // or 0x4B if A0 pin connected to Vcc

HAL_StatusTypeDef MAX44009_Begin();

float MAX44009_Get_Lux(void);

#endif
