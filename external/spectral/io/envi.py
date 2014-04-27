#########################################################################
#
#   envi.py - This file is part of the Spectral Python (SPy) package.
#
#   Copyright (C) 2001-2010 Thomas Boggs
#
#   Spectral Python is free software; you can redistribute it and/
#   or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   Spectral Python is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this software; if not, write to
#
#               Free Software Foundation, Inc.
#               59 Temple Place, Suite 330
#               Boston, MA 02111-1307
#               USA
#
#########################################################################
#
# Send comments to:
# Thomas Boggs, tboggs@users.sourceforge.net
#

'''
ENVI [#envi-trademark]_ is a popular commercial software package for processing
and analyzing geospatial imagery.  SPy supports reading imagery with associated
ENVI header files and reading & writing spectral libraries with ENVI headers.
ENVI files are opened automatically by the SPy :func:`~spectral.image` function
but can also be called explicitly.  It may be necessary to open an ENVI file
explicitly if the data file is in a separate directory from the header or if
the data file has an unusual file extension that SPy can not identify.

    >>> import spectral.io.envi as envi
    >>> img = envi.open('cup95eff.int.hdr', '/Users/thomas/spectral_data/cup95eff.int')

.. [#envi-trademark] ENVI is a registered trademark of ITT Corporation.
'''

import numpy as np

dtype_map = [('1', np.int8),                    # byte
             ('2', np.int16),                   # 16-bit int
             ('3', np.int32),                   # 32-bit int
             ('4', np.float32),                 # 32-bit float
             ('5', np.float64),                 # 64-bit float
             ('6', np.complex64),               # 2x32-bit complex
             ('9', np.complex128),              # 2x64-bit complex
             ('12', np.uint16),                 # 6-bit unsigned int
             ('13', np.uint32),                 # 32-bit unsigned int
             ('14', np.int64),                  # 64-bit int
             ('15', np.uint64)]                 # 64-bit unsigned int
envi_to_dtype = dict((k, np.dtype(v).char) for (k, v) in dtype_map)
dtype_to_envi = dict(tuple(reversed(item)) for item in envi_to_dtype.items())


def read_envi_header(file):
    '''
    USAGE: hdr = read_envi_header(file)

    Reads an ENVI ".hdr" file header and returns the parameters in
    a dictionary as strings.
    '''

    from string import find, split, strip
    from exceptions import IOError
    from __builtin__ import open

    f = open(file, 'r')

    if find(f.readline(), "ENVI") == -1:
        f.close()
        raise IOError("Not an ENVI header.")

    lines = f.readlines()
    f.close()

    dict = {}
    i = 0
    try:
        while i < len(lines):
            if find(lines[i], '=') == -1:
                i += 1
                continue
            (key, sep, val) = lines[i].partition('=')
            key = key.strip()
            val = val.strip()
            if val[0] == '{':
                str = val.strip()
                while str[-1] != '}':
                    i += 1
                    str += '\n' + lines[i].strip()
                if key == 'description':
                    dict[key] = str.strip('{}').strip()
                else:
                    vals = split(str[1:-1], ',')
                    for j in range(len(vals)):
                        vals[j] = strip(vals[j])
                    dict[key] = vals
            else:
                dict[key] = val
            i += 1
        return dict
    except:
        raise IOError("Error while reading ENVI file header.")


def gen_params(envi_header):
    '''
    Parse an envi_header to a `Params` object.

    Arguments:

    `envi_header` (dict or file_name):

        A dict or an `.hdr` file name
    '''
    from exceptions import TypeError
    import spectral

    if not isinstance(envi_header, dict):
        from spyfile import find_file_path
        headerPath = find_file_path(envi_header)
        h = read_envi_header(headerPath)
    else:
        h = envi_header

    class Params:
        pass
    p = Params()
    p.nbands = int(h["bands"])
    p.nrows = int(h["lines"])
    p.ncols = int(h["samples"])
    p.offset = int(h["header offset"])
    p.byte_order = int(h["byte order"])
    p.dtype = np.dtype(envi_to_dtype[h["data type"]]).str
    if p.byte_order != spectral.byte_order:
        p.dtype = np.dtype(p.dtype).newbyteorder().str
    p.filename = None
    return p


