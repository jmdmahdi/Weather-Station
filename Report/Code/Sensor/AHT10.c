/*
 * HCSR05.h
 *
 *  Created on: Aug 11, 2020
 *      Author: jmdmahdi
 */

#include "AHT10.h"

uint8_t AHT10_RX_Data[6];
uint32_t AHT10_ADC_Raw;
float AHT10_Temperature;
float AHT10_Humidity;
uint8_t AHT10_TmpHum_Cmd[3] = { 0xAC, 0x33, 0x00};
#define AHT10_ADRESS (0x38 << 1)
uint8_t T_100ms = 255;
uint8_t AHT10_Switcher = 255;

I2C_HandleTypeDef *AHT10_hi2c;

void AHT10_Init(I2C_HandleTypeDef *hi2c) {
	AHT10_hi2c = hi2c;
}

void AHT10_GetRaw_Temperature_hum(void) {
	HAL_I2C_Master_Receive(AHT10_hi2c, AHT10_ADRESS, (uint8_t*) AHT10_RX_Data,
			6, 100);
}

void AHT10_GetTemperature_hum(int8_t *Data) {
	HAL_I2C_Master_Transmit(AHT10_hi2c, AHT10_ADRESS,
			(uint8_t*) AHT10_TmpHum_Cmd, 3, 100);
	AHT10_GetRaw_Temperature_hum();
	AHT10_ADC_Raw = (((uint32_t) AHT10_RX_Data[3] & 15) << 16)
			| ((uint32_t) AHT10_RX_Data[4] << 8) | AHT10_RX_Data[5];
	AHT10_Temperature = (float) (AHT10_ADC_Raw * 200.00 / 1048576.00) - 50.00;

	AHT10_ADC_Raw = ((uint32_t) AHT10_RX_Data[1] << 12)
			| ((uint32_t) AHT10_RX_Data[2] << 4) | (AHT10_RX_Data[3] >> 4);
	AHT10_Humidity = (float) (AHT10_ADC_Raw * 100.00 / 1048576.00);

	*Data = AHT10_Temperature;
	*(Data + 1) = AHT10_Humidity;
}
