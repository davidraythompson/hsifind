/** @file slic.h
 ** @brief SLIC superpixels (@ref slic)
 ** @author Andrea Vedaldi
 **/

/*
Copyright (C) 2007-12 Andrea Vedaldi and Brian Fulkerson.
All rights reserved.

This file is part of the VLFeat library and is made available under
the terms of the BSD license (see the COPYING file).
*/

#ifndef VL_SLIC_H
#define VL_SLIC_H

void
slic_segment (uint32_t * segmentation,
                 float const * image,
                 uint32_t width,
                 uint32_t height,
                 uint32_t numChannels,
                 uint32_t regionSize,
                 float regularization,
                 uint32_t minRegionSize) ;

/* VL_SLIC_H */
#endif
