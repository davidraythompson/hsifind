#!/usr/bin/env python
#
# 20110516, xing

try:
    import json
except ImportError:
    import simplejson as json

from cgi import parse_qs

import urllib

from pprint import pformat

from passepartout.factory import ApplicationFactory
from passepartout.lister import Lister
from passepartout.inputifier import Inputifier
from passepartout.sxn import Sxn

from passepartout.constant import SERV10N

import md5
#import os
import sys

# a logical, its mere apperance will set it to True,
# regardless what the value is given in query string
def get_param_as_boolean(d, param):
    if not d.has_key(param):
        return False
    return True

def get_param_value(d, param):
    if not d.has_key(param):
        return None
    for value in d[param]:
        if value != "":
            return value
    return None

def get_params(queryString):
    # keep_blank_values = True
    d = parse_qs(queryString, True)

    params = {}

    # parameters that can take arbitrary string value
    key = "callback"
    params[key] = get_param_value(d, key)

    #key = "output"
    #params[key] = get_param_value(d,key)
    #params[key] = normalize_output_format_string(params[key])

    # parameters that serve as boolean
    for key in ["indent"]:
        params[key] = get_param_as_boolean(d, key)

    return params

def show_environ(environ, start_response):
    """Show the environment. List is returned."""
    output = ['<pre>']
    output.append(pformat(environ))
    output.append('</pre>')

    output_len = sum(len(line) for line in output)

    mimeType = "text/plain"
    status = '200 OK'
    response_headers = [('Content-type', mimeType),
                        ('Content-Length', str(output_len))]

    start_response(status, response_headers)

    return output

def exit_400(start_response, err):
    status = "400 Bad Request"
    output = []
    output.append(json.dumps({"error":err}))
    output_len = sum(len(line) for line in output)

    mimeType = "text/plain"
    response_headers = [('Content-type', mimeType),
                        ('Content-Length', str(output_len))]

    start_response(status, response_headers)

    return output

def exit_500(d, start_response):
    status = "500 Internal Server Error"
    output = [json.dumps(d)]
    output_len = sum(len(line) for line in output)

    mimeType = "text/plain"
    response_headers = [('Content-type', mimeType),
                        ('Content-Length', str(output_len))]

    start_response(status, response_headers)

    return output

def show_description(d, start_response):

    status = "200 OK"

    output = ["application: %s\n" % d["application"]]
    output.append("\n")
    output.append("""usage: There are two ways to call this service:

(1) Do an HTTP GET using URL

    %s?queryString

(2) Do an HTTP POST with queryString as message body using URL

    %s

in which queryString is a query expressed in JSON format, e.g.,
%s

The result is returned in JSON format too.
""" % (d["script_uri"], d["script_uri"], d["usage"]))
    output.append("\n")
    output.append("method: %s\n" % d["method"])

    output_len = sum(len(line) for line in output)

    mimeType = "text/plain"
    response_headers = [('Content-type', mimeType),
                        ('Content-Length', str(output_len))]

    start_response(status, response_headers)

    return output

# d is a dict
def do_it(d, start_response, indent=None, callback=None):

    status = "200 OK"
    
    if callback != None:
        indent = None
    text = json.dumps(d, indent=indent)
    if callback != None:
        text = "%s(%s)" % (callback, text)
    output = [text]
    # just to print out nicer with an extra "\n"
    if indent != None:
        output.append("\n")
    output_len = sum(len(line) for line in output)

    mimeType = "text/plain"
    response_headers = [('Content-type', mimeType),
                        ('Content-Length', str(output_len))]

    start_response(status, response_headers)

    return output

# wsgi entry point for environ checking
def application1(environ, start_response):
    # quick hack, dump wsgi.input as string
    key = "wsgi.input"
    if environ.has_key(key):
        environ[key] = environ[key].read()
    return show_environ(environ, start_response)

# get identifier from inputString when method is POST
def get_inputifier_from_post(auri, inputString, debug=False):

    i8r = Inputifier.from_auri(auri)

    # if auri is "", just ignore inputString
    if auri == "":
        return i8r

    # auri must be like /md5String(/)? now
    if not (len(i8r.ordered) == 1 and i8r.keyed == {}):
        raise Exception("POST method not supported for auri %s" % auri)

    i8r = Inputifier.from_json(inputString)
    if auri != i8r.auri:
        raise Exception("Inconsistent POST request: url and body mismatch")
    print >> sys.stderr, "i8r=", i8r
    return i8r

