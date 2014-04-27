from configobj import ConfigObj

import sys

class Config(object):

    def __init__(self, configPath, debug=False):
        self.debug = debug

        # validate first?
        config = ConfigObj(configPath)

        self.type = None
        if "type" in config:
            self.type = config["type"]

        # for type = module
        self.clazz = None
        if "class" in config:
            self.clazz = config["class"]

        # for type = executable
        self.version = None
        if "version" in config:
            self.version = config["version"]
        if self.debug:
            print >> sys.stderr, "version:", self.version

        self.description = None
        if "description" in config:
            self.description = config["description"]

        self.path = None
        if "path" in config:
            self.path = config["path"]

        self.arguments = []
        if "arguments" in config:
            self.arguments = config["arguments"]

        self.result = []
        if "result" in config:
            self.result = config["result"]

if __name__ == "__main__":
        #configPath = "./sample.conf"
        configPath = sys.argv[1]
        config = Config(configPath)
        print config.path
        #print config.url
        print config.arguments
        print config.arguments[3]
        print config.result
