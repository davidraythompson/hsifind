#!/usr/bin/env python
# David R. Thompson

import sys, os, os.path 
import numpy as np
import scipy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# get path to spectral python directory
#spectral_path = os.getenv('HSIFIND_SPECTRALPYTHON_PATH') 
#if spectral_path is None:
#  spectral_path = '/home/drt/src/hsifind/external'
#if not os.path.exists(spectral_path): 
#  raise IOError("Set the HSIFIND_SPECTRALPYTHON_PATH environment variable.")
#sys.path.append(spectral_path)

try:
  import spectral.io.envi as envi
except ImportError:
  print("Couldn't find spectral python. Try setting the PYTHONPATH variable")
  sys.exit(-1)

# get path to data directory
data_path = os.getenv('HSIFIND_DATA_PATH') 
if data_path is None:
  data_path = '/home/drt/hsidata'
if not os.path.exists(data_path): 
  raise IOError("Set the HSIFIND_DATA_PATH environment variable.")

# get path to binary executable
dmsmf_bin = os.getenv('HSIFIND_DMSMF') 
if dmsmf_bin is None:
  dmsmf_bin = '/home/drt/bin/dmsmf'
if not os.path.exists(dmsmf_bin): 
  raise IOError("Set the HSIFIND_DMSMF environment variable.")

thumbsize = (100, 100) # thumbnail size in pixels
diag   = 0.001  # diagonal loading
spectral_subsampling = 1 # increase for a faster result on large cubes 
histeq = False
heatmap = True

def make_rgb(img):
  rgb = []
  for b in [0.1, 0.4, 0.8]:
    band = img.read_band(img.shape[2] * b)
    tmp = band[7:-7, 7:-7]
    bmin = tmp.min ()
    bmax = tmp.max () - bmin + 1e-9
    rgb.append(255*(band-bmin)/bmax)
  return np.array(rgb, dtype=np.uint8)


def load_metadata(path):
 # only print metadata for ISIS cubes
 if not path.endswith('.QUB'):
   return
 lblfile = path.replace('.QUB','.LBL') 
 metadata = {'FILENAME':os.path.basename(lblfile)[-1],
    'START_TIME':None, 'CENTER_LATITUDE':None, 'CENTER_LONGITUDE':None,
    'SUB_SOLAR_LATITUDE':None, 'SUB_SOLAR_LONGITUDE':None,
    'INCIDENCE_ANGLE':None, 'EMISSION_ANGLE':None, 'PHASE_ANGLE':None,
    'SLANT_DISTANCE':None,'INSTRUMENT_HOST_NAME':None,
    'INSTRUMENT_NAME':None,'TARGET_NAME':None,'TARGET_TYPE':None,
    'HORIZONTAL_PIXEL_SCALE':None, 'VERTICAL_PIXEL_SCALE':None,
    'PROCESSING_LEVEL_ID':None}
 with open(lblfile,'r') as f:
   for line in f:
    toks=line.strip().split('=')
    if len(toks) > 1:
      key = toks[0].strip()
      val = toks[1].strip()
      if key in metadata:
        metadata[key] = val
 return metadata


def load_image(path):
  hdrpath = path+'.hdr'
  for p in [path, hdrpath]:
    if not os.path.exists(p):
      raise IOError('Cannot find %s\n' % p)
  img = envi.open(hdrpath)
  if img.sample_size != 4: 
    raise ValueError('I need 4 byte floating point values\n')
  if img.bands.band_unit == 'Nanometers':
    img.bands.band_unit = 'Microns'
    img.bands.centers = [v/1000.0 for v in img.bands.centers]
    img.bands.bandwidths = [v/1000.0 for v in img.bands.bandwidths] 
  return img, path


def spectrum_hash(*args):
  rows = []
  cols = []
  if len(args) == 1:
    if '[' in args[0] and ']' in args[0]:
      # new format
      tokens = args[0].replace(']','').split('[')
      img = tokens[0]
      for rowcol in tokens[-1].split(','):
        t = rowcol.split('.')
        rows.append(int(t[0]))
        cols.append(int(t[1]))
    else:
      # old format
      tokens = args[0].split('.')
      rows = np.array([int(tokens[-2])])
      cols = np.array([int(tokens[-1])])
      img = '.'.join(tokens[:-2])
  else:
    raise IndexError('Need one or three args')
  return img, rows, cols 


def output_spectrum(wl, vec, interval=None):
  order = np.argsort(wl)
  p = plt.plot(wl[order], vec[order], color='red')
  ax = plt.gca()
  ax.set_xlabel('Wavelength')
  ax.set_ylabel('Magnitude')
  ax.grid(True)
  ax.spines['bottom'].set_color('white')
  ax.spines['top'].set_color('white')
  ax.spines['left'].set_color('white')
  ax.spines['right'].set_color('white')
  ax.xaxis.label.set_color('white')
  ax.yaxis.label.set_color('white')
  ax.tick_params(axis='x', colors='white')
  ax.tick_params(axis='y', colors='white')
  if interval is not None:
      plt.axvspan(interval[0], interval[1], facecolor='white', alpha=0.25)
  plt.savefig('spectrum_out.png',transparent=True)
  sys.stdout.write('%i'%len(wl))
  for w in wl:
    sys.stdout.write(' %f' % w)
  for v in vec:
    sys.stdout.write(' %f' % v)
  sys.stdout.write('\n')
  os.system('convert -resize 100x100 spectrum_out.png thumb_out.png')


