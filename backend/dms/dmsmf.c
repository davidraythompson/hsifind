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
#include "common.h"
#include "dms.h"

#ifndef DMSRX_C
#define DMSRX_C

void usage(char *name){
  fprintf(stderr, " %s [OPTIONS] <input> <library> <output> [dfile]\n",name);
  fprintf(stderr, " Do matched filter detection on image <input>\n"); 
  fprintf(stderr, "  with a given library. Write result to <output>.\n"); 
  fprintf(stderr, "  The optional <dfile> output holds mahalanobis \n");
  fprintf(stderr, "  distances for anomaly detection or false alarm.\n");
  fprintf(stderr, "  mitigation.  By default, both <output> and <dfile> \n");
  fprintf(stderr, "  are binary files comprised of 4-byte little-endian \n");
  fprintf(stderr, "  Floating point values.  Similarly, <image> and \n");
  fprintf(stderr, "  <library> use 4-byte floating point values, with BIP\n");
  fprintf(stderr, "  interleave.  Certain options can allow the code to\n");
  fprintf(stderr, "  accept different input formats, but the output is always\n");
  fprintf(stderr, "  the same.\n");
  fprintf(stderr, "\n");
  fprintf(stderr, " OPTIONS:\n"); 
  fprintf(stderr, " -i <int> <int>  band interval (zero-indexed, inclusive).\n");
  fprintf(stderr, " -c <int>        linear continuum fit, N periphery bands.\n");
  fprintf(stderr, " -b <int>        specify number of bands.\n");
  fprintf(stderr, " -e <int>        number of eigenvectors estimated.\n");
  fprintf(stderr, " -f <float>      covariance matrix diagonal loading.\n");
  fprintf(stderr, " -s <int>        BSQ interleave, w/ <int> samples per line.\n");
  fprintf(stderr, " -l <int>        BIL interleave, w/ <int> samples per line.\n");
  fprintf(stderr, " -S <int>        spectral subsampling factor (default = 1)\n");
  fprintf(stderr, " -B              input data is big-endian.\n");
  fprintf(stderr, " -h              print this message.\n");
  fprintf(stderr, "\n");
  fprintf(stderr, "References:\n");
  fprintf(stderr, "  D. Manolakis et al., Imaging Spectroscopy XIV, 2009\n");
  fprintf(stderr, "  R. S. DiPietro et al., Opt. Eng. 51(1), 2012\n");
  exit(-1);
}



