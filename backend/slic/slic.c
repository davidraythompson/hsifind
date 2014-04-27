/*
 * David R. Thompson
 * Winter 2013
 * 
 * Based on slic.c with the following copyright statement:
 * Copyright (C) 2007-12 Andrea Vedaldi and Brian Fulkerson. All rights reserved.
 * This file is part of the VLFeat library and is made available under
 * the terms of the BSD license
*/


#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <stdarg.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>
#include "slic.h"

#ifndef SLIC_C
#define SLIC_C

#define VL_MIN(x,y) (((x)<(y))?(x):(y))
#define VL_MAX(x,y) (((x)>(y))?(x):(y))
#define VL_INFINITY_F 9e99


inline long int
vl_round_d (double x)
{
#ifdef VL_COMPILER_GNUC
  return __builtin_lround(x) ;
#elif VL_COMPILER_MSC
  if (x >= 0.0) {
    return floor(x + 0.5) ;
  } else {
    return ceil(x - 0.5) ;
  }
#else
  return lround(x) ;
#endif
}

/** @brief SLIC superpixel segmentation
 ** @param segmentation segmentation.
 ** @param image image to segment.
 ** @param width image width.
 ** @param height image height.
 ** @param numChannels number of image channels (depth).
 ** @param regionSize nominal size of the regions.
 ** @param regularization trade-off between appearance and spatial terms.
 ** @param minRegionSize minimum size of a segment.
 **
 ** The function computes the SLIC superpixels of the specified image @a image.
 ** @a image is a pointer to an @c width by @c height by @c by numChannles array of @c float.
 ** @a segmentation is a pointer to a @c width by @c height array of @c uint32_t.
 ** @a segmentation contain the labels of each image pixels, from 0 to
 ** the number of regions minus one.
 **
 ** @sa @ref slic-overview, @ref slic-tech
 **/

