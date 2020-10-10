#include "QMC5883L.h"

/* The default I2C address of this chip */
#define QMC5883L_ADDR 0x0D<<1

/* Register numbers */
#define QMC5883L_X_LSB 0
#define QMC5883L_X_MSB 1
#define QMC5883L_Y_LSB 2
#define QMC5883L_Y_MSB 3
#define QMC5883L_Z_LSB 4
#define QMC5883L_Z_MSB 5
#define QMC5883L_STATUS 6
#define QMC5883L_TEMP_LSB 7
#define QMC5883L_TEMP_MSB 8
#define QMC5883L_CONFIG 9
#define QMC5883L_CONFIG2 10
#define QMC5883L_RESET 11
#define QMC5883L_RESERVED 12
#define QMC5883L_CHIP_ID 13

/* Bit values for the STATUS register */
#define QMC5883L_STATUS_DRDY 1
#define QMC5883L_STATUS_OVL 2
#define QMC5883L_STATUS_DOR 4

/* Oversampling values for the CONFIG register */
#define QMC5883L_CONFIG_OS512 0b00000000
#define QMC5883L_CONFIG_OS256 0b01000000
#define QMC5883L_CONFIG_OS128 0b10000000
#define QMC5883L_CONFIG_OS64  0b11000000

/* Range values for the CONFIG register */
#define QMC5883L_CONFIG_2GAUSS 0b00000000
#define QMC5883L_CONFIG_8GAUSS 0b00010000

/* Rate values for the CONFIG register */
#define QMC5883L_CONFIG_10HZ   0b00000000
#define QMC5883L_CONFIG_50HZ   0b00000100
#define QMC5883L_CONFIG_100HZ  0b00001000
#define QMC5883L_CONFIG_200HZ  0b00001100

/* Mode values for the CONFIG register */
#define QMC5883L_CONFIG_STANDBY 0b00000000
#define QMC5883L_CONFIG_CONT    0b00000001

/* Apparently PI isn't available in all environments. */
#ifndef PI
#define PI 3.14159265358979323846264338327950288
#endif

I2C_HandleTypeDef *QMC5883L_i2c;

void QMC5883L_Write_Register(uint16_t reg, int value) {
	HAL_I2C_Mem_Write(QMC5883L_i2c, QMC5883L_ADDR, reg, 1, (uint8_t*) value, 1,
			100);
}

void QMC5883L_Read_Register(uint8_t *data, uint16_t reg, uint16_t count) {
	HAL_I2C_Mem_Read(QMC5883L_i2c, QMC5883L_ADDR, reg, 1, data, count, 100);
}

void QMC5883L_Reconfig() {
	QMC5883L_Write_Register(QMC5883L_CONFIG,
			oversampling | range | rate | mode);
}

void QMC5883L_Reset() {
	QMC5883L_Write_Register(QMC5883L_RESET, 0x01);
	QMC5883L_Reconfig();
}

void QMC5883L_Set_Oversampling(int x) {
	switch (x) {
	case 512:
		oversampling = QMC5883L_CONFIG_OS512;
		break;
	case 256:
		oversampling = QMC5883L_CONFIG_OS256;
		break;
	case 128:
		oversampling = QMC5883L_CONFIG_OS128;
		break;
	case 64:
		oversampling = QMC5883L_CONFIG_OS64;
		break;
	}
	QMC5883L_Reconfig();
}

void QMC5883L_Set_Range(int x) {
	switch (x) {
	case 2:
		range = QMC5883L_CONFIG_2GAUSS;
		break;
	case 8:
		range = QMC5883L_CONFIG_8GAUSS;
		break;
	}
	QMC5883L_Reconfig();
}

void QMC5883L_Set_Sampling_Rate(int x) {
	switch (x) {
	case 10:
		rate = QMC5883L_CONFIG_10HZ;
		break;
	case 50:
		rate = QMC5883L_CONFIG_50HZ;
		break;
	case 100:
		rate = QMC5883L_CONFIG_100HZ;
		break;
	case 200:
		rate = QMC5883L_CONFIG_200HZ;
		break;
	}
	QMC5883L_Reconfig();
}

void QMC5883L_Init(I2C_HandleTypeDef *i2c) {
	QMC5883L_i2c = i2c;
	/* This assumes the wire library has been initialized. */
	addr = QMC5883L_ADDR;
	oversampling = QMC5883L_CONFIG_OS512;
	range = QMC5883L_CONFIG_2GAUSS;
	rate = QMC5883L_CONFIG_50HZ;
	mode = QMC5883L_CONFIG_STANDBY;
	QMC5883L_Reset();
}

void QMC5883L_Sleep() {
	mode = QMC5883L_CONFIG_STANDBY;
	QMC5883L_Reset();
}

int QMC5883L_Ready() {
	uint8_t data;
	QMC5883L_Read_Register(&data, QMC5883L_STATUS, 1);
	if (!data)
		return 0;
	return data & QMC5883L_STATUS_DRDY;
}

int QMC5883L_ReadRaw(int16_t *x, int16_t *y, int16_t *z) {
	mode = QMC5883L_CONFIG_CONT;
	QMC5883L_Reset();
	while (!QMC5883L_Ready()) {
	}

	uint8_t data[6];

	QMC5883L_Read_Register(data, QMC5883L_X_LSB, 6);

	*x = data[0] | (data[1] << 8);
	*y = data[2] | (data[3] << 8);
	*z = data[4] | (data[5] << 8);

	return 1;
}

void QMC5883L_Reset_Calibration() {
	xhigh = yhigh = 0;
	xlow = ylow = 0;
}

int QMC5883L_Read_Heading() {
	int16_t x, y, z;

	if (!QMC5883L_ReadRaw(&x, &y, &z))
		return 0;

	/* Update the observed boundaries of the measurements */

	if (x < xlow)
		xlow = x;
	if (x > xhigh)
		xhigh = x;
	if (y < ylow)
		ylow = y;
	if (y > yhigh)
		yhigh = y;

	/* Bail out if not enough data is available. */

	if (xlow == xhigh || ylow == yhigh)
		return 0;

	/* Recenter the measurement by subtracting the average */

	x -= (xhigh + xlow) / 2;
	y -= (yhigh + ylow) / 2;

	/* Rescale the measurement to the range observed. */

	float fx = (float) x / (xhigh - xlow);
	float fy = (float) y / (yhigh - ylow);

	int heading = 180.0 * atan2(fy, fx) / M_PI;
	if (heading <= 0)
		heading += 360;

	return heading;
}
