import os, sys

from config import Config
from executable import Executable

class ApplicationFactoryException(Exception): pass

class ApplicationFactory:

    def __init__(self, appConfDir, debug=False):
        if appConfDir == None:
            raise ApplicationFactoryException("application config dir is None")
        if not os.path.exists(appConfDir):
            raise ApplicationFactoryException("non-existent: %s" % appConfDir)
        if not os.path.isdir(appConfDir):
            raise ApplicationFactoryException("not a dir: %s" % appConfDir)
        self.appConfDir = appConfDir

        self.debug = debug

    def _get_app_executable(self, appName, workDirTop, resultUrlTop, config):
        # fixme: 20120516, xing, to satisfy executable.py
        # we will change it when re-make executable.py along with backend.py
        serviceFullName = "/%s" % appName

        app = Executable(serviceFullName, workDirTop, resultUrlTop, config, debug=self.debug)
        if self.debug:
            print >> sys.stderr, app

        return app

    def get(self, appName, workDirTop=None, resultUrlTop=None):
        # application name (appName) is always \w+
        # fixme: sanity check on appName

        appConfigPath = os.path.join(self.appConfDir, "%s.conf" % appName)
        if not os.path.exists(appConfigPath):
            raise ApplicationFactoryException("unknown application: %s" % appName)

        if self.debug:
            print >> sys.stderr, "use config", appConfigPath

        config = Config(appConfigPath, debug=self.debug)
        if config.type == None:
            raise ApplicationFactoryException("application type is None")
        
        if config.type == "executable":
            return self._get_app_executable(appName, workDirTop, resultUrlTop, config)

        # otherwise default to type = module
        classFullName = config.clazz
        if self.debug:
            print >> sys.stderr, classFullName
        idx = classFullName.rfind(".")
        if idx == -1:
            raise ApplicationFactoryException("unsupported class: %s" % classFullName)
        moduleName = classFullName[:idx]
        className = classFullName[idx+1:]
        if self.debug:
            print >> sys.stderr, moduleName, className

        x = __import__(moduleName)
        appClass = getattr(x, className)
        if self.debug:
            print >> sys.stderr, appClass

        # fixme: 20120516, xing, to satisfy backend.py
        # we will change it later when re-make backend.py
        serviceFullName = "/%s" % appName
        app = appClass(serviceFullName, workDirTop, resultUrlTop, config, debug=self.debug)
        if self.debug:
            print >> sys.stderr, app

        return app

def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: appConfDir appName [debug]"
        sys.exit(-1)

    debug = False
    if len(sys.argv) > 3 and sys.argv[3] != "":
        debug = True

    appConfDir, appName = sys.argv[1:3]
    appFactory = ApplicationFactory(appConfDir, debug=debug)

    if debug:
        print >> sys.stderr, "appConfDir:", appConfDir, ", appName:", appName

    print appFactory.get(appName, workDirTop="/tmp/p10t/work", resultUrlTop="file:///tmp/p10t/result")

if __name__ == "__main__":
    main()
