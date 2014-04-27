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
#include "dms.h"

#ifndef DMS_C
#define DMS_C


/* 
 * Remove a linear continuum.  Linear least squares via 
 * the book, "Numerical Recipes in C++"
 * Inputs: 
 *   X - Data matrix size [a data points x b dimensions], 
 *       modified in place to remove a linear continuum
 *   nX - Number of data points 
 *   d - Dimensionality of data point 
 *   c - Margin to use - this number of data points on 
 *      either extreme will be used to fit the line.
 * Outputs:
 *   X - modified in place to remove continuum.
 */ 
int rmctm(float **X, const int nX, const int d, const int c)
{
  int i,j;
  float a, b, ss=0, sx=0, sy=0, st2=0,t,sxoss=0;
  if (d < 1)
  {
    fprintf(stderr,"Error in continuum removal - bad dimensionality\n");
    return ERR;
  }
  if (c < 1)
  {
    fprintf(stderr,"Error in continuum removal - margin too small\n");
    return ERR;
  }
  if (c > d/2)
  {
    fprintf(stderr,"Error in continuum removal - margin too large\n");
    return ERR;
  }

  for (i=0; i<nX; i++)
  {
    st2 = 0;
    sx = 0;
    sy = 0;
    b = 0;

    /* sum x and y */
    for (j=0; j<c; j++)
    {
      sx+=j;
      sy+=X[i][j];
    }
    for (j=d-c; j<d; j++)
    {
      sx+=j;
      sy+=X[i][j];
    }

    ss = c*2; 
    sxoss = sx/ss;

    for (j=0; j<c; j++)
    {
      t = j-sxoss;
      st2 += t*t;
      b += t*X[i][j];
    }
    for (j=d-c; j<d; j++)
    {
      t = j-sxoss;
      st2 += t*t;
      b += t*X[i][j];
    }

    /* compute the best-fitting line */
    b /= st2;
    a = (sy - sx*b) / ss;
     
    /* subtract the continuum */
    for (j=0; j<d; j++)
    {
      X[i][j] -= (a + b*j);
    }
  }
  return OK;
}

/* 
 * Compute Inverse covariance matrix using Dominant Mode Supression. 
 * Inputs: 
 *   X - Data matrix size [a data points x b dimensions], 
 *       modified in place to be zero mean
 *   nX - Number of data points 
 *   d - Dimensionality of data point 
 *   e - Number of eigenvectors to use in Cinv estimation
 *   delt - Diagonal loading
 * Outputs:
 *   Cinv - Size [b x b] inverse covariance matrix
 *          Must be preallocated.
 *   m - size b vector, the mean of the original data 
 *          Must be preallocated.
 *   bad - size nX vector, a 0/1 flag indicating bad datapoints.
 *          Must be preallocated.
 *
 * Performs several operations at once:
 * 1) makes the data matrix X zero mean, modifying X in place 
 * 2) computes the inverse covariance matrix
 */

int zmInvCov(float **X, const int nX, const int d, const int e, 
        const float delt, float **Cinv, float *m, uint8_t *bad)
{
  float **CCov=NULL;
  float **eigvec=NULL;
  float *eigval=NULL;
  if (initf(&CCov, d, d, 0) == ERR || 
      vinitf(&eigval, d, 0) == ERR ||
      initf(&eigvec, d, d, 0) == ERR)
  {
    fprintf(stderr,"Error allocating memory in zmInvCov(...)\n");
    clearf(CCov, d, d);
    return ERR;
  }

  float bad_flag = 65534.0; /* anything greater is "bad" */
  int i,j,k,nm=0;

  /* find bad data values */
  for (i=0; i<nX; i++)
  {
    bad[i] = 0;
    for (j=0; j<d; j++)
    {
      if (X[i][j]>bad_flag) 
      {
        bad[i] = 1;
        break;
      }
    }
  }

  /* accumulate mean */
  for (i=0; i<nX; i++)
  {
    if (bad[i] == 0)
    {
       nm++;
       for (j=0; j<d; j++)
       {
         m[j] += X[i][j];
       }
    }
  }
  for (j=0; j<d; j++)
  {
    m[j] = m[j] / ((float) nm);
  }

  /* make X zero mean */
  for (i=0; i<nX; i++)
  {
    for (j=0; j<d; j++)
    {
      X[i][j] = X[i][j] - m[j];
    }
  }

  /* make covariance matrix of zero-meaned data */
  for (i=0; i<nX; i++)
  {
    if (bad[i] == 0)
    { 
      for (j=0; j<d; j++)
      {
        for (k=0; k<d; k++)
        {
          CCov[j][k] += X[i][j]*X[i][k];
        }
      }
    }
  }
  for (j=0; j<d; j++)
  {
    for (k=0; k<d; k++)
    {
      CCov[j][k] /= ((float) nm);
    }
  }

  /* SVD */
  if (svdcmp(CCov, d, d, eigval, eigvec) == ERR)
  {
    fprintf(stderr,"SVD error in zmInvCov(...)\n");
    clearf(CCov, d, d);
    vclearf(eigval);
    clearf(eigvec, d, d);
    return ERR;
  }

  /* mean of minor eigenvalues */
  float alpha = 0;
  for (i=e; i<d; i++)
  {
    alpha += eigval[i] / ((float)(d-e));
  }

  for (i=0; i<e; i++)
  {
    float beta = (eigval[i]-alpha)/(eigval[i]+delt);
    for (j=0; j<d; j++)
    {
      for (k=0; k<d; k++)
      {
        Cinv[j][k] = Cinv[j][k] + beta*eigvec[j][i]*eigvec[k][i];
      }
    }
  }

  for (j=0; j<d; j++)
  {
    for (k=0; k<d; k++)
    {
       float diag = (j==k);
       Cinv[j][k] = 1.0/(alpha+delt)*(diag-Cinv[j][k]);
     }
   }

  vclearf(eigval);
  clearf(eigvec, d, d);
  clearf(CCov, d, d);
  return OK;
}


