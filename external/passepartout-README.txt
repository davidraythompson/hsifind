20130805, Zhangfan Xing

passepartout-0.7.1p1a is a patched version of the passepartout 
package, which is needed to run HSIFind.  It has the following
additional third-party dependencies:

python 2.4 and above
httpd-2.2.x
pip-1.2.1
setuptools-0.6c11

You should set up the filesystem so that the hsifind.conf file is in the appropriate application configuration directory, and that it runs as a service from httpd.
