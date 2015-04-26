"""
Report environment info relevant to pylibftdi

example usage::

    $ python3 -m pylibftdi.examples.info
    pylibftdi version     : 0.15.0
    libftdi version       : libftdi_version(major=1, minor=1, micro=0, version_str=b'1.1', snapshot_str=b'unknown')
    libftdi library path  : /usr/local/lib/libftdi1.dylib
    libusb version        : libusb_version(major=1, minor=0, micro=19, nano=10903, rc=b'', describe=b'http://libusb.info')
    libusb library path   : /usr/local/lib/libusb-1.0.dylib
    Python version        : 3.4.0
    OS platform           : Darwin-14.1.0-x86_64-i386-64bit

Copyright (c) 2015 Ben Bass <benbass@codedstructure.net>
"""


import platform
from collections import OrderedDict

import pylibftdi


def ftdi_info():
    """
    Return (ordered) dictionary contianing pylibftdi environment info

    Designed for display purposes only; keys and value types may vary.
    """
    info = OrderedDict()
    d = pylibftdi.Driver()
    info['pylibftdi version'] = pylibftdi.__VERSION__
    try:
        info['libftdi version'] = d.libftdi_version()
        info['libftdi library name'] = d._load_library('libftdi')._name
    except pylibftdi.LibraryMissingError:
        info['libftdi library'] = "Missing"
    try:
        info['libusb version'] = d.libusb_version()
        info['libusb library name'] = d._load_library('libusb')._name
    except pylibftdi.LibraryMissingError:
        info['libusb library'] = "Missing"
    info['Python version'] = platform.python_version()
    info['OS platform'] = platform.platform()
    return info

if __name__ == '__main__':
    for key, value in ftdi_info().items():
        print("{:22}: {}".format(key, value))
