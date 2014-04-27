/*=================================================================
 * David R. Thompson
 * Autumn 2012
 *=================================================================*/

#include <stdio.h>
#include <string.h>
#include <math.h>
#include "mex.h"
#include "common.h"
#include "dms.h"
 
/* mexFunction is the gateway routine for the MEX-file. */ 
void
mexFunction( int nlhs, mxArray *plhs[],
             int nrhs, const mxArray *prhs[] )
{
  int i, r, c, Xrows, Xcols, Lrows, Lcols;
  float **mfv, **X, **L, *inData, *inLib, *outData, *outMd;
  (void) nlhs;     /* unused parameters */
  (void) plhs;
  const mwSize *dims;
  mwSize number_of_dimensions;
  mxClassID  category;

/* Check to see if we are on a platform that does not support the compatibility layer. */
#if defined(_LP64) || defined (_WIN64)
#ifdef MX_COMPAT_32
  for (i=0; i<nrhs; i++)  {
      if (mxIsSparse(prhs[i])) {
          mexErrMsgIdAndTxt("MATLAB:explore:NoSparseCompat",
                    "MEX-files compiled on a 64-bit platform that use sparse array functions need to be compiled using -largeArrayDims.");
      }
  }
#endif
#endif

  /* check inputs */
  if (nrhs != 2) 
  {
    fprintf(stderr,"I need 2 inputs\n");
    return;
  }
  if (mxGetNumberOfDimensions(prhs[0]) != 2)
  {
    mexPrintf("usage: mf(X,L), where each row of X is a spectrum\n");
    return;
  }
  if (mxGetNumberOfDimensions(prhs[1]) != 2)
  {
    mexPrintf("usage: mf(X,L), where each row of L is a spectrum\n");
    return;
  }
  category = mxGetClassID(prhs[0]);
  if (category != mxSINGLE_CLASS)
  {
    mexPrintf("The data matrix must have type 'single'\n");
    return;
  }
  category = mxGetClassID(prhs[1]);
  if (category != mxSINGLE_CLASS)
  {
    mexPrintf("The library matrix must have type 'single'\n");
    return;
  }
  
  /* Get input dimensions */
  dims = mxGetDimensions(prhs[0]);
  Xrows = dims[0];
  Xcols = dims[1];
  dims = mxGetDimensions(prhs[1]);
  Lrows = dims[0];
  Lcols = dims[1];
        
  if (Lcols != Xcols)
  {
    mexPrintf("Dimension mismatch between library and data\n");
    return;
  }
  
  inData = (float *) mxGetData(prhs[0]);
  inLib = (float *)  mxGetData(prhs[1]);

  /* build data arrays. do MF detection, clean up */
  newf(&X, Xrows, Xcols);
  newf(&L, Lrows, Lcols);
  initf(&mfv, Xrows, Lrows, 0);
  
  /* Copy matlab input arrays into X and L */
  for (r=0; r<Xrows; r++)
  {
    for (c=0; c<Xcols; c++)
    {
      X[r][c] = inData[c*Xrows+r];
    }
  }
  for (r=0; r<Lrows; r++)
  {
    for (c=0; c<Lcols; c++)
    {
      L[r][c] = inLib[c*Lrows+r];
    }
  }
  
  /* create space for output */
  outData = (float *) mxCalloc(Xrows*Lrows, sizeof(float));
  outMd = (float *) mxCalloc(Xrows, sizeof(float));
  
  /* call the library function for matched filter detection */
  mf(X, Xrows, Xcols, L, Lrows, NEVALS, DIAG, mfv, outMd);
  
  /* copy into the output array */
  for (r=0; r<Xrows; r++)
  {
    for (c=0; c<Lrows; c++)
    {
      outData[c*Xrows+r] = mfv[r][c];
    }
  }
  
  /* clean up */
  clearf(X, Xrows, Xcols);
  clearf(L, Lrows, Lcols);
  clearf(mfv, Xrows, Lrows);

  /* create output structure */
  plhs[0] = mxCreateNumericMatrix(0, 0, mxSINGLE_CLASS, mxREAL);
  mxSetData(plhs[0], outData);
  mxSetM(plhs[0], Xrows);
  mxSetN(plhs[0], Lrows);
  
  if (nlhs > 1) 
  {
    plhs[1] = mxCreateNumericMatrix(0, 0, mxSINGLE_CLASS, mxREAL);
    mxSetData(plhs[1], outMd);
    mxSetM(plhs[1], Xrows);
    mxSetN(plhs[1], 1);
  }
  else
  {
    mxFree(outMd);
  }
}

