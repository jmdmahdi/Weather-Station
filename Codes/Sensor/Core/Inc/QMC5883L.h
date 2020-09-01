#ifndef QMC5883L_H
#define QMC5883L_H

#include "stm32f1xx_hal.h"
#include "math.h"

void QMC5883L_Init();
void QMC5883L_Sleep();
void QMC5883L_Reset();
int QMC5883L_Ready();
void QMC5883L_Reconfig();

int QMC5883L_Read_Heading();
int QMC5883L_ReadRaw(int16_t *x, int16_t *y, int16_t *z);

void QMC5883L_Reset_Calibration();

void QMC5883L_Set_Sampling_Rate(int rate);
void QMC5883L_Set_Range(int range);
void QMC5883L_Set_Oversampling(int ovl);

int16_t xhigh, xlow;
int16_t yhigh, ylow;
uint8_t addr;
uint8_t mode;
uint8_t rate;
uint8_t range;
uint8_t oversampling;

#endif
