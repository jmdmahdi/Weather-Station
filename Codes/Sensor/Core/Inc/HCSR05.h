/*
 * HCSR05.h
 *
 *  Created on: Aug 11, 2020
 *      Author: jmdmahdi
 */

#ifndef HCSR05_H
#define HCSR05_H

#include "main.h"
#include "math.h"
#include "complex.h"
#include "dwt_delay.h"

#define PI 3.1415926536

extern GPIO_TypeDef *HCSR05_Trigger_Port;
extern uint16_t HCSR05_Trigger_Pin;
extern TIM_HandleTypeDef* HCSR05_Htim;
extern uint32_t HCSR05_Channel;
extern uint8_t HCSR05_Captured;
extern uint32_t HCSR05_IC_First_Val;
extern uint32_t HCSR05_IC_Second_Val;
extern uint32_t HCSR05_TOF;
extern uint8_t HCSR05_Is_First_Val_Captured;
extern uint8_t HCSR05_Distance;
extern float_t HCSR05_SoundSpeed;

void HCSR05_Init(void);
void HCSR05_Calculate_SoundSpeed(int8_t T, uint32_t P, int8_t H);
void HCSR05_Calculate_TOF(void);
void HCSR05_TIM_Callback(TIM_HandleTypeDef *htim);
void HCSR05_Ready(GPIO_TypeDef *trig_port, uint16_t trig_pin, TIM_HandleTypeDef* htim, uint32_t timer_channel, uint8_t distance);
float_t HCSR05_Get_WindSpeed(int8_t T, uint32_t P, int8_t H);
void HCSR05_Calculate_WindSpeedNdAngle(float_t X_axis, float_t Y_axis, float_t *result);

#endif /* HCSR05_H */