def open(file, image=None):
    '''
    Opens an image or spectral library with an associated ENVI HDR header file.

    Arguments:

        `file` (str):

            Name of the header file for the image.

        `image` (str):

            Optional name of the associated image data file.

    Returns:

        :class:`spectral.SpyFile` or :class:`spectral.io.envi.SpectralLibrary`
        object.

    Raises:

        TypeError, IOError.

    If the specified file is not found in the current directory, all
    directories listed in the SPECTRAL_DATA environment variable will be
    searched until the file is found.  Based on the name of the header file,
    this function will search for the image file in the same directory as the
    header, looking for a file with the same name as the header but different
    extension. Extensions recognized are .img, .dat, .sli, and no extension.
    Capitalized versions of the file extensions are also searched.
    '''

    import os
    from exceptions import IOError, TypeError
    from spyfile import find_file_path
    import numpy
    import spectral

    headerPath = find_file_path(file)
    h = read_envi_header(headerPath)

    p = gen_params(h)

    inter = h["interleave"]

    #  Validate image file name
    if not image:
        #  Try to determine the name of the image file
        headerDir = os.path.split(headerPath)
        if headerPath[-4:].lower() == '.hdr':
            headerPathTitle = headerPath[:-4]
            exts = ['', 'img', 'IMG', 'dat', 'DAT', 'sli', 'SLI', 'hyspex'] +\
                   [inter.lower(), inter.upper()]
            for ext in exts:
                if len(ext) == 0:
                    testname = headerPathTitle
                else:
                    testname = headerPathTitle + '.' + ext
                if os.path.isfile(testname):
                    image = testname
                    break
        if not image:
            raise IOError('Unable to determine image file name.')
    else:
        image = find_file_path(image)

    p.filename = image

    if h.get('file type') == 'ENVI Spectral Library':
        # File is a spectral library
        data = numpy.fromfile(p.filename, p.dtype, p.ncols * p.nrows)
        data.shape = (p.nrows, p.ncols)
        return SpectralLibrary(data, h, p)

    #  Create the appropriate object type for the interleave format.
    inter = h["interleave"]
    if inter == 'bil' or inter == 'BIL':
        from spectral.io.bilfile import BilFile
        img = BilFile(p, h)
    elif inter == 'bip' or inter == 'BIP':
        from spectral.io.bipfile import BipFile
        img = BipFile(p, h)
    else:
        from spectral.io.bsqfile import BsqFile
        img = BsqFile(p, h)

    img.scale_factor = float(h.get('reflectance scale factor', 1.0))

    # Add band info

    if 'wavelength' in h:
        try:
            img.bands.centers = [float(b) for b in h['wavelength']]
        except:
            pass
    if 'fwhm' in h:
        try:
            img.bands.bandwidths = [float(f) for f in h['fwhm']]
        except:
            pass
    img.bands.band_unit = h.get('wavelength units', "")
    img.bands.bandQuantity = "Wavelength"

    return img


def check_new_filename(hdr_file, img_ext, force):
    '''Raises an exception if the associated header or image file names exist.
    '''
    import os
    if len(img_ext) > 0 and img_ext[0] != '.':
        img_ext += '.'
    hdr_file = os.path.realpath(hdr_file)
    (base, ext) = os.path.splitext(hdr_file)
    if ext.lower() != '.hdr':
        raise ValueError('Header file name must end in ".hdr" or ".HDR".')
    image_file = base + img_ext
    if not force:
        if os.path.isfile(hdr_file):
            raise Exception('Header file %s already exists. Use `force` '
                            'keyword to force overwrite.' % hdr_file)
        if os.path.isfile(image_file):
            raise Exception('Image file %s already exists. Use `force` '
                            'keyword to force overwrite.' % image_file)
    return (hdr_file, image_file)


