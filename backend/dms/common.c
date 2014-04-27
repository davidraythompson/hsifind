/*
 * David R. Thompson
 * Autumn 2012
 * Based on code from the LITA project with contributions from F. Calderon
 * Circa 2006
 * TODO: test vector and matrix sizes for NaNs and Infs
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <stdarg.h>
#include <string.h>
#include "common.h"

#ifndef COMMON_C
#define COMMON_C

/* SVD functions from MFBD-LEC, institute for solar physics
 but actually I think this goes back to numerical recipes for C...*/

int vinitc(uint8_t**v , int a, uint8_t val)
{
    *v = (uint8_t *)malloc(sizeof(uint8_t)*a);
    if (v==NULL)
    {
      fprintf(stderr,"out of memory\n");
      return ERR;
    }
    int i;
    for (i=0; i<a; ++i)
    {
        (*v)[i] = val;
    }
    return OK;
}

int vnewc(uint8_t**v , int a)
{
    *v = (uint8_t *)malloc(sizeof(uint8_t)*a);
    if (v==NULL)
    {
      fprintf(stderr,"out of memory\n");
      return ERR;
    }
    return OK;
}


int vclearc(uint8_t* v)
{
    if (v!=NULL)
    {
      free(v);
    }
    return OK;
}


int vcopyc(uint8_t *dst, uint8_t *src, int a)
{
  if (src == NULL || dst == NULL)
  {
    return ERR;
  }
  int i;
  for (i=0; i<a; ++i)
  {
    dst[i] = src[i]; 
  }
  return OK;
}

int vinitf(float**v , int a, float val)
{
    *v = (float *)malloc(sizeof(float)*a);
    if (v==NULL)
    {
      fprintf(stderr,"out of memory\n");
      return ERR;
    }
    int i;
    for (i=0; i<a; ++i)
    {
        (*v)[i] = val;
    }
    return OK;
}

int vnewf(float**v , int a)
{
    *v = (float *)malloc(sizeof(float)*a);
    if (v==NULL)
    {
      fprintf(stderr,"out of memory\n");
      return ERR;
    }
    return OK;
}


int vclearf(float* v)
{
    if (v!=NULL)
    {
      free(v);
    }
    return OK;
}


int vcopyf(float *dst, float *src, int a)
{
  if (src == NULL || dst == NULL)
  {
    return ERR;
  }
  int i;
  for (i=0; i<a; ++i)
  {
    dst[i] = src[i]; 
  }
  return OK;
}


int newf(float*** mat, int a, int b){
    *mat = (float **) malloc(sizeof(float*)*a);
    if (mat == NULL)
    {
      return ERR;
    }
    (*mat)[0] = (float*) malloc(sizeof(float)*(a*b));
    if ((*mat)[0] == NULL)
    {
      free(mat);
      return ERR;
    }
    int i;
    for (i=1; i<a; ++i)
    {
        (*mat)[i] = &((*mat)[0][i*b]);
    }
    return OK;
}


int initf(float*** mat, int a, int b, float val){
    *mat = (float **) malloc(sizeof(float*)*a);
    if (mat == NULL)
    {
      return ERR;
    }
    (*mat)[0] = (float*) malloc(sizeof(float)*(a*b));
    if ((*mat)[0] == NULL)
    {
      free(mat);
      return ERR;
    }
    int i;
    for (i=0; i<(a*b); ++i)
    {
      (*mat)[0][i] = val;   
    }
    for (i=1; i<a; ++i)
    {
      (*mat)[i] = &((*mat)[0][i*b]);
    }
    return OK;
}


int clearf(float **mat, int a, int b)
{
    if (mat!=NULL)
    {
      if (mat[0]!=NULL)
      {
        free(mat[0]);
      }
      free(mat);
    }
    return OK;
}


void printvec(FILE *file, float *v, int a)
{
    int i;
    for (i=0; i<a; ++i)
    {
        fprintf(file,"%f ",v[i]);
    }
    fprintf(file,"\n");
}


void printmat(FILE *file, float **mat, int a, int b)
{
    int i,j;
    for (i=0; i<a; ++i){
        for (j=0; j<b; ++j){
            fprintf(file,"%f ",mat[i][j]);
        }
        fprintf(file,"\n");
    }
    fprintf(file,"\n");
}


double sign(const double a, const double b)
{
    return (b>=0)? ((a>=0)? a:-a) : ((a>=0)? -a:a);
}


