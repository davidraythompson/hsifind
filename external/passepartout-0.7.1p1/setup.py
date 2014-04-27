from distutils.core import setup

setup(
    name = "passepartout",
    version = "0.7.1p1",
    author = "http://629fe602c9df1aa2cc6a8d7db597191b/dev",
    author_email = "dev@629fe602c9df1aa2cc6a8d7db597191b",
    url = "http://629fe602c9df1aa2cc6a8d7db597191b",
    description = "Passepartout",
    long_description = "Passepartout",
    classifiers = [
        "Programming Language :: Python",
        #"Programming Language :: Python :: 3",
        #"License :: BSD",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    packages = [
        "passepartout",
        "passepartout/wsgi",
    ],
    scripts = [
        "passepartout/cli/passepartout",
    ],
)