def save_image(hdr_file, image, **kwargs):
    '''
    Saves an image to disk.

    Arguments:

        `hdr_file` (str):

            Header file (with ".hdr" extension) name with path.

        `image` (SpyFile object or numpy.ndarray):

            The image to save.

    Keyword Arguments:

        `dtype` (numpy dtype or type string):

            The numpy data type with which to store the image.  For example,
            to store the image in 16-bit unsigned integer format, the argument
            could be any of `numpy.uint16`, "u2", "uint16", or "H".

        `force` (bool):

            If the associated image file or header already exist and `force` is
            True, the files will be overwritten; otherwise, if either of the
            files exist, an exception will be raised.

        `ext` (str):

            The extension to use for the image file.  If not specified, the
            default extension ".img" will be used.  If `ext` is an empty
            string, the image file will have the same name as the header but
            without the ".hdr" extension.

        `interleave` (str):

            The band interleave format to use in the file.  This argument
            should be one of "bil", "bip", or "bsq".  If not specified, the
            image will be written in BIP interleave.

        `byteorder` (int or string):

            Specifies the byte order (endian-ness) of the data as
            written to disk. For little endian, this value should be
            either 0 or "little".  For big endian, it should be
            either 1 or "big". If not specified, native byte order
            will be used.

        `metadata` (dict):

            A dict containing ENVI header parameters (e.g., parameters
            extracted from a source image).

    If the source image being saved was already in ENVI format, then the
    SpyFile object for that image will contain a `metadata` dict that can be
    passed as the `metadata` keyword. However, care should be taken to ensure
    that all the metadata fields from the source image are still accurate
    (e.g., band names or wavelengths will no longer be correct if the data
    being saved are from a principal components transformation).
    '''
    import os
    import sys
    import __builtin__
    import spectral
    from spectral.io.spyfile import SpyFile, interleave_transpose

    metadata = kwargs.get('metadata', {}).copy()
    force = kwargs.get('force', False)
    img_ext = kwargs.get('ext', '.img')
    
    endian_out = str(kwargs.get('byteorder', sys.byteorder)).lower()
    if endian_out in ('0', 'little'):
        endian_out = 'little'
    elif endian_out in ('1', 'big'):
        endian_out = 'big'
    else:
        raise ValueError('Invalid byte order: "%s".' % endian_out)

    (hdr_file, img_file) = check_new_filename(hdr_file, img_ext, force)

    if isinstance(image, np.ndarray):
        data = image
        src_interleave = 'bip'
        swap = False
    elif isinstance(image, SpyFile):
        if image.memmap is not None:
            data = image.memmap
            src_interleave = {spectral.BSQ: 'bsq', spectral.BIL: 'bil',
                              spectral.BIP: 'bip'}[image.interleave]
            swap = image.swap
        else:
            data = image.load(dtype=image.dtype, scale=False)
            src_interleave = 'bip'
            swap = False
        if image.scale_factor != 1:
            metadata['reflectance scale factor'] = image.scale_factor
    else:
        data = image.load()
        src_interleave = 'bip'
        swap = False
    dtype = np.dtype(kwargs.get('dtype', data.dtype)).char
    if dtype != data.dtype.char:
        data = data.astype(dtype)
    metadata['data type'] = dtype_to_envi[dtype]
    # A few header parameters need to be set independent of what is provided
    # in the supplied metadata.

    # Always write data from start of file, regardless of what was in
    # provided metadata.
    offset = int(metadata.get('header offset', 0))
    if offset != 0:
        print 'Ignoring non-zero header offset in provided metadata.'
    metadata['header offset'] = 0

    metadata['lines'] = image.shape[0]
    metadata['samples'] = image.shape[1]
    metadata['bands'] = image.shape[2]
    metadata['file type'] = 'ENVI Standard'
    interleave = kwargs.get('interleave', 'bip').lower()
    if interleave not in ['bil', 'bip', 'bsq']:
        raise ValueError('Invalid interleave: %s'
                         % str(kwargs['interleave']))
    if interleave != src_interleave:
        data = data.transpose(interleave_transpose(src_interleave, interleave))
    metadata['interleave'] = interleave
    metadata['byte order'] = 1 if endian_out == 'big' else 0
    if (endian_out == sys.byteorder and not data.dtype.isnative) or \
      (endian_out != sys.byteorder and data.dtype.isnative):
        data = data.byteswap()

    write_envi_header(hdr_file, metadata, is_library=False)
    print 'Saving', img_file
    bufsize = data.shape[0] * data.shape[1] * np.dtype(dtype).itemsize
    fout = __builtin__.open(img_file, 'wb', bufsize)
    fout.write(data.tostring())
    fout.close()


