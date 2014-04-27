/*
 * David R. Thompson
 * Autumn 2012
 * Based on code from the LITA project with contributions from F. Calderon
 * Circa 2006
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <math.h>
#include <stdarg.h>
#include <string.h>

#ifndef DMS_COMMON_H
#define DMS_COMMON_H

#define ERR 1
#define OK 0
#define MAX_STRING 512 
#define SMAX(x,y)  (((x) > (y)) ? (x) : (y))
#define BIP_INTERLEAVE (0)
#define BIL_INTERLEAVE (1)
#define BSQ_INTERLEAVE (2)


int  newf(float*** mat, int a, int b);
int  initf(float*** mat, int a, int b, float val);
int  clearf(float **mat, int a, int b);

int  vcopyf(float *dst, float *src, int a);
int  vsubf(float*a, float *b, float *out, int n);
int  vdivf(float*a, float *b, float *out, int n);
int  vnewf(float**v , int a);
int  vinitf(float**v , int a, float val);
int  vclearf(float*v);

int  vcopyc(uint8_t *dst, uint8_t *src, int a);
int  vsubc(uint8_t*a, uint8_t *b, uint8_t *out, int n);
int  vdivc(uint8_t*a, uint8_t *b, uint8_t *out, int n);
int  vnewc(uint8_t**v , int a);
int  vinitc(uint8_t**v , int a, uint8_t val);
int  vclearc(uint8_t*v);

int  svdcmp(float **a, int m, int n, float *w, float **v);
void printmat(FILE *file, float **mat, int a, int b);
void printvec(FILE *file, float *v, int a);

void flip_endianness(float *x);
#endif

