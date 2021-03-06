/*
 * HCSR05.h
 *
 *  Created on: Aug 11, 2020
 *      Author: jmdmahdi
 */

#ifndef AHT10_H
#define AHT10_H

#include "stm32f1xx_hal.h"

void AHT10_Init(I2C_HandleTypeDef *hi2c);
void AHT10_GetRaw_Temperature_hum(void);
void AHT10_GetTemperature_hum(int8_t *Data);

#endif /* AHT10_H */
