/*
 * HCSR05.c
 *
 *  Created on: Aug 11, 2020
 *      Author: jmdmahdi
 */
#include "HCSR05.h"

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
float_t HCSR05_SoundSpeed;

/**
 * Initialization sensor requirments
 */
void HCSR05_Init(void)
{
	// Init delay function
	DWT_Init();
}

/**
 * Calculate sound speed based on Owen Cramer's method.
 * @param T Temperature (Celsius).
 * @param P Air pressure (Pa).
 * @param H Relative humidity (%).
 */
void HCSR05_Calculate_SoundSpeed(int8_t T, uint32_t P, int8_t H){
	double_t Xc, Xw, V1, V2, V3, f, PSV, PSV1, PSV2, T_kel, T_sqr;

	// Variables description is in the report
	Xc = 400 * 1e-6;
	T_kel = 273.15 + T;
	T_sqr = pow(T, 2);
	f = 1.00062 + 3.141593 * 1e-8 * P + T_sqr * 5.6 * 1e-7;
	PSV1 = pow(T_kel, 2) * 1.2378847 * 1e-8 - 1.9121316 * 1e-2 * T_kel;
	PSV2 = 33.93711047 - 6.3431645 * 1e3 / T_kel;
	PSV = exp(PSV1 + PSV2);
	Xw = (H / 100) * f * PSV / P;
	V1 = 0.603055 * T + 331.5024 - T_sqr * 5.28 * 1e-4 + (0.1495874 * T + 51.471935 -T_sqr * 7.82 * 1e-4) * Xw;
	V2 = (-1.82 * 1e-7 + 3.73 * 1e-8 * T - T_sqr * 2.93 * 1e-10) * P + (-85.20931 - 0.228525 * T + T_sqr * 5.91 * 1e-5) * Xc;
	V3 = pow(Xw, 2) * 2.835149 - pow(P, 2) * 2.15 * 1e-13 + pow(Xc, 2) * 29.179762 + 4.86 * 1e-4 * Xw * P * Xc;

	HCSR05_SoundSpeed =  V1 + V2 - V3;
}

/**
 * Calculate sound time of flight.
 */
void HCSR05_Calculate_TOF(void)
{
	// Send 10 microsecond pulse on trigger pin
	HAL_GPIO_WritePin(HCSR05_Trigger_Port, HCSR05_Trigger_Pin, GPIO_PIN_SET);
	DWT_Delay(10);
	HAL_GPIO_WritePin(HCSR05_Trigger_Port, HCSR05_Trigger_Pin, GPIO_PIN_RESET);

	// Start timer
	HAL_TIM_IC_Start_IT(HCSR05_Htim, HCSR05_Channel);

	// Wait for Echo pulse
	uint32_t startTick = HAL_GetTick();
	do{
		if(HCSR05_Captured) break;
	}while((HAL_GetTick() - startTick) < 500);

	// Reset state
	HCSR05_Captured = 0;
	HAL_TIM_IC_Stop_IT(HCSR05_Htim, HCSR05_Channel);
}
/**
 * must put in HAL_TIM_IC_CaptureCallback
 */
void HCSR05_TIM_Callback(TIM_HandleTypeDef *htim)
{
	// If the interrupt source is on our channel
	if (htim->Channel == HCSR05_Channel) {
		// If the first val is not captured
		if (HCSR05_Is_First_Val_Captured==0) {
			// Get first value
			HCSR05_IC_First_Val = HAL_TIM_ReadCapturedValue(htim, HCSR05_Channel);
			// Set first val captured as true
			HCSR05_Is_First_Val_Captured = 1;
			// change the polarity to falling edge
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, HCSR05_Channel, TIM_INPUTCHANNELPOLARITY_FALLING);
		} else if (HCSR05_Is_First_Val_Captured==1) { // If first val is already captured
			// Get second value
			HCSR05_IC_Second_Val = HAL_TIM_ReadCapturedValue(htim, HCSR05_Channel);

			// Calculate HCSR05_TOF
			if (HCSR05_IC_Second_Val > HCSR05_IC_First_Val) {
				HCSR05_TOF = HCSR05_IC_Second_Val-HCSR05_IC_First_Val;
			} else if (HCSR05_IC_First_Val > HCSR05_IC_Second_Val) {
				HCSR05_TOF = (0xffff - HCSR05_IC_First_Val) + HCSR05_IC_Second_Val;
			}

			// Capturing finished
			HCSR05_Captured = 1;

			// Reset HCSR05_Is_First_Val_Captured for next use
			HCSR05_Is_First_Val_Captured = 0;
			// Reset the counter
			__HAL_TIM_SET_COUNTER(htim, 0);
			// Set polarity to rising edge for next use
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, HCSR05_Channel, TIM_INPUTCHANNELPOLARITY_RISING);
		}
	}
}

/**
 * Get things ready.
 * @param trig_port HCSR05 Trigger pin port.
 * @param trig_pin HCSR05 Trigger pin.
 * @param htim HCSR05 timer.
 * @param timer_channel HCSR05 timer channel.
 * @param distance Distance between transducers (cm).
 */
void HCSR05_Ready(GPIO_TypeDef *trig_port, uint16_t trig_pin, TIM_HandleTypeDef* htim, uint32_t timer_channel, uint8_t distance){
	// Set trigger port and pin global variables
	HCSR05_Trigger_Port = trig_port;
	HCSR05_Trigger_Pin = trig_pin;
	// Set timer global variables
	HCSR05_Htim = htim;
	HCSR05_Channel = timer_channel;
	// Set distance global variable
	HCSR05_Distance = distance;
	// Reset measurement Variables
	HCSR05_TOF = 0;
	HCSR05_Captured = 0;
	HCSR05_IC_First_Val = 0;
	HCSR05_IC_Second_Val = 0;
	HCSR05_TOF = 0;
	HCSR05_Is_First_Val_Captured = 0;
	HCSR05_SoundSpeed = 0;
}

/**
 * Get wind speed on one axis.
 * @param T Temperature (Celsius).
 * @param P Air pressure (Pa).
 * @param H Relative humidity (%).
 */
float_t HCSR05_Get_WindSpeed(int8_t T, uint32_t P, int8_t H){
	// Calculate sound speed
	HCSR05_Calculate_SoundSpeed(T, P, H);
	// Calculate time of flight
	HCSR05_Calculate_TOF();

	// If Calculated values true
	if(HCSR05_TOF > 0 && HCSR05_SoundSpeed > 0){
		// Calculate and Return Wind Speed on one axis
		return (HCSR05_Distance * 1e4 / HCSR05_TOF) - HCSR05_SoundSpeed;
	}
	return 0;
}

/**
 * Calculate speed R and theta
 * @param X_axis X axis speed.
 * @param Y_axis Y axis speed.
 * @param result Air pressure (Pa).
 */
void HCSR05_Calculate_WindSpeedNdAngle(float_t X_axis, float_t Y_axis, float_t *result){
	//Convert data to complex numbers
	float _Complex speed = X_axis + (Y_axis * _Complex_I);
	// fill result with R and theta form complex number
	*result = cabs(speed);
	*(result+1) = carg(speed);
}
