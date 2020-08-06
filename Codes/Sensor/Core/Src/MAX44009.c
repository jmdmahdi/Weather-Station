#include "MAX44009.h"

I2C_HandleTypeDef *MAX44009_hi2c;

HAL_StatusTypeDef MAX44009_Begin(I2C_HandleTypeDef *hi2c)
{
	MAX44009_hi2c = hi2c;
	return 	HAL_I2C_Mem_Write(MAX44009_hi2c, MAX44009_ADDR, 0x02, 1, 0x00, 1, 100);
}


float MAX44009_Get_Lux(void)
{
	uint8_t data[2];

	if(HAL_I2C_Mem_Read(MAX44009_hi2c, MAX44009_ADDR, 0x03, 1, data, 1, 100) == HAL_OK){
		if(HAL_I2C_Mem_Read(MAX44009_hi2c, MAX44009_ADDR, 0x04, 1, data+1, 1, 100) == HAL_OK){
				// Convert the data to lux
				uint8_t exponent = data[0]>>4;
				uint32_t mantisa = ((data[0] & 0x0F)<<4) + (data[1] & 0x0F);
				mantisa <<= exponent;
				return ((float)(mantisa) * 0.045);
			}
	}
	return 0;
}