def get_spectrum_data(img, rows, cols):
  imgpath = os.path.join(data_path, img);
  spixpath = imgpath+'.spix'
  if os.path.exists(spixpath):
    img, imgpath = load_image(spixpath)
  else:
    img, imgpath = load_image(imgpath)
  vec = []
  for row, col in zip(rows, cols):
    vec.append(np.array(img.read_pixel(row, col), dtype=np.float32))
  vec = np.mean(np.array(vec), axis=0)
  wl  = np.array(img.bands.centers)
  return wl, vec


def main():
  # parse command line
  args = sys.argv[:]
  if len(args) < 2:
    cmd = 'list_cubes'
  else:
    cmd = args[1].strip()
  if len(args) < 3:
    obj = 'cuprite97-scene04-cr.rfl'
  else:
    obj = args[2]
  params = args[3:]

  # must always generate these output images
  os.system('touch map_out.png thumb_out.png spectrum_out.txt spectrum_out.png overlay_out.png browse_out.png')

  if cmd == 'list_cubes':

    import glob
    for fi in glob.glob(os.path.join(data_path,'*.hdr')):
        if not '.spix' in fi:
            img, path = load_image(fi.replace('.hdr',''))
            tail, head = os.path.split(path)
            sys.stdout.write(head+'\n')


  elif cmd == 'get_cube':

    import scipy.misc, numpy as np
    cubename = os.path.join(data_path, obj)
    img, imgpath = load_image(cubename)
    rgb = make_rgb(img)
    scipy.misc.imsave('browse_out.png', rgb)
    scipy.misc.imsave('thumb_out.png', scipy.misc.imresize(rgb, thumbsize))
    metadata = load_metadata(cubename)
    for key,val in metadata.items():
      sys.stdout.write('{0},{1}\n'.format(key,val))


  elif cmd == 'get_spectrum_id':

    img, imgpath = load_image(os.path.join(data_path, obj))
    row, col = params
    
  elif cmd == 'get_spectrum_data':

    img, rows, cols = spectrum_hash(obj)
    wl, vec = get_spectrum_data(img, rows, cols)
    output_spectrum(wl, vec)
    
  elif cmd == 'search':

    import scipy.misc, numpy as np
    specimg, rows, cols = spectrum_hash(params[0])
    continuum_removal = params[1]
    wl, vec = get_spectrum_data(specimg, rows, cols)

    import subprocess
    img, imgpath = load_image(os.path.join(data_path, obj))
    targpath, outpath, mdpath = 'target.dat','result.dat','distances.dat'
    vec.tofile(targpath)
    wl = np.array(img.bands.centers)

    # start building dmsmf command line
    args = [dmsmf_bin]
    if img.byte_order != 0:
      args = args + ['-B'] 
    if img.interleave == 0 or img.interleave == 'bsq':
      args = args + ['-s',str(img.shape[0])]
    elif img.interleave == 1 or img.interleave == 'bil':
      args = args + ['-l',str(img.shape[0])]

    # spectral subsampling?
    if spectral_subsampling > 1:
      args = args + ['-S', str(spectral_subsampling)] 

    # continuum removal? add appropriate command line parameters
    if ',' in continuum_removal:
      min_wl, max_wl, ctm_margin = continuum_removal.split(',');
      min_band = str(np.argmin(np.fabs(float(min_wl)-wl)))
      max_band = str(np.argmin(np.fabs(float(max_wl)-wl)))
      continuum_range = str(int(np.ceil(float(ctm_margin)/(wl[1]-wl[0]))))
      args = args + ['-i', min_band, max_band, '-c', continuum_range]
      # output spectrum with a specific interval defined
      output_spectrum(wl, vec, interval=(min_wl, max_wl))
    else:
      output_spectrum(wl, vec)

    # call the search program
    args = args+['-d', str(diag), '-b', str(img.nbands), imgpath, targpath, 
        outpath, mdpath]
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.wait()
    with open(outpath,'r') as fi:
      result = np.fromfile(file=fi, dtype=np.float32).reshape(img.shape[:2])
      with open(mdpath,'r') as mdfi:
        md = np.fromfile(file=mdfi, dtype=np.float32).reshape(img.shape[:2])
        result = result-md/img.nbands;

      # if needed, histogram equalize for better contrast
      if histeq:
        nbins = 256
        imhist, bins = sp.histogram(result.flatten(), nbins, normed=True)
        cdf = imhist.cumsum()
        cdf = 255.0 * cdf / cdf[-1] # normalize
        I = sp.interp(result.flatten(), bins[:-1], cdf)
        I = I.reshape(result.shape)/255.0
      else:
        I = result
       
      # save result as greyscale or heat map
      if heatmap:
        blu = sp.minimum(sp.maximum(4.0*(0.75-I),0.),1.)*255.0
        red = sp.minimum(sp.maximum(4.0*(I-0.25),0.),1.)*255.0
        grn = sp.minimum(sp.maximum(4.0*np.fabs(I-0.5)-1.0,0.),1.)*255.0
        scipy.misc.imsave('map_out.png', np.dstack((red,grn,blu)))
      else:
        scipy.misc.imsave('map_out.png', I.reshape(result.shape))
        

  else:
    raise ValueError('unrecognized command %s' % cmd)

if __name__ == '__main__':
    main()