def create_image(hdr_file, metadata, **kwargs):
    '''
    Creates an image file and ENVI header with a memmep array for write access.

    Arguments:

        `hdr_file` (str):

            Header file (with ".hdr" extension) name with path.

        `metadata` (dict):

            Metadata to specify the image file format.  The following paramters
            (in ENVI header format) are required: "bands", "lines", "samples",
            "header offset", and "data type".

    Keyword Arguments:

        `dtype` (numpy dtype or type string):

            The numpy data type with which to store the image.  For example,
            to store the image in 16-bit unsigned integer format, the argument
            could be any of `numpy.uint16`, "u2", "uint16", or "H". If this
            keyword is given, it will override the "data type" parameter in
            the `metadata` argument.

        `force` (bool, False by default):

            If the associated image file or header already exist and `force` is
            True, the files will be overwritten; otherwise, if either of the
            files exist, an exception will be raised.

        `ext` (str):

            The extension to use for the image file.  If not specified, the
            default extension ".img" will be used.  If `ext` is an empty
            string, the image file will have the same name as the header but
            without the ".hdr" extension.

        `memmap_mode` (str):

            Mode of img.memmap ("w+" by default). See numpy.memmap for further
            information.

    Returns:

        `SpyFile` object:

            The returned SpyFile subclass object will have a `numpy.memmmap`
            object member named `memmap`, which can be used for direct access
            to the memory-mapped file data.
    '''
    from exceptions import NotImplementedError, TypeError
    import numpy as np
    import os
    import spectral

    force = kwargs.get('force', False)
    img_ext = kwargs.get('ext', '.img')
    memmap_mode = kwargs.get('memmap_mode', 'w+')
    (hdr_file, img_file) = check_new_filename(hdr_file, img_ext, force)

    metadata = metadata.copy()
    params = gen_params(metadata)
    if kwargs.get('dtype'):
        metadata['data type'] = dtype_to_envi[dtype(kwargs['dtype']).char]
        dt = np.dtype(kwargs['dtype']).char
    else:
        dt = np.dtype(params.dtype).char
    metadata['byte order'] = spectral.byte_order
    params.filename = img_file

    is_library = False
    if metadata.get('file type') == 'ENVI Spectral Library':
        is_library = True
        raise NotImplementedError('ENVI Spectral Library cannot be created ')

    # Create the appropriate object type -> the memmap (=image) will be
    # created on disk
    inter = metadata["interleave"]
    (R, C, B) = (params.nrows, params.ncols, params.nbands)
    if inter.lower() not in ['bil', 'bip', 'bsq']:
        raise ValueError('Invalid interleave specified: %s.' % str(inter))
    if inter.lower() == 'bil':
        from spectral.io.bilfile import BilFile
        memmap = np.memmap(img_file, dtype=dt, mode=memmap_mode,
                           offset=params.offset, shape=(R, B, C))
        img = BilFile(params, metadata)
        img.memmap = memmap
    elif inter.lower() == 'bip':
        from spectral.io.bipfile import BipFile
        memmap = np.memmap(img_file, dtype=dt, mode=memmap_mode,
                           offset=params.offset, shape=(R, C, B))
        img = BipFile(params, metadata)
        img.memmap = memmap
    else:
        from spectral.io.bsqfile import BsqFile
        memmap = np.memmap(img_file, dtype=dt, mode=memmap_mode,
                           offset=params.offset, shape=(B, R, C))
        img = BsqFile(params, metadata)
        img.memmap = memmap

    # Write the header file after the image to assure write success
    write_envi_header(hdr_file, metadata, is_library=is_library)
    return img


