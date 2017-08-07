#!/usr/bin/python

import sys

try:
    # this is primarily to support the 'develop' target
    # if setuptools/distribute are installed
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup_args = dict(
    name="pylibftdi",
    version="0.16.0",
    description="Pythonic interface to FTDI devices using libftdi",
    long_description=open('README.rst').read(),
    author="Ben Bass",
    author_email="benbass@codedstructure.net",
    url="http://bitbucket.org/codedstructure/pylibftdi",
    packages=["pylibftdi", "pylibftdi.examples"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Hardware"
    ]
)

if sys.platform == 'darwin':
    # only install the OS X scripts if we're on a Mac
    setup_args['scripts'] = ["scripts/ftdi_osx_driver_reload",
                             "scripts/ftdi_osx_driver_unload"]

setup(**setup_args)