void
slic_segment (uint32_t * segmentation,
             float const * image,
             uint32_t width,
             uint32_t height,
             uint32_t numChannels,
             uint32_t regionSize,
             const float regularization,
             uint32_t minRegionSize)
{
  int i, x, y, u, v, k, region ;
  uint64_t iter ;
  uint64_t const numRegionsX = (uint64_t) ceil((double) width / regionSize) ;
  uint64_t const numRegionsY = (uint64_t) ceil((double) height / regionSize) ;
  uint64_t const numRegions = numRegionsX * numRegionsY ;
  uint64_t const numPixels = width * height ;
  float * centers ;
  float * edgeMap ;
  float previousEnergy = VL_INFINITY_F ;
  float startingEnergy ;
  uint32_t * masses ;
  uint64_t const maxNumIterations = 100 ;

  assert(segmentation) ;
  assert(image) ;
  assert(width >= 1) ;
  assert(height >= 1) ;
  assert(numChannels >= 1) ;
  assert(regionSize >= 1) ;
  assert(regularization >= 0) ;

#define atimage(x,y,k) image[(y)*width*numChannels+(x)*numChannels+(k)];
#define atEdgeMap(x,y) edgeMap[(y)*width+(x)]

  edgeMap = calloc(numPixels, sizeof(float)) ;
  masses = malloc(sizeof(uint32_t) * numPixels) ;
  centers = malloc(sizeof(float) * (2 + numChannels) * numRegions) ;

  /* compute edge map (gradient strength) */
  for (k = 0 ; k < (signed)numChannels ; ++k) {
    for (y = 1 ; y < (signed)height-1 ; ++y) {
      for (x = 1 ; x < (signed)width-1 ; ++x) {
        float a = atimage(x-1,y,k) ;
        float b = atimage(x+1,y,k) ;
        float c = atimage(x,y+1,k) ;
        float d = atimage(x,y-1,k) ;
        atEdgeMap(x,y) += (a - b)  * (a - b) + (c - d) * (c - d) ;
      }
    }
  }

  /* initialize K-means centers */
  i = 0 ;
  for (v = 0 ; v < (signed)numRegionsY ; ++v) {
    for (u = 0 ; u < (signed)numRegionsX ; ++u) {
      int xp ;
      int yp ;
      int centerx = 0;
      int centery = 0;
      float minEdgeValue = VL_INFINITY_F ;

      x = (int) vl_round_d(regionSize * (u + 0.5)) ;
      y = (int) vl_round_d(regionSize * (v + 0.5)) ;

      x = VL_MAX(VL_MIN(x, (signed)width-1),0) ;
      y = VL_MAX(VL_MIN(y, (signed)height-1),0) ;

      /* search in a 3x3 neighbourhood the smallest edge response */
      for (yp = VL_MAX(0, y-1) ; yp <= VL_MIN((signed)height-1, y+1) ; ++ yp) {
        for (xp = VL_MAX(0, x-1) ; xp <= VL_MIN((signed)width-1, x+1) ; ++ xp) {
          float thisEdgeValue = atEdgeMap(xp,yp) ;
          if (thisEdgeValue < minEdgeValue) {
            minEdgeValue = thisEdgeValue ;
            centerx = xp ;
            centery = yp ;
          }
        }
      }

      /* initialize the new center at this location */
      centers[i++] = (float) centerx ;
      centers[i++] = (float) centery ;
      for (k  = 0 ; k < (signed)numChannels ; ++k) {
        centers[i++] = atimage(centerx,centery,k) ;
      }
    }
  }

  /* run k-means iterations */
  for (iter = 0 ; iter < maxNumIterations ; ++iter) {
    float factor = regularization / (regionSize * regionSize) ;
    float energy = 0 ;

    /* assign pixels to centers */
    for (y = 0 ; y < (signed)height ; ++y) {
      for (x = 0 ; x < (signed)width ; ++x) {
        int u = floor((double)x / regionSize - 0.5) ;
        int v = floor((double)y / regionSize - 0.5) ;
        int up, vp ;
        float minDistance = VL_INFINITY_F ;

        for (vp = VL_MAX(0, v) ; vp <= VL_MIN((signed)numRegionsY-1, v+1) ; ++vp) {
          for (up = VL_MAX(0, u) ; up <= VL_MIN((signed)numRegionsX-1, u+1) ; ++up) {
            int region = up  + vp * numRegionsX ;
            float centerx = centers[(2 + numChannels) * region + 0]  ;
            float centery = centers[(2 + numChannels) * region + 1] ;
            float spatial = (x - centerx) * (x - centerx) + (y - centery) * (y - centery) ;
            float appearance = 0 ;
            float distance ;
            for (k = 0 ; k < (signed)numChannels ; ++k) {
              float centerz = centers[(2 + numChannels) * region + k + 2]  ;
              float z = atimage(x,y,k) ;
              appearance += (z - centerz) * (z - centerz) ;
            }
            /* DRT hack */
            appearance = appearance/numChannels;
            distance = appearance + factor * spatial ;
            if (minDistance > distance) {
              minDistance = distance ;
              segmentation[x + y * width] = (uint32_t)region ;
            }
          }
        }
        energy += minDistance ;
      }
    }

    /*
     VL_PRINTF("vl:slic: iter %d: energy: %g\n", iter, energy) ;
    */

    /* check energy termination conditions */
    if (iter == 0) {
      startingEnergy = energy ;
    } else {
      if ((previousEnergy - energy) < 1e-5 * (startingEnergy - energy)) {
        break ;
      }
    }
    previousEnergy = energy ;

    /* recompute centers */
    memset(masses, 0, sizeof(uint32_t) * width * height) ;
    memset(centers, 0, sizeof(float) * (2 + numChannels) * numRegions) ;

    for (y = 0 ; y < (signed)height ; ++y) {
      for (x = 0 ; x < (signed)width ; ++x) {
        int pixel = x + y * width ;
        int region = segmentation[pixel] ;
        masses[region] ++ ;
        centers[region * (2 + numChannels) + 0] += x ;
        centers[region * (2 + numChannels) + 1] += y ;
        for (k = 0 ; k < (signed)numChannels ; ++k) {
          centers[region * (2 + numChannels) + k + 2] += atimage(x,y,k) ;
        }
      }
    }

    for (region = 0 ; region < (signed)numRegions ; ++region) {
      float mass = VL_MAX(masses[region], 1e-8) ;
      for (i = (2 + numChannels) * region ;
           i < (signed)(2 + numChannels) * (region + 1) ;
           ++i) {
        centers[i] /= mass ;
      }
    }
  }

  free(masses) ;
  free(centers) ;

  /* elimiate small regions */
  {
    uint32_t * cleaned = calloc(numPixels, sizeof(uint32_t)) ;
    uint32_t * segment = malloc(sizeof(uint) * numPixels) ;
    uint64_t segmentSize ;
    uint32_t label ;
    uint32_t cleanedLabel ;
    uint64_t numExpanded ;
    int const dx [] = {+1, -1,  0,  0} ;
    int const dy [] = { 0,  0, +1, -1} ;
    int direction ;
    int pixel ;

    for (pixel = 0 ; pixel < (signed)numPixels ; ++pixel) {
      if (cleaned[pixel]) continue ;
      label = segmentation[pixel] ;
      numExpanded = 0 ;
      segmentSize = 0 ;
      segment[segmentSize++] = pixel ;

      /*
       find cleanedLabel as the label of an already cleaned
       region neihbour of this pixel
       */
      cleanedLabel = label + 1 ;
      cleaned[pixel] = label + 1 ;
      x = pixel % width ;
      y = pixel / width ;
      for (direction = 0 ; direction < 4 ; ++direction) {
        int xp = x + dx[direction] ;
        int yp = y + dy[direction] ;
        int neighbor = xp + yp * width ;
        if (0 <= xp && xp < (signed)width &&
            0 <= yp && yp < (signed)height &&
            cleaned[neighbor]) {
          cleanedLabel = cleaned[neighbor] ;
        }
      }

      /* expand the segment */
      while (numExpanded < segmentSize) {
        int open = segment[numExpanded++] ;
        x = open % width ;
        y = open / width ;
        for (direction = 0 ; direction < 4 ; ++direction) {
          int xp = x + dx[direction] ;
          int yp = y + dy[direction] ;
          int neighbor = xp + yp * width ;
          if (0 <= xp && xp < (signed)width &&
              0 <= yp && yp < (signed)height &&
              cleaned[neighbor] == 0 &&
              segmentation[neighbor] == label) {
            cleaned[neighbor] = label + 1 ;
            segment[segmentSize++] = neighbor ;
          }
        }
      }

      /* change label to cleanedLabel if the semgent is too small */
      if (segmentSize < minRegionSize) {
        while (segmentSize > 0) {
          cleaned[segment[--segmentSize]] = cleanedLabel ;
        }
      }
    }
    /* restore base 0 indexing of the regions */
    for (pixel = 0 ; pixel < (signed)numPixels ; ++pixel) cleaned[pixel] -- ;

    memcpy(segmentation, cleaned, numPixels * sizeof(uint32_t)) ;
    free(cleaned) ;
    free(segment) ;
  }
}


