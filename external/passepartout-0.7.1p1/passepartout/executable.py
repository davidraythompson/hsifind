#!/usr/bin/env python
#
# 20110426, xing

from backend import Backend, BackendException

from file import Copier

import shutil

try:
    import json
except ImportError:
    import simplejson as json

try:
    import hashlib
except ImportError:
    import md5 as hashlib

import os, sys

import subprocess

class Executable(Backend):

    def __init__(self, serviceFullName, workDirTop, resultUrlTop, config, debug=False):
        Backend.__init__(self, serviceFullName, workDirTop, resultUrlTop, config, debug=debug)
        self.copier = Copier()

    def get_name(self):
        # get service name
        idx = self.serviceFullName.rfind("/")
        if idx == -1:
            raise BackendException("internal inconsistency: wrong format for service full name %s" % self.serviceFullName)
        serviceName = self.serviceFullName[idx+1:]
        #return "%s-%s" % (APP_NAME, APP_VERSION)
        return serviceName

    def get_version(self):
        return self.config.version

    def get_usage(self):
        ordered = self.config.arguments
        keyed = {"warning":"to be implemented"}
        d = {"ordered":ordered, "keyed":keyed}
        return d

    def check(self, ordered=[], keyed={}):
        # check keyed
        if keyed != {}:
            raise BackendException("not implemented: checking %s" % keyed)

        # check ordered
        if len(ordered) != len(self.config.arguments):
            raise BackendException("wrong number of ordered arguments: %s required" % len(self.config.arguments))

        return

    def do_it(self, ordered=[], keyed={}):
        # fix me: there is a potential race condition
        # must be resolved using locking or other mechanism.

        # key to uniquely identify work for this query
        key = json.dumps(ordered) + json.dumps(keyed)
        tag = hashlib.md5(key).hexdigest()
        if self.debug:
            print >> sys.stderr, "tag:", tag

        # where real work is conducted
        # it is deleted after work is done.
        myWorkDir = os.path.join(self.workDir, tag)
        if not os.path.exists(myWorkDir):
            os.makedirs(myWorkDir)
        if self.debug:
            print >> sys.stderr, "myWorkDir:", myWorkDir
        # temporarily disabled

        #it has been checked by check(), so we just extract arg values
        #arguments = self.config.arguments
        argValues = ordered
        if self.debug:
            print >> sys.stderr, argValues

        # do rpc now
        cmdList = [self.config.path]
        #if self.config.path.endswith(".sh"):
        #    cmdList = ["sh", "-e", self.config.path]
        #if self.config.path.endswith(".csh"):
        #    cmdList = ["csh", "-e", self.config.path]
        for argValue in argValues:
            # cmdList member only takes strings !!!
            # fix me: should we demand user to make sure?
            cmdList.append(str(argValue))
        if self.debug:
            print >> sys.stderr, "cmdList:", cmdList
        proc = subprocess.Popen(cmdList, cwd=myWorkDir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        outValue, errValue = proc.communicate()
        if self.debug:
            print >> sys.stderr, "stdout is", outValue
            print >> sys.stderr, "stderr is", errValue

        # if the excutable existed with error
        if proc.returncode != 0:
            shutil.rmtree(myWorkDir)
            return {"stdout":outValue,
                "stderr":errValue}

        # if files are generated, move them to a place accessible by client
        urlList = []
        if self.config.path[0] != "/":
            raise BackendException("executable path defined in app config must be absolute: %s" % x)
        prefix = myWorkDir
        for x in self.config.result:
            if x[0] == "/":
                raise BackendException("result path defined in app config must be relative: %s" % x)
            srcPath = os.path.join(prefix, x)
            if self.debug:
                print >> sys.stderr, "srcPath:", srcPath
            #
            destUrl = "%s/%s/%s" % (self.resultUrl, tag, x)
            if self.debug:
                print >> sys.stderr, "destUrl:", destUrl
            self.copier.copy(srcPath, destUrl)
            urlList.append(destUrl)

        shutil.rmtree(myWorkDir)

        if urlList == []:
            return {"stdout": outValue,
                "stderr": errValue}

        return {"stdout": outValue,
            "stderr": errValue,
            "files": urlList}
