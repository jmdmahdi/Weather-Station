#include "BMP180.h"
#include "main.h"

I2C_HandleTypeDef *_bmp180_ui2c;
BMP180_EEPROM _bmp180_eeprom;
BMP180_OSS _bmp180_oss;

const uint8_t BMP180_EEPROM_ADDR_MSB[11] = { 0xaa, 0xac, 0xae, 0xb0, 0xb2, 0xb4, 0xb6, 0xb8, 0xba, 0xbc, 0xbe };
const uint8_t BMP180_EEPROM_ADDR_LSB[11] = { 0xab, 0xad, 0xaf, 0xb1, 0xb3, 0xb5, 0xb7, 0xb9, 0xbb, 0xbd, 0xbf };

const uint8_t BMP180_CMD_TEMP = 0x2e;
const uint8_t BMP180_DELAY_TEMP = 5;
const uint8_t BMP180_CMD_PRES[4] = { 0x34, 0x74, 0xb4, 0xf4 };
const uint8_t BMP180_DELAY_PRES[4] = { 5, 8, 14, 26 };

/**
 * @brief Initializes the BMP180 temperature/pressure sensor.
 * @param hi2c User I2C handle pointer.
 */
void BMP180_Init(I2C_HandleTypeDef *hi2c) {
	_bmp180_ui2c = hi2c;
}

/**
 * @param oss Enum, oversampling setting.
 * @note Available resolutions: BMP180_LOW, BMP180_STANDARD, BMP180_HIGH, BMP180_ULTRA.
 * @note Refer to section 3.3.1 of datasheet.
 */
void BMP180_SetOversampling(BMP180_OSS oss) {
	_bmp180_oss = oss;
}

/**
 * @brief Updates calibration data.
 * @note Must be called once before main loop.
 */
void BMP180_UpdateCalibrationData(void) {
	uint8_t result[2];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC1], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC1 =(result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC2], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC2 =(result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC3], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC3 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC4], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC4 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC5], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC5 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_AC6], (uint8_t *)result);
	_bmp180_eeprom.BMP180_AC6 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_B1], (uint8_t *)result);
	_bmp180_eeprom.BMP180_B1 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_B2], (uint8_t *)result);
	_bmp180_eeprom.BMP180_B2 = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_MB], (uint8_t *)result);
	_bmp180_eeprom.BMP180_MB = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_MC], (uint8_t *)result);
	_bmp180_eeprom.BMP180_MC = (result[0] << 8) | result[1];
	BMP180_ReadReg(BMP180_EEPROM_ADDR_MSB[BMP180_INDEX_MD], (uint8_t *)result);
	_bmp180_eeprom.BMP180_MD = (result[0] << 8) | result[1];
}

/**
 * @brief Writes to a specific register.
 * @param reg Address of register to write to.
 * @param cmd Byte to write.
 */
void BMP180_WriteReg(uint8_t reg, uint8_t cmd) {
	uint8_t arr[2] = { reg, cmd };
	HAL_I2C_Master_Transmit(_bmp180_ui2c, BMP180_I2C_ADDR << 1, arr, 2, BMP180_I2C_TIMEOUT);
}

/**
 * @brief Reads from a specific register.
 * @param reg Address of register to read from.
 * @return Byte read.
 */
uint8_t BMP180_ReadReg8(uint8_t reg) {
	HAL_I2C_Master_Transmit(_bmp180_ui2c, BMP180_I2C_ADDR << 1, &reg, 1, BMP180_I2C_TIMEOUT);
	uint8_t result;
	HAL_I2C_Master_Receive(_bmp180_ui2c, BMP180_I2C_ADDR << 1, &result, 1, BMP180_I2C_TIMEOUT);
	return result;
}


/**
 * @brief Reads from a specific register.
 * @param reg Address of register to read from.
 * @return Byte read.
 */
void BMP180_ReadReg(uint8_t reg, uint8_t *result) {
	HAL_I2C_Master_Transmit(_bmp180_ui2c, BMP180_I2C_ADDR << 1, &reg, 1, BMP180_I2C_TIMEOUT);
	HAL_I2C_Master_Receive(_bmp180_ui2c, BMP180_I2C_ADDR << 1, (uint8_t*)result, 2, BMP180_I2C_TIMEOUT);
}