void get_superpixel_average(float *X, uint32_t *S, float *A, const int nrows,
        const int ncols, const int nbands)
{
    int nspec = ncols*nrows;
    int i, j, spind;
    int nspix = 0;

    /* total number of superpixels */
    for (i=0; i<nspec; i++) 
    {
        nspix = ((S[i]+1) > nspix)? (S[i]+1) : nspix;
    }

    uint32_t *nZ = malloc(sizeof(uint32_t)*nspix); /* number spectra per spixel */
    float *Z = malloc(sizeof(float)*nspix*nbands); /* holds spectrum average */

    /* averages, counts start at zero */
    for (i=0; i<nspec*nbands; i++) 
    {
        A[i] = 0.0;
    }
    for (i=0; i<nspix; i++) 
    {
        nZ[i] = 0;
        for (j=0; j<nbands; j++) 
        {
           Z[i*nbands+j] = 0.0;
        }
    }

    /* accumulate spectra */
    for (i=0; i<nspec; i++) 
    {
        spind = S[i];
        nZ[spind] = nZ[spind]+1;
        for (j=0; j<nbands; j++)
        {
            Z[spind*nbands+j] += X[i*nbands+j];
        }
    }

    /* safe averaging */
    for (i=0; i<nspix; i++) 
    {
        if (nZ[i]>0)
        {
            for (j=0; j<nbands; j++)
            {
                Z[i*nbands+j] /= ((float)(nZ[i]));
            }
        }
        else
        {
            for (j=0; j<nbands; j++)
            {
                Z[i*nbands+j] = 0;
            }
        }
    }

    /* copy superpixel averages back into the original A matrix */
    for (i=0; i<nspec; i++) 
    {
        spind = S[i];
        for (j=0; j<nbands; j++)
        {
            A[i*nbands+j] = Z[spind*nbands+j];
        }
    }
    if (nZ) free(nZ); 
    if (Z) free(Z); 
}


