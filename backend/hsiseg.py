#!/usr/bin/env python
# David R. Thompson

import sys, os, os.path, shutil
import numpy as np
import spectral.io.envi as envi

# get path to data directory
data_path = os.getenv('HSIFIND_DATA_PATH') 
if data_path is None:
  data_path = '/home/drt/hsidata'
if not os.path.exists(data_path): 
  raise IOError("Set the HSIFIND_DATA_PATH environment variable.")

def main():
    smoothing = 0.0001
    for root, dirs, files in os.walk(data_path):
        print root, files
        for fi in files:
            if fi.endswith('.hdr') and '.spix' not in fi:
                inhdr = os.path.join(root, fi)
                inimg = inhdr.replace('.hdr','')
                outimg = inhdr.replace('.hdr','.spix')
                outhdr = inhdr.replace('.hdr','.spix.hdr')
                if not os.path.exists(outhdr):
                    shutil.copy(inhdr,outhdr)
                if not os.path.exists(outimg):
                    p = subprocess.Popen(['slic', 
                                      '-r', str(img.shape[0]), 
                                      '-c', str(img.shape[1]), 
                                      '-b', str(img.shape[2]), 
                                      '-s', str(smoothing),
                                      '-a', outimg, inimg])
                    p.wait()
if __name__ == '__main__':
    main()
