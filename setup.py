#!/usr/bin/python

from distutils.core import setup

setup(
    name="pylibftdi",
    version="0.1",
    description="Pythonic interface to FTDI devices using libftdi",
    author="Ben Bass",
    author_email="benbass@codedstructure.net",
    url="http://bitbucket.org/codedstructure/pylibftdi",
    packages=["pylibftdi"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Hardware"
    ]
)
