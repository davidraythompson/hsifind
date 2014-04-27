from constant import SPEC, APP_NAME, APP_VERSION
from constant import NAME, VALUE

class Sxn:

    _l = ["spec",
        "application",
        "type",
        "path",
        "identifier"
        ]

    def __init__(self):
        self.__dict__["spec"] = SPEC
        self.__dict__["application"] = "%s-%s" % (APP_NAME, APP_VERSION)
        self.__dict__["type"] = None
        self.__dict__["path"] = None
        self.__dict__["identifier"] = None

    def __setattr__(self, attr, value):
        if attr not in self._l:
            raise AttributeError, attr + " not allowed"
        self.__dict__[attr] = value

    def __getattr__(self, attr):
        if attr not in self._l:
            raise AttributeError, attr + " non-existent"
        return self.__dict__[attr]

    def from_list(self,l):
        for x in l:
            name = x[NAME]
            value = x[VALUE]
            #print name,value
            # skip unrecognized name
            if name not in self._l:
                continue
            self.__dict__[name] = value

    def to_list(self):
        l = []
        for x in self._l:
            if self.__dict__[x] == None:
                continue
            l.append({NAME:x,VALUE:self.__dict__[x]})
        return l

    def to_dict(self):
        d = {}
        for x in self._l:
            if self.__dict__[x] == None:
                continue
            d[x] = self.__dict__[x]
        return d

def test():

    sxn = Sxn()

    print sxn.spec
    print sxn.application
    print sxn.type
    print sxn.path
    print sxn.identifier

    print sxn.to_list()
    print sxn.to_dict()

    print ""
    sxn.path = "/this/is/a/service"
    print sxn.to_list()
    print sxn.to_dict()

    print ""
    l = [
        {NAME:"type",VALUE:"x.test"},
        {NAME:"path",VALUE:"/this/is/a/service"},
        {NAME:"identifier",VALUE:"/echo/a/b/c/"},
        ]

    sxn.from_list(l)
    print sxn.to_list()
    print sxn.to_dict()

def main():

    """
    import sys

    if (len(sys.argv) != 2):
        print "Usage: key"
        sys.exit(0)
    """

    test()

if __name__ == '__main__':
    main()
