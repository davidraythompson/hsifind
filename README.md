-------------------------------------------------------------------------------
                     HSIFind - a lightweight web-based search 
                     service for imaging spectroscopy data
-------------------------------------------------------------------------------

Copyright 2013, by the California Institute of Technology.  ALL RIGHTS 
RESERVED. United States Government Sponsorship acknowledged. Any commercial 
use must be negotiated with the Office of Technology Transfer at the California 
Institute of Technology.

This software may be subject to U.S. export control laws and regulations. By 
accepting this document, the user agrees to comply with all U.S. export laws 
and regulations.  User has the responsibility to obtain export licenses, or
other export authority as may be required before exporting such information to 
foreign countries or providing access to foreign persons.
 
Authors:
  David R. Thompson   david.r.thompson@jpl.nasa.gov
  Alex Smith   alexander.smith@jpl.nasa.gov 
  Zhangfan Xing   zhangfan.xing@jpl.nasa.gov

Requirements:
  Python 2.5+ 
  NumPy 
  Python Imaging Library (PIL)  
  wxPython  
  matplotlib 
  sampo (bundled with this distribution) 
  spectral python (bundled with this distribution) 
  A c compiler like GCC 


-------------------------------------------------------------------------------
                           Installation Instructions
-------------------------------------------------------------------------------


Step 1 - Compile the server-side search program "dmsmf"
-------------------------------------------------------------------------------
Unzip enter the directory backend/dms/ and run 'make install' This will create 
a matched filter search routine called "dmsmf" that you should install in your 
path.  It can run from the command line to test the matched filter search 
algorithm.  


Step 2 - Configure environment variables
-------------------------------------------------------------------------------
Set the following environment variables: 
  HSIFIND_DATA_PATH - the data directory with imaging spectrometer data
  HSIFIND_DMSMF - indicates the full filepath to the "dmsmf" binary
  PYTHONPATH - this is a colon-separated list of absolute filepaths that tells 
    your python installation where to find the dependencies.  Make sure it 
    includes the backend/ subdirectory. If you did not install spectral python 
    separately, also include backend/spectral/ and its subdirectories 
    (backend/spectral/io, backend/spectral/algorithms, 
     backend/spectral/database, backend/spectra/utilities).  All directories 
    should be absolute paths, separated by colons.


Step 3 - alter the configuration file
-------------------------------------------------------------------------------
The configuration file is hsifind.conf. Make a new configuration file. You 
should make a new server-side configuration directory to hold hsifind.conf, and 
modify the configuration file using a text editor so that it points to your 
version of the (executable) python code "hsifind.py"


Step 3 - Configure the server
----------------------------
sampo-1.0.0-linux-x86_64-a.tar.gz is a ready-to-use package, pre-compiled for 
64-bit linux. It bundles passepartout with python 2.7 and httpd 2.2.23, using 
PAC (Python Apache Combo).  Linux and Mac OS compilations are provided. 

It is straightforward to use sampo:
(1) untar to a directory
(2) run sampo-service config
(3) run sampo-service start
(4) optionally, run sampo-service stop

Here is a real example, run from the base directory: 
$ ./sampo-1.0.0-linux-x86_64-a/bin/sampo-service config -p 18080 \
      -d /path/to/my/configuration/directory/conf
$ ./sampo-1.0.0-linux-x86_64-a/bin/sampo-service start
$ ./sampo-1.0.0-linux-x86_64-a/bin/sampo-service stop


Step 4 - Set up the client software
---------------------------------
After setting up the "sampo" package, you'll find javascript in the client/
subdirectory.  A README file in that directory explains the process.


-------------------------------------------------------------------------------
                                   Usage
-------------------------------------------------------------------------------



