import sys

import os, sys

class BackendException(Exception):
    pass

class Backend:

    def __init__(self, serviceFullName, workDirTop, resultUrlTop, config, debug=False):
        if serviceFullName == None:
            raise BackendException("Unknown service full name")
        if serviceFullName[0] != "/":
            raise BackendException("Service full name does not start with '/'")
        self.serviceFullName = serviceFullName

        if workDirTop == None:
            raise BackendException("Unknown work dir top")
        self.workDirTop = workDirTop

        if resultUrlTop == None:
            raise BackendException("Unknown result url top")
        self.resultUrlTop = resultUrlTop

        self.config = config

        self.debug = debug

        # subclass should use the following:
        # work dir for this service
        self.workDir = os.path.join(workDirTop, serviceFullName[1:])
        # result url for this service
        self.resultUrl = os.path.join(resultUrlTop, serviceFullName[1:])

    # must be overriden
    # return: name of application
    def get_name(self):
        raise Exception("%s undefined." % sys._getframe().f_code.co_name)

    # must be overriden
    # return: version of application
    def get_version(self):
        raise Exception("%s undefined." % sys._getframe().f_code.co_name)

    # must be overriden
    # return: usage as a string
    def get_usage(self):
        raise Exception("%s undefined." % sys._getframe().f_code.co_name)

    # return: more detailed description
    def get_description(self):
        return self.config.description

    # must be overriden
    # return: nothing
    def check(self, ordered=[], keyed={}):
        raise Exception("%s undefined." % sys._getframe().f_code.co_name)

    # must be overriden
    # returns a dict
    def do_it(self, ordered=[], keyed={}):
        raise Exception("%s undefined." % sys._getframe().f_code.co_name)

    def get_info(self):
        return {"name":self.get_name(),
            "version":self.get_version(),
            "usage":self.get_usage(),
            "description":self.get_description()}

    def info(self):
        return self.get_info()

    # can be overriden
    def do(self, ordered=[], keyed={}):
        application = "%s-%s" % (self.get_name(), self.get_version())

        # check orederd and keyed arguments
        if self.debug:
            print >> sys.stderr, "check arguments"
        self.check(ordered=ordered, keyed=keyed)

        if self.debug:
            print >> sys.stderr, "run it"

        error = None
        result = None
        try:
            result = self.do_it(ordered=ordered, keyed=keyed)
        except:
            theType, theValue, theTraceback = sys.exc_info()
            error = "%s" % theValue

        #return error
        if error != None:
            return {"application":application, "error":error}

        # return result
        return {"application":application, "result":result}
