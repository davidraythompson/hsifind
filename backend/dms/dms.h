/*
 * David R. Thompson
 * Autumn 2012
 * Based on code from the LITA project with contributions from F. Calderon
 * Circa 2006
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <stdarg.h>
#include <string.h>
#include "common.h"

#ifndef DMS_H
#define DMS_H

/* Number of eigenvalues used by default */
#define NEVALS (12)
#define DIAG   (0.01)

int zmInvCov(float **X, const int nX, const int d, const int e, 
        const float diag, float **Cinv, float *m, uint8_t *bad);
int rx(float **X, const int nX, const int d, const int e,
        const float diag, float *w, uint8_t *bad);
int mf(float **X, const int nX, const int d, float **Lib, const int nLib, 
        const int e, const float diag, float **mf, float *md, uint8_t *bad);
int rmctm(float **X, const int nX, const int d, const int c);

#endif