/* Matched Filter detection with principal mode suppression 
 * Also returns the Mahalanobis distance of the candidate to 
 * the background.  All vector and matrix parameters should be
 * preallocated.
 * Inputs:
 *   X - data matrix [nX data points by d dimensions]
 *   nX - the number of data points
 *   d - the dimensionality of the spectra 
 *   L - a library of spectrum targets [nLib data points by d dimensions]
 *   e - the number of eigenvectors for dominant mode suppression
 *   nLib - the number of library data points
 * Outputs:
 *   mfv - vector preallocated to [nX by nLib], 
 *        filled with matched filter scores
 *   md - vector preallocated to size [nX] 
 *        filled with mahalanobis distances
 *   bad - vector preallocated to size [nX] 
 *        filled with bad data flags
 * This routine modifies X and L in place to be zero mean 
 */
int mf(float **X, const int nX, const int d, float **Lib, const int nLib, 
        const int e, const float diag, float **mfv, float *md, uint8_t *bad)
{

  /* should add parameter checking here */

  float *m = NULL;  /* mean of data matrix */
  float *t = NULL;  /* whitened matched filter target vector */
  float **Cinv = NULL; /* inverse covariance matrix */

  /* Allocate memory or die */
  if (vinitf(&m, d, 0) == ERR ||
      vinitf(&t, d, 0) == ERR ||
      initf(&Cinv, d, d, 0) == ERR)
  {
    fprintf(stderr,"Error allocating memory in mf(...)\n");
    vclearf(m);
    vclearf(t);
    clearf(Cinv, d, d);
    return ERR;
  }

  /* compute inverse covariance matrix, make X zero mean */
  if (zmInvCov(X, nX, d, e, diag, Cinv, m, bad) == ERR)
  {
    fprintf(stderr,"Error in zmInvCov\n");
    vclearf(m);
    vclearf(t);
    clearf(Cinv, d, d);
    return ERR;
  }

  /* compute mahalanobis distances */
  int i,j,k;
  for (i=0; i<nX; i++)
  {
    md[i] = 0.0;
    if (bad[i])
    {
        continue;
    }
    for (j=0; j<d; j++)
    {
      for (k=0; k<d; k++)
      {
        md[i] += X[i][j] * Cinv[j][k] * X[i][k];
      }
    }
    md[i] = sqrt(md[i]);
  } 

  /* make each L zero-mean */
  for (i=0; i<nLib; i++)
  {
    for (j=0; j<d; j++)
    {
      Lib[i][j] -= m[j];
    }
  }

  /* make background-adaptive matched filter vectors */
  for (i=0; i<nLib; i++)
  {
    float denominator = 0;
    for (j=0; j<d; j++)
    {
      for (k=0; k<d; k++)
      {
        denominator += Lib[i][j] * Cinv[j][k] * Lib[i][k];
      }
    }
    for (j=0; j<d; j++)
    {
      t[j] = 0;
      for (k=0; k<d; k++)
      {
        t[j] += Cinv[j][k] * Lib[i][k];
      }
      t[j] = t[j] / denominator;
    } 

    /* Compute dot product of each t to each data point */
    for (j=0; j<nX; j++)
    {
       mfv[j][i] = 0;

       if (bad[j])
       {
           continue;
       }
       for (k=0; k<d; k++)
       {
          mfv[j][i] += t[k] * X[j][k];
      }
    }
  }

  /* We're done */
  vclearf(m);
  vclearf(t);
  clearf(Cinv, d, d);
  return OK;
}


/* RX anomaly detection with principal mode suppression */
/* a is the number of spectra in the a x b matrix */
/* b is the number of bands in the a x b matrix */
/* modifies X in place */
int rx(float **X, const int nX, const int d,
        const int e, const float diag, float *md, uint8_t *bad)
{

  float *m = NULL;  
  float **Cinv = NULL; 
  if (vinitf(&m, d, 0) == ERR ||
      initf(&Cinv, d, d, 0) == ERR)
  {
    fprintf(stderr,"Error allocating memory in rx(...)\n");
    vclearf(m);
    clearf(Cinv, d, d);
    return ERR;
  }

  if (zmInvCov(X, nX, d, e, diag, Cinv, m, bad) == ERR)
  {
    fprintf(stderr,"Error in zmInvCov\n");
    vclearf(m);
    clearf(Cinv, d, d);
    return ERR;
  }

  int i,j,k;
  for (i=0; i<nX; i++)
  {
    md[i] = 0;
    for (j=0; j<d; j++)
    {
      for (k=0; k<d; k++)
      {
        /* X is already zero mean */
        md[i] += X[i][j] * Cinv[j][k] * X[i][k];
      }
    }
    md[i] = sqrt(md[i]);
  } 

  vclearf(m);
  clearf(Cinv, d, d);
  return OK;
}



#endif
