#include "main.h"


HAL_StatusTypeDef AHT10_Init(I2C_HandleTypeDef *hi2c);
void AHT10_GetRaw_Temperature_hum(void);
void AHT10_GetTemperature_hum(int8_t* Data);