# wsgi entry point
def application(environ, start_response):

    #debug = True
    debug = False

    # must know workDirTop
    if not environ.has_key("PASSEPARTOUT_WORK_DIR_TOP"):
        raise Exception("Missing work dir top")
    workDirTop = environ["PASSEPARTOUT_WORK_DIR_TOP"]

    # must know resultUrlTop
    if not environ.has_key("PASSEPARTOUT_RESULT_URI_PREFIX"):
        raise Exception("Missing result url prefix")
    resultUriPrefix = environ["PASSEPARTOUT_RESULT_URI_PREFIX"]
    if resultUriPrefix[0] != "/":
        raise Exception("result uri prefix must start with '/'")
    resultUrlTop = "file://%s%s" % (environ['DOCUMENT_ROOT'], resultUriPrefix)

    # must know where application config dir is
    if not environ.has_key("PASSEPARTOUT_APP_CONF_DIR"):
        raise Exception("Missing application config dir")
    appConfDir = environ["PASSEPARTOUT_APP_CONF_DIR"]

    # check on http method
    if environ['REQUEST_METHOD'] not in ["GET", "POST"]:
        raise Exception("Method %s is not supported." % environ['REQUEST_METHOD'])

    pathInfo = environ['PATH_INFO']
    if not pathInfo.startswith("/"):
        raise Exception("Internal inconsistency: PATH_INFO does not start with '/': %s" % pathInfo)

    queryString = environ['QUERY_STRING']
    # do url unescape
    queryString = urllib.unquote(queryString)
    # callback parameter
    params = get_params(queryString)
    callback = params["callback"]
    if debug:
        print >> sys.stderr, "callback=", callback
    # indent parameter
    # be aware that params["indent"] has value True/False, but
    # indent must be None or a number
    indent = None
    if params["indent"]:
        indent = 4
    if debug:
        print >> sys.stderr, "indent=", indent

    # pathInfo is /
    if pathInfo == "/":
        # sxn info
        sxn = Sxn()
        sxn.type = "x.sxn.b"
        sxn.path = environ["SCRIPT_NAME"]
        sxn.identifier = "/"
        # list of applications
        l = Lister(appConfDir, debug=debug)
        # dict to return
        d = {}
        d["applications"] = l.list()
        d["method"] = environ['REQUEST_METHOD']
        d[SERV10N] = sxn.to_list()
        return do_it(d, start_response, indent=indent, callback=callback)

    # pathInfo is /app(/*)?
    a = pathInfo.split("/")
    # service name
    serviceFullName = pathInfo[:1+len(a[1])]
    if debug:
        print >> sys.stderr, "serviceFullName=", serviceFullName
    # identifier string
    idString = pathInfo[1+len(a[1]):]
    if debug:
        print >> sys.stderr, "idString=", idString
    auri = idString
    isMeta = False
    if idString.endswith("/"):
        auri = idString[:-1]
        isMeta = True
    i8r = Inputifier.from_auri(auri)
    # if POST, inputifier should be obtained from http body
    if environ['REQUEST_METHOD'] == "POST":
        inputString = environ["wsgi.input"].read()
        i8r = get_inputifier_from_post(auri, inputString, debug=debug)

    # sxn
    sxn = Sxn()
    sxn.type = "x.sxn.a"
    sxn.path = "%s%s" % (environ["SCRIPT_NAME"], serviceFullName)
    sxn.identifier = idString

    # yet to implement this
    if i8r.keyed != {}:
        raise Exception("Unsupported service endpoint with keyed arguments: %s" % pathInfo)

    # yet to implement this
    if isMeta and i8r.ordered != []:
        raise Exception("Unsupported service endpoint with trailing '/': %s" % pathInfo)

    # dispatched to the backend application
    appFactory = ApplicationFactory(appConfDir, debug=debug)
    appName = serviceFullName[1:] # remove leading "/"
    app = appFactory.get(appName, workDirTop=workDirTop, resultUrlTop=resultUrlTop)
    if isMeta:
        d = app.info()
    else:
        d = app.do(ordered=i8r.ordered, keyed=i8r.keyed)
        # map result file urls from file:// to uris relative to document root
        result = None
        if d.has_key("result"):
            result = d["result"]
        if result != None and result.has_key("files"):
            # must be in sync with resultUrlTop above!!!
            idx = len("file://%s" % environ["DOCUMENT_ROOT"])
            files = []
            for x in result["files"]:
                files.append(x[idx:])
            result["files"] = files
        # save input too
        d["input"] = {"ordered":i8r.ordered, "keyed":i8r.keyed}
    d["method"] = environ['REQUEST_METHOD']
    d[SERV10N] = sxn.to_list()
    return do_it(d, start_response, indent=indent, callback=callback)

# cgi entry point
if __name__ == '__main__':
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(application)