/**
 * @brief Measures and calculates temperature.
 * @return Temperature in 0.1 (1/10) degrees Celsius.
 */
int32_t BMP180_GetRawTemperature(void) {
	BMP180_WriteReg(BMP180_CONTROL_REG, BMP180_CMD_TEMP);
	HAL_Delay(BMP180_DELAY_TEMP);
	uint8_t result[2];
	BMP180_ReadReg(BMP180_MSB_REG, (uint8_t *)result);
	int32_t ut = (result[0] << 8) | result[1];
	int32_t x1 = (ut - _bmp180_eeprom.BMP180_AC6) * _bmp180_eeprom.BMP180_AC5 / (1 << 15);
	int32_t x2 = (_bmp180_eeprom.BMP180_MC * (1 << 11)) / (x1 + _bmp180_eeprom.BMP180_MD);
	int32_t b5 = x1 + x2;
	return (b5 + 8) / (1 << 4);
}

/**
 * @brief Measures and calculates temperature.
 * @return Temperature in degrees Celsius.
 */
float BMP180_GetTemperature(void) {
	int32_t temp = BMP180_GetRawTemperature();
	return temp / 10.0;
}

/**
 * @brief Measures and calculates pressure.
 * @return Pressure in Pascal(Pa).
 */
int32_t BMP180_GetPressure(void) {
	BMP180_WriteReg(BMP180_CONTROL_REG, BMP180_CMD_TEMP);
	HAL_Delay(BMP180_DELAY_TEMP);
	int32_t ut = BMP180_GetUT();
	BMP180_WriteReg(BMP180_CONTROL_REG, BMP180_CMD_PRES[_bmp180_oss]);
	HAL_Delay(BMP180_DELAY_PRES[_bmp180_oss]);
	int32_t up = BMP180_GetUP();
	int32_t x1 = (ut - _bmp180_eeprom.BMP180_AC6) * _bmp180_eeprom.BMP180_AC5 / (1 << 15);
	int32_t x2 = (_bmp180_eeprom.BMP180_MC * (1 << 11)) / (x1 + _bmp180_eeprom.BMP180_MD);
	int32_t b5 = x1 + x2;
	int32_t b6 = b5 - 4000;
	x1 = (_bmp180_eeprom.BMP180_B2 * (b6 * b6 / (1 << 12))) / (1 << 11);
	x2 = _bmp180_eeprom.BMP180_AC2 * b6 / (1 << 11);
	int32_t x3 = x1 + x2;
	int32_t b3 = (((_bmp180_eeprom.BMP180_AC1 * 4 + x3) << _bmp180_oss) + 2) / 4;
	x1 = _bmp180_eeprom.BMP180_AC3 * b6 / (1 << 13);
	x2 = (_bmp180_eeprom.BMP180_B1 * (b6 * b6 / (1 << 12))) / (1 << 16);
	x3 = ((x1 + x2) + 2) / 4;
	uint32_t b4 = _bmp180_eeprom.BMP180_AC4 * (uint32_t) (x3 + 32768) / (1 << 15);
	uint32_t b7 = ((uint32_t) up - b3) * (50000 >> _bmp180_oss);
	int32_t p;
	if (b7 < 0x80000000)
		p = (b7 * 2) / b4;
	else
		p = (b7 / b4) * 2;
	x1 = (p / (1 << 8)) * (p / (1 << 8));
	x1 = (x1 * 3038) / (1 << 16);
	x2 = (-7357 * p) / (1 << 16);
	p = p + (x1 + x2 + 3791) / (1 << 4);
	return p;
}

int32_t BMP180_GetUT(void){
	uint8_t result[2];
	BMP180_ReadReg(BMP180_MSB_REG, (uint8_t *)result);
	return (result[0] << 8) | result[1];
}

int32_t BMP180_GetUP(void){
	uint8_t result1[2];
	BMP180_ReadReg(BMP180_MSB_REG, (uint8_t *)result1);
	return ((result1[0] << 16) | (result1[1] << 8) | BMP180_ReadReg8(BMP180_XLSB_REG)) >> (8 - _bmp180_oss);
}