double pythag(double a, double b) 
{
  float absa,absb;
  absa=fabs(a);
  absb=fabs(b);
  if(absa>absb)
    return absa*sqrt(1.0+(absb/absa)*(absb/absa));
  else
    return(absb==0.0)?0.0:absb*sqrt(1.0+(absa/absb)*(absa/absb));
}



int svdcmp(float **a, int m, int n, float *w, float **v)
{
  int flag, i, its, j, jj, k, l=0, nm=0; 
  float c, f, h, s, x, y, z;
  float anorm = 0.0, g = 0.0, scale = 0.0;
  float *rv1;
  
  if (m < n) 
  {
      fprintf(stderr, "#rows must be > #cols \n");
      return ERR;
  }
  
  rv1 = (float *)malloc((unsigned int) n*sizeof(float));

  /* Householder reduction to bidiagonal form */
  for (i = 0; i < n; i++) 
  {
      /* left-hand reduction */
      l = i + 1;
      rv1[i] = scale * g;
      g = s = scale = 0.0;
      if (i < m) 
      {
          for (k = i; k < m; k++) 
              scale += fabs((float)a[k][i]);
          if (scale) 
          {
              for (k = i; k < m; k++) 
              {
                  a[k][i] = (float)((float)a[k][i]/scale);
                  s += ((float)a[k][i] * (float)a[k][i]);
              }
              f = (float)a[i][i];
              g = -sign(sqrt(s), f);
              h = f * g - s;
              a[i][i] = (float)(f - g);
              if (i != n - 1) 
              {
                  for (j = l; j < n; j++) 
                  {
                      for (s = 0.0, k = i; k < m; k++) 
                          s += ((float)a[k][i] * (float)a[k][j]);
                      f = s / h;
                      for (k = i; k < m; k++) 
                          a[k][j] += (float)(f * (float)a[k][i]);
                  }
              }
              for (k = i; k < m; k++) 
                  a[k][i] = (float)((float)a[k][i]*scale);
          }
      }
      w[i] = (float)(scale * g);
  
      /* right-hand reduction */
      g = s = scale = 0.0;
      if (i < m && i != n - 1) 
      {
          for (k = l; k < n; k++) 
              scale += fabs((float)a[i][k]);
          if (scale) 
          {
              for (k = l; k < n; k++) 
              {
                  a[i][k] = (float)((float)a[i][k]/scale);
                  s += ((float)a[i][k] * (float)a[i][k]);
              }
              f = (float)a[i][l];
              g = -sign(sqrt(s), f);
              h = f * g - s;
              a[i][l] = (float)(f - g);
              for (k = l; k < n; k++) 
                  rv1[k] = (float)a[i][k] / h;
              if (i != m - 1) 
              {
                  for (j = l; j < m; j++) 
                  {
                      for (s = 0.0, k = l; k < n; k++) 
                          s += ((float)a[j][k] * (float)a[i][k]);
                      for (k = l; k < n; k++) 
                          a[j][k] += (float)(s * rv1[k]);
                  }
              }
              for (k = l; k < n; k++) 
                  a[i][k] = (float)((float)a[i][k]*scale);
          }
      }
      anorm = SMAX(anorm, (fabs((float)w[i]) + fabs(rv1[i])));
  }
  
  /* accumulate the right-hand transformation */
  for (i = n - 1; i >= 0; i--) 
  {
      if (i < n - 1) 
      {
          if (g) 
          {
              for (j = l; j < n; j++)
                  v[j][i] = (float)(((float)a[i][j] / (float)a[i][l]) / g);
                  /* float division to avoid underflow */
              for (j = l; j < n; j++) 
              {
                  for (s = 0.0, k = l; k < n; k++) 
                      s += ((float)a[i][k] * (float)v[k][j]);
                  for (k = l; k < n; k++) 
                      v[k][j] += (float)(s * (float)v[k][i]);
              }
          }
          for (j = l; j < n; j++) 
              v[i][j] = v[j][i] = 0.0;
      }
      v[i][i] = 1.0;
      g = rv1[i];
      l = i;
  }
  
  /* accumulate the left-hand transformation */
  for (i = n - 1; i >= 0; i--) 
  {
      l = i + 1;
      g = (float)w[i];
      if (i < n - 1) 
          for (j = l; j < n; j++) 
              a[i][j] = 0.0;
      if (g) 
      {
          g = 1.0 / g;
          if (i != n - 1) 
          {
              for (j = l; j < n; j++) 
              {
                  for (s = 0.0, k = l; k < m; k++) 
                      s += ((float)a[k][i] * (float)a[k][j]);
                  f = (s / (float)a[i][i]) * g;
                  for (k = i; k < m; k++) 
                      a[k][j] += (float)(f * (float)a[k][i]);
              }
          }
          for (j = i; j < m; j++) 
              a[j][i] = (float)((float)a[j][i]*g);
      }
      else 
      {
          for (j = i; j < m; j++) 
              a[j][i] = 0.0;
      }
      ++a[i][i];
  }

  /* diagonalize the bidiagonal form */
  for (k = n - 1; k >= 0; k--) 
  {                             /* loop over singular values */
      for (its = 0; its < 30; its++) 
      {                         /* loop over allowed iterations */
          flag = 1;
          for (l = k; l >= 0; l--) 
          {                     /* test for splitting */
              nm = l - 1;
              if (fabs(rv1[l]) + anorm == anorm) 
              {
                  flag = 0;
                  break;
              }
              if (fabs((float)w[nm]) + anorm == anorm) 
                  break;
          }
          if (flag) 
          {
              c = 0.0;
              s = 1.0;
              for (i = l; i <= k; i++) 
              {
                  f = s * rv1[i];
                  if (fabs(f) + anorm != anorm) 
                  {
                      g = (float)w[i];
                      h = pythag(f, g);
                      w[i] = (float)h; 
                      h = 1.0 / h;
                      c = g * h;
                      s = (- f * h);
                      for (j = 0; j < m; j++) 
                      {
                          y = (float)a[j][nm];
                          z = (float)a[j][i];
                          a[j][nm] = (float)(y * c + z * s);
                          a[j][i] = (float)(z * c - y * s);
                      }
                  }
              }
          }
          z = (float)w[k];
          if (l == k) 
          {                  /* convergence */
              if (z < 0.0) 
              {              /* make singular value nonnegative */
                  w[k] = (float)(-z);
                  for (j = 0; j < n; j++) 
                      v[j][k] = (-v[j][k]);
              }
              break;
          }
          if (its >= 30) {
              free((void*) rv1);
              fprintf(stderr, "No convergence after 30,000! iterations \n");
              return ERR;
          }
  
          /* shift from bottom 2 x 2 minor */
          x = (float)w[l];
          nm = k - 1;
          y = (float)w[nm];
          g = rv1[nm];
          h = rv1[k];
          f = ((y - z) * (y + z) + (g - h) * (g + h)) / (2.0 * h * y);
          g = pythag(f, 1.0);
          f = ((x - z) * (x + z) + h * ((y / (f + sign(g, f))) - h)) / x;
        
          /* next QR transformation */
          c = s = 1.0;
          for (j = l; j <= nm; j++) 
          {
              i = j + 1;
              g = rv1[i];
              y = (float)w[i];
              h = s * g;
              g = c * g;
              z = pythag(f, h);
              rv1[j] = z;
              c = f / z;
              s = h / z;
              f = x * c + g * s;
              g = g * c - x * s;
              h = y * s;
              y = y * c;
              for (jj = 0; jj < n; jj++) 
              {
                  x = (float)v[jj][j];
                  z = (float)v[jj][i];
                  v[jj][j] = (float)(x * c + z * s);
                  v[jj][i] = (float)(z * c - x * s);
              }
              z = pythag(f, h);
              w[j] = (float)z;
              if (z) 
              {
                  z = 1.0 / z;
                  c = f * z;
                  s = h * z;
              }
              f = (c * g) + (s * y);
              x = (c * y) - (s * g);
              for (jj = 0; jj < m; jj++) 
              {
                  y = (float)a[jj][j];
                  z = (float)a[jj][i];
                  a[jj][j] = (float)(y * c + z * s);
                  a[jj][i] = (float)(z * c - y * s);
              }
          }
          rv1[l] = 0.0;
          rv1[k] = f;
          w[k] = (float)x;
      }
  }
  free((void*) rv1);
  return OK;
}


void flip_endianness(float *x)
{
   float flipped; 
   char *orig = (char *) x; 
   char *flip =  (char *) &flipped;
   flip[0] = orig[3];
   flip[1] = orig[2];
   flip[2] = orig[1];
   flip[3] = orig[0];
   (*x) = flipped;
}
#endif
