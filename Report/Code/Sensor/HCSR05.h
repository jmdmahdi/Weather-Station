/*
 * HCSR05.h
 *
 *  Created on: Aug 11, 2020
 *      Author: jmdmahdi
 */

#ifndef HCSR05_H
#define HCSR05_H

#include "stm32f1xx_hal.h"
#include "math.h"
#include "dwt_delay.h"

#ifndef PI
#define PI 3.14159265358979323846264338327950288
#endif

void HCSR05_Init(void);
void HCSR05_Calculate_SoundSpeed(int8_t T, uint32_t P, int8_t H);
void HCSR05_Calculate_TOF(void);
void HCSR05_TIM_Callback(TIM_HandleTypeDef *htim);
void HCSR05_Ready(GPIO_TypeDef *trig_port, uint16_t trig_pin, TIM_HandleTypeDef* htim, uint32_t timer_channel, uint8_t distance, int8_t angle_difference);
float_t HCSR05_Get_WindSpeed(int8_t T, uint32_t P, int8_t H);
float_t HCSR05_Calculate_Angle(double_t x, double_t y);
void HCSR05_Calculate_WindSpeedNdAngle(float_t X_axis, float_t Y_axis, int16_t x, int16_t y, float_t *result);


GPIO_TypeDef *HCSR05_Trigger_Port;
uint16_t HCSR05_Trigger_Pin;
TIM_HandleTypeDef* HCSR05_Htim;
uint32_t HCSR05_Channel;
uint8_t HCSR05_Captured;
uint32_t HCSR05_IC_First_Val;
uint32_t HCSR05_IC_Second_Val;
uint32_t HCSR05_TOF;
uint8_t HCSR05_Is_First_Val_Captured;
uint8_t HCSR05_Distance;
int8_t HCSR05_Angle_Difference;
float_t HCSR05_SoundSpeed;

#endif /* HCSR05_H */
