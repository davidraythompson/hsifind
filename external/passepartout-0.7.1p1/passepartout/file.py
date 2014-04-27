import shutil
import urllib2

import os

class CopierException(Exception): pass

class Copier:

    def __init__(self):
        pass

    # make a copy from an absolute srcPath to a destUrl
    #def put(srcPath, destUrl, deleteOriginal=True, rmParentDir=True):
    def copy(self, srcPath, destUrl, deleteOriginal=False):
        if srcPath[0] != "/":
            raise CopierException("srcPath must be absolute: %s" % srcPath)

        # http://en.wikipedia.org/wiki/File_URI_scheme
        if destUrl[0:7] == "file://":
            destPath = destUrl[7:]
            if destPath[0] != "/":
                raise CopierException("destUrl is not an acceptable file url: %s" % destUrl)
            parentDir = os.path.dirname(destPath)
            if not os.path.exists(parentDir):
                os.makedirs(parentDir)
            shutil.copyfile(srcPath, destPath)
            if deleteOriginal:
                srcPath.remove()
            return

        # then, must be http:// scheme
        if destUrl[0:7] != "http://":
            raise CopierException("destUrl is neither file nor http url: %s" % destUrl)

        # fixme: use python's newer requests module?
        f = open(srcPath, "r")
        data = f.read()
        f.close()
        #
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        # assume w10n write here, so "[]" suffix is required.
        request = urllib2.Request(destUrl+"[]", data=data)
        #request.add_header('Content-Type', 'application/octet-stream')
        request.get_method = lambda: 'PUT'
        url = opener.open(request)

        return

def main():
    import sys
    src = sys.argv[1]
    dest = sys.argv[2]

    print >> sys.stderr, src, dest
    cpr = Copier()
    cpr.copy(src, dest)

if __name__ == "__main__":
    main()
