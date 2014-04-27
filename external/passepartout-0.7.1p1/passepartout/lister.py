from constant import APP_CONFIG_FILE_SUFFIX
from factory import ApplicationFactory

import os, sys

# list available applications

class ListerException(Exception):
    pass

class Lister:

    # path: path of working dir
    def __init__(self, dir, debug=False):
        # dir containing application def/conf files.
        self.dir = dir
        self.appFactory = ApplicationFactory(dir, debug=debug)
        self.debug = debug

    def list(self, format="json"):
        dirList = os.listdir(self.dir)
        dirList.sort()
        #count = 0
        entries = []
        for x in dirList:
            if not x.endswith("."+APP_CONFIG_FILE_SUFFIX):
                continue
            name = x[:-(len(APP_CONFIG_FILE_SUFFIX)+1)]
            app = self.appFactory.get(name, workDirTop="/tmp/p10t/work0", resultUrlTop="file:///tmp/p10t/result0")
            entries.append(app.info())

        if format == "json":
            return entries

        raise ListerException("Unsupported format "+format)

def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: appConfDir [debug]"
        sys.exit(-1)

    debug = False
    if len(sys.argv) > 2 and sys.argv[2] != "":
        debug = True

    dir = sys.argv[1]

    try:
        import json
    except ImportError:
        import simplejson as json

    lister = Lister(dir, debug=debug)
    print >> sys.stdout, json.dumps(lister.list(), indent=4)

if __name__ == "__main__":
    main()
