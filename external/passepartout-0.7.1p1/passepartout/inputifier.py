# inputifier = INPUT identIFIER, representing a combo of
# positional arguments and options to
# a shell command or callable function/method/subroutine, etc.
#
# auri is a serialization of inputifier expressed as a URI, e.g.,
# /k0=v0/k1=v1/k2=v2/.../arg0/arg1/arg3/...
# auri can also take a form like
# /acfed9f98eef67ae02b8832c7e712346
# which is the md5sum of the json string
# {"ordered": [0, 1, 2, 3, 4, 5], "keyed": {}}
# Please see from_json() for details.
#
# argument/parameter is positional, thus ordered
# option/flag/switch is named, thus keyed

try:
    import json
except ImportError:
    import simplejson as json

try:
    import hashlib
except ImportError:
    import md5 as hashlib

import urllib

class InputifierException(Exception): pass

SEPARATOR = "="

class Inputifier:

    # python does not enforce private constructor,
    # so we mimic the behavior by checking a kwarg for pre-defined value.
    note = "the constructor is private"

    # private constructor, so that auri CAN NOT be arbitrarily assigned.
    def __init__(self, auri, ordered=[], keyed={}, warning="don't use"):
        if warning != Inputifier.note:
            raise InputifierException(Inputifier.note)

        self.auri = auri
        # ordered arguements as a list
        self.ordered = ordered
        # keyed arguements (key-value pairs) as a dict
        self.keyed = keyed

    @staticmethod
    def from_json(jsonString):
        try:
            auri = "/%s" % hashlib.md5(jsonString).hexdigest()
            d = json.loads(jsonString)
            ordered = d["ordered"]
            keyed = d["keyed"]
            return Inputifier(auri, ordered=ordered, keyed=keyed, warning=Inputifier.note)
        except ValueError, ve:
            raise InputifierException("Failed to instantiate: %s: %s" % (ValueError.__name__, ve))
        except KeyError, ke:
            raise InputifierException("Failed to instantiate: %s: %s" % (KeyError.__name__, ke))

    @staticmethod
    # it must be "" or starts with "/" and not ending with "/"
    def from_auri(auriStr):
        if auriStr == "":
            return Inputifier(auriStr, warning=Inputifier.note)

        if not auriStr[0] == "/" or auriStr[-1] == "/":
            raise InputifierException("Invalid inputifier: %s" % auriStr)

        a = auriStr.split("/")
        # a[0] should be ""

        ordered = []
        keyed = {}
        for x in a[1:]:
            if x == "":
                continue
            idx = x.find(SEPARATOR)
            # ordered
            if idx == -1:
                # fixme: urlEscape(x)?
                ordered.append(urllib.unquote_plus(x))
            # otherwise keyed
            else:
                # fixme: urlEscape(x)?
                keyed[x[0:idx]] = urllib.unquote_plus(x[idx+1:])
        return Inputifier(auriStr, ordered=ordered, keyed=keyed, warning=Inputifier.note)

    def __repr__(self):
        return "Inputifier(\"%s\", ordered=%s, keyed=%s, warning=\"%s\")" % (self.auri, self.ordered, self.keyed, Inputifier.note)

    def __str__(self):
        return self.auri
        #auriStr = ""
        #for x in self.ordered:
        #    auriStr += "/%s" % x
        #for k, v in self.keyed.iteritems():
        #    auriStr += "/%s%s%s"% (k, SEPARATOR, v)
        #return auriStr

def main():
    import sys

    count = 0

    print >> sys.stdout, ">> Test", count; count += 1
    auriString = "/a/b/-1.0/0/1/x%s1/y%sb/z%s-1" % (SEPARATOR, SEPARATOR, SEPARATOR)
    n = Inputifier.from_auri(auriString)
    print >> sys.stdout, n
    print >> sys.stdout, str(n)
    print >> sys.stdout, repr(n)
    #print >> sys.stdout, eval(repr(n))
    print >> sys.stdout, n.auri
    print >> sys.stdout, n.ordered
    print >> sys.stdout, n.keyed

    print >> sys.stdout, ">> Test", count; count += 1
    auriString = ""
    n = Inputifier.from_auri(auriString)
    print >> sys.stdout, n
    print >> sys.stdout, str(n)
    print >> sys.stdout, repr(n)
    #print >> sys.stdout, eval(repr(n))
    print >> sys.stdout, n.auri
    print >> sys.stdout, n.ordered
    print >> sys.stdout, n.keyed

    print >> sys.stdout, ">> Test", count; count += 1
    jsonString = '{"ordered": [0, 1, 2, 3, 4, 5], "keyed": {}}'
    n = Inputifier.from_json(jsonString)
    print >> sys.stdout, n
    print >> sys.stdout, str(n)
    print >> sys.stdout, repr(n)
    #print >> sys.stdout, eval(repr(n))
    print >> sys.stdout, n.auri
    print >> sys.stdout, n.ordered
    print >> sys.stdout, n.keyed

if __name__ == "__main__":
    main()