int main(int argc, char** argv){

  /* default values */
  int nbands = 0;
  int ninterval = 0;
  int nspec = 0;
  int nlib = 0;
  int nskip = 1, nsubs = 0;
  int ncontinuum = 0;
  int min_band = 0;
  int max_band = 0;
  int big_endian = 0;
  int nsamps = 0, nlines = 0;
  float diag = 0.001;
  int i,j,k,e = 15;
  int interleave = BIP_INTERLEAVE;
  char *infname=NULL, *libfname=NULL, *outfname=NULL, *mdfname=NULL;
  FILE *inf=NULL, *libf=NULL, *outf=NULL, *mdf=NULL;
  float **X=NULL, **L=NULL, **MFV=NULL, *MD=NULL;
  float **Xi=NULL, **Li=NULL, **XiS=NULL, **LiS=NULL;
  uint8_t *bad = NULL;

  /* parse input */
  int arg=1;
  while(arg<argc){
    if (argv[arg][0]=='-'){
      if (nspec>0)
      {
        usage(argv[0]);
      }
      switch (argv[arg][1]){
        case 'h': 
          usage(argv[0]);
          break;
        case 'B': 
          big_endian = 1;
          break;
        case 'd':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          diag = atof(argv[arg]);
          break;
        case 'e':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          e = atoi(argv[arg]);
          break;
        case 'b':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nbands = atoi(argv[arg]);
          break;
        case 'c':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          ncontinuum = atoi(argv[arg]);
          break;
        case 'i':
          if (arg+2 >= argc)
          {
            usage(argv[0]);
          }
          arg++;
          min_band = atoi(argv[arg]);
          arg++;
          max_band = atoi(argv[arg]);
          break;
        case 's':
          interleave = BSQ_INTERLEAVE;
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nsamps = atoi(argv[arg]);
          break;
        case 'l':
          interleave = BIL_INTERLEAVE;
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nsamps = atoi(argv[arg]);
          break;
        case 'S':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nskip = atoi(argv[arg]);
          break;
      }
    }
    else if (infname == NULL)
    {
        infname = argv[arg];
    }
    else if (libfname == NULL)
    {
        libfname = argv[arg];
    }
    else if (outfname == NULL)
    {
        outfname = argv[arg];
    }
    else if (mdfname == NULL)
    {
        mdfname = argv[arg];
    }
    arg++;
  }

  if (outfname == NULL)
  {
    usage(argv[0]);
  }
  
  if (min_band > max_band || max_band >= nbands)
  {
    fprintf(stderr,"Bad band interval!\n");
    usage(argv[0]);
  }

  /* get the number of bands in the used spectral region */
  if (min_band == 0 && max_band == 0)
  {
     min_band = 0;
     max_band = nbands-1;
  }
  ninterval = max_band-min_band+1;

  /* open files for I/O */             
  inf = fopen(infname, "rb");
  if (inf == NULL)
  {
     fprintf(stderr,"Cannot open file %s\n", infname);
     exit(-1); 
  }
  libf = fopen(libfname, "rb");
  if (libf == NULL)
  {
     fprintf(stderr,"Cannot open file %s\n", libfname);
     fclose(inf);
     exit(-1); 
  }
  outf = fopen(outfname, "wb");
  if (outf == NULL)
  {
     fprintf(stderr,"Cannot open file %s\n", outfname);
     fclose(inf);
     fclose(libf);
     exit(-1); 
  }
  if (mdfname != NULL)
  {
    mdf = fopen(mdfname, "wb");
    if (mdf == NULL)
    {
       fprintf(stderr,"Cannot open file %s\n", mdfname);
       fclose(inf);
       fclose(libf);
       fclose(outf);
       exit(-1); 
    }
  }
  fprintf(stderr,"Here we go!\n");

  /* use file sizes to get number of data points */
  fseek(inf, 0, SEEK_END);
  nspec = ftell(inf) / (sizeof(float)*nbands);
  rewind(inf);
  fseek(libf, 0, SEEK_END);
  nlib = ftell(libf) / (sizeof(float)*nbands);
  rewind(libf);

  /* allocate memory */
  newf(&Xi, nspec, ninterval);
  newf(&Li, nspec, ninterval);
  newf(&MFV, nspec, nlib);
  vnewf(&MD, nspec);
  vnewc(&bad, nspec);

  /* read input, transpose to BIP if needed */
  switch (interleave)
  {
    case BIP_INTERLEAVE:
      newf(&X, nspec, nbands);
      fread(&(X[0][0]), sizeof(float), nspec*nbands, inf);
      for (i=0; i<nspec; i++)
        for (j=0; j<ninterval; j++)
          Xi[i][j] = X[i][j+min_band];
      clearf(X, nspec, nbands);
      break;
    case BIL_INTERLEAVE:
      nlines = nspec/nsamps;
      newf(&X, nlines*nbands, nsamps);
      fread(&(X[0][0]), sizeof(float), nspec*nbands, inf);
      for (i=0; i<nlines; i++)
        for (j=0; j<ninterval; j++)
          for (k=0; k<nsamps; k++)
            Xi[i*nsamps+k][j] = X[i*nbands+(j+min_band)][k];
      clearf(X, nlines*nbands, nsamps);
      break;
    case BSQ_INTERLEAVE:
      nlines = nspec/nsamps;
      newf(&X, nbands, nsamps*nlines);
      fread(&(X[0][0]), sizeof(float), nspec*nbands, inf);
      for (i=0; i<ninterval; i++)
        for (j=0; j<nlines; j++)
          for (k=0; k<nsamps; k++)
            Xi[j*nsamps+k][i] = X[i+min_band][j*nsamps+k];
      clearf(X, nbands, nsamps*nlines);
      break;
  }
  fclose(inf);

  /* swap endianness if needed */
  if (big_endian)
    for (i=0; i<nspec; i++)
        for (j=0; j<ninterval; j++)
            flip_endianness(&(Xi[i][j]));

  /* read library */
  newf(&L, nspec, nbands);
  fread(&(L[0][0]), sizeof(float), nlib*nbands, libf);
  for (i=0; i<nlib; i++)
    for (j=0; j<ninterval; j++)
      Li[i][j] = L[i][j+min_band];
  fclose(libf);
  clearf(L, nspec, nbands);

  /* remove continuum, if needed */
  if (ncontinuum>0)
  {
     rmctm(Li, nspec, ninterval, ncontinuum); 
     rmctm(Xi, nspec, ninterval, ncontinuum); 
  }

  /* matched filter detection */
  if (nskip>1)
  {
    /* spectral binning for speed.  Accumulate arrays. */
    nsubs = ninterval/nskip;
    newf(&LiS, nlib, nsubs);
    for (i=0; i<nlib; i++) 
    {
      for (j=0; j<nsubs; j++)
      {
        LiS[i][j] = 0;
        for (k=0; k<nskip; k++)
        {
          LiS[i][j] = Li[i][j*nskip+k] / ((float)(nskip));
        }
      }
    }
    newf(&XiS, nspec, nsubs);
    for (i=0; i<nspec; i++) 
    {
      for (j=0; j<nsubs; j++)
      {
        XiS[i][j] = 0;
        for (k=0; k<nskip; k++)
        {
          XiS[i][j] = Xi[i][j*nskip+k] / ((float)(nskip));
        }
      }
    }
    mf(XiS, nspec, nsubs, LiS, nlib, e, diag, MFV, MD, bad);
    clearf(LiS,nlib,nsubs);
    clearf(XiS,nspec,nsubs);
  }
  else
  {
    /* matched filter detection on original array */
    mf(Xi, nspec, ninterval, Li, nlib, e, diag, MFV, MD, bad);
  }

  /* write output - matched filter result */
  fwrite(&(MFV[0][0]), sizeof(float), nspec*nlib, outf);
  fclose(outf);

  /* write output - mahalanobis distance result*/
  if (mdf != NULL)
  {
    fwrite(&(MD[0]), sizeof(float), nspec, mdf);
    fclose(mdf);
  }
    
  /* clean up */
  clearf(Xi,nspec,ninterval);
  clearf(Li,nlib,ninterval);
  clearf(MFV,nspec,nlib);
  vclearf(MD);
  vclearc(bad);
  return 1;
}


#endif