void usage(char *name){
  fprintf(stderr, " %s [OPTIONS] <input> <output> \n",name);
  fprintf(stderr, " Segment an BIP image <input> (floating point) into superpixels.\n"); 
  fprintf(stderr, "  Write result to <output> as an integer matrix.\n"); 
  fprintf(stderr, "\n");
  fprintf(stderr, " OPTIONS:\n"); 
  fprintf(stderr, " -r <int>         specify number of rows.\n");
  fprintf(stderr, " -c <int>         specify number of columns.\n");
  fprintf(stderr, " -b <int>         specify number of bands.\n");
  fprintf(stderr, " -a <file>        average superpixel spectra.\n");
  fprintf(stderr, " -s <float>       spatial regularizer (default 0.001).\n");
  fprintf(stderr, " -h               print this message.\n");
  fprintf(stderr, "\n");
  exit(-1);
}



int main(int argc, char** argv){

  /* default values */
  int nbands = 0, nrows=0, ncols=0;
  int nspec = 0;
  char *infname=NULL, *outfname=NULL, *avgfname=NULL;
  float *X=NULL; 
  uint32_t *S=NULL; 
  int regionSize = 10;
  int minRegionSize = 10;
  float regularization = 0.001;

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
        case 's':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          regularization = atof(argv[arg]);
          break;
        case 'b':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nbands = atoi(argv[arg]);
          break;
        case 'r':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          nrows = atoi(argv[arg]);
          break;
        case 'c':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          ncols = atoi(argv[arg]);
          break;
        case 'a':
          arg++;
          if (arg >= argc)
          {
            usage(argv[0]);
          }
          avgfname = argv[arg];
          break;
        default:
          fprintf(stderr,"unknown option %s\n",argv[arg]);
          break;
      }
    }
    else if (infname == NULL)
    {
        infname = argv[arg];
    }
    else if (outfname == NULL)
    {
        outfname = argv[arg];
    }
    arg++;
  }

  if (nrows<1 || ncols<1 || nbands<1)
  {
    fprintf(stderr,"Incorrect dimensions %ix%ix%i.\n", nrows, ncols, nbands);
    usage(argv[0]);
  }
  if (outfname == NULL)
  {
    usage(argv[0]);
  }

  /* open files for I/O */             
  FILE *inf = fopen(infname, "rb");
  if (inf == NULL)
  {
     fprintf(stderr,"Cannot open file %s\n", infname);
     exit(-1); 
  }
  FILE *outf = fopen(outfname, "wb");
  if (outf == NULL)
  {
     fprintf(stderr,"Cannot open file %s\n", outfname);
     fclose(inf);
     exit(-1); 
  }

  /* use file sizes to get number of BIL data points */
  fseek(inf, 0, SEEK_END);
  nspec = ftell(inf) / (sizeof(float)*nbands);
  if (nspec != nrows*ncols)
  {
     fprintf(stderr,"Input file size inconsistent with image dimensions\n");
     fclose(inf);
     fclose(outf);
     exit(-1); 
  }
  rewind(inf);

  /* allocate memory */
  X = malloc(sizeof(float) * nspec * nbands);
  S = malloc(sizeof(uint32_t) * nspec);

  /* read input */
  fread(&(X[0]), sizeof(float), nspec*nbands, inf);
  fclose(inf);

  /* matched filter detection */
  fprintf(stderr,"SLIC segmentation\n");
  slic_segment(S, X, ncols, nrows, nbands,
          regionSize, regularization, minRegionSize);


  /* write output */
  fwrite(&(S[0]), sizeof(uint32_t), nspec, outf);
  fclose(outf);

  /* get superpixel averages */
  if (avgfname)
  {
    float *A = malloc(sizeof(float) * nspec * nbands);
    fprintf(stderr,"Computing superpixel average spectra.\n");
    get_superpixel_average(X,S,A,nrows,ncols,nbands);

    FILE *avgf = fopen(avgfname, "wb");
    if (avgf == NULL)
    {
       fprintf(stderr,"Cannot open file %s\n", avgfname);
       free(A);
       free(X);
       free(S);
       exit(-1); 
    }
    fwrite(&(A[0]), sizeof(float), nbands*nspec, avgf);
    fclose(avgf);
    free(A);
  }
  fprintf(stderr,"Done.\n");

  /* clean up */
  free(X);
  free(S);
  return 1;
}


#endif