class SpectralLibrary:
    '''
    The envi.SpectralLibrary class holds data contained in an ENVI-formatted
    spectral library file (.sli files), which stores data as specified by a
    corresponding .hdr header file.  The primary members of an
    Envi.SpectralLibrary object are:

        `spectra` (:class:`numpy.ndarray`):

            A subscriptable array of all spectra in the library. `spectra` will
            have shape `CxB`, where `C` is the number of spectra in the library
            and `B` is the number of bands for each spectrum.

        `names` (list of str):

            A length-`C` list of names corresponding to the spectra.

        `bands` (:class:`spectral.BandInfo`):

            Spectral bands associated with the library spectra.

    '''

    def __init__(self, data, header, params):
        from spectral.spectral import BandInfo
        self.spectra = data
        self.bands = BandInfo()
        if 'wavelength' in header:
            try:
                self.bands.centers = [float(b) for b in header['wavelength']]
            except:
                pass
        if 'fwhm' in header:
            try:
                self.bands.bandwidths = [float(f) for f in header['fwhm']]
            except:
                pass
        if 'spectra names' in header:
            self.names = header['spectra names']
        else:
            self.names = [''] * self.bands.shape[0]
        self.bands.band_unit = header.get('wavelength units', "")
        self.bands.bandQuantity = "Wavelength"
        self.params = params
        self.metadata = {}
        self.metadata.update(header)
        self.metadata['data ignore value'] = 'NaN'

    def save(self, fileBaseName, description=None):
        '''
        Saves the spectral library to a library file.

        Arguments:

            `fileBaseName` (str):

                Name of the file (without extension) to save.

            `description` (str):

                Optional text description of the library.

        This method creates two files: `fileBaseName`.hdr and
        `fileBaseName`.sli.
        '''
        import spectral
        import __builtin__
        meta = {}
        meta.update(self.metadata)
        if self.bands.centers:
            meta['samples'] = len(self.bands.centers)
        else:
            meta['samples'] = len(self.spectra.shape[0])
        meta['lines'] = self.spectra.shape[0]
        meta['bands'] = 1
        meta['header offset'] = 0
        meta['data type'] = 4           # 32-bit float
        meta['interleave'] = 'bsq'
        meta['byte order'] = spectral.byte_order
        meta['wavelength units'] = self.bands.band_unit
        meta['spectra names'] = [str(n) for n in self.names]
        meta['wavelength'] = self.bands.centers
        meta['fwhm'] = self.bands.bandwidths
        if (description):
            meta['description'] = description
        write_envi_header(fileBaseName + '.hdr', meta, True)
        fout = __builtin__.open(fileBaseName + '.sli', 'wb')
        self.spectra.astype('f').tofile(fout)
        fout.close()


def _write_header_param(fout, paramName, paramVal):
    if paramName.lower() == 'description':
        valStr = '{\n%s}' % '\n'.join(['  ' + line for line
                                       in paramVal.split('\n')])
    elif not isinstance(paramVal, str) and hasattr(paramVal, '__len__'):
        valStr = '{ %s }' % (
            ' , '.join([str(v).replace(',', '-') for v in paramVal]),)
    else:
        valStr = str(paramVal)
    fout.write('%s = %s\n' % (paramName, valStr))


def write_envi_header(fileName, header_dict, is_library=False):
    import __builtin__
    fout = __builtin__.open(fileName, 'w')
    d = {}
    d.update(header_dict)
    if is_library:
        d['file type'] = 'ENVI Spectral Library'
    elif 'file type' not in d:
        d['file type'] = 'ENVI Standard'
    fout.write('ENVI\n')
    # Write the standard parameters at the top of the file
    std_params = ['description', 'samples', 'lines', 'bands', 'header offset',
                  'file type', 'data type', 'interleave', 'sensor type',
                  'byte order', 'reflectance scale factor', 'map info']
    for k in std_params:
        if k in d:
            _write_header_param(fout, k, d[k])
    for k in d:
        if k not in std_params:
            _write_header_param(fout, k, d[k])
    fout.close()


def readEnviHdr(file):
    warn('readEnviHdr has been deprecated.  Use read_envi_header.',
         DeprecationWarning)
    return read_envi_header(file)


def writeEnviHdr(fileName, header_dict, is_library=False):
    warn('writeEnviHdr has been deprecated.  Use write_envi_header.',
         DeprecationWarning)
    return write_envi_header(fileName, header_dict, is_library)
