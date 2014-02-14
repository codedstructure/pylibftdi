"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import itertools

# be disciplined so pyflakes can check us...
from ctypes import (CDLL, byref, c_int, c_char_p, c_void_p, cast,
                    create_string_buffer, Structure, pointer, POINTER)
from ctypes.util import find_library

from pylibftdi._base import FtdiError


class ftdi_device_list(Structure):
    _fields_ = [('next', c_void_p),
                ('dev', c_void_p)]


class ftdi_version_info(Structure):
    _fields_ = [('major', c_int),
                ('minor', c_int),
                ('micro', c_int),
                ('version_str', c_char_p),
                ('snapshot_str', c_char_p)]

# Note I gave up on attempts to use ftdi_new/ftdi_free (just using
# ctx instead of byref(ctx) in first param of most ftdi_* functions) as
# (at least for 64-bit) they only worked if argtypes was declared
# (c_void_p for ctx), and that's too much like hard work to maintain.
# So I've reverted to using create_string_buffer for memory management,
# byref(ctx) to pass in the context instance, and ftdi_init() /
# ftdi_deinit() pair to manage the driver resources. It's very nice
# how layered the libftdi code is, with access to each layer.

# These constants determine what type of flush operation to perform
FLUSH_BOTH = 1
FLUSH_INPUT = 2
FLUSH_OUTPUT = 3
# Device Modes
BITMODE_RESET = 0x00
BITMODE_BITBANG = 0x01

# Opening / searching for a device uses this list of IDs to search
# by default. These can be extended directly after import if required.
FTDI_VENDOR_ID = 0x0403
USB_VID_LIST = [FTDI_VENDOR_ID]
USB_PID_LIST = [0x6001, 0x6010, 0x6011, 0x6014]

FTDI_ERROR_DEVICE_NOT_FOUND = -3


class Driver(object):
    """
    This is where it all happens...
    We load the libftdi library, and use it.
    """

    _instance = None
    _need_init = True

    # prefer libftdi1 if available. Windows uses 'lib' prefix.
    _dll_list = ('ftdi1', 'libftdi1', 'ftdi', 'libftdi')

    def __init__(self, libftdi_search=None):
        """
        :param libftdi_search: force a particular version of libftdi to be used
        :type libftdi_search: string or sequence of strings
        """
        self._libftdi_path = self._find_libftdi(libftdi_search)
        self.fdll = CDLL(self._libftdi_path)
        # most args/return types are fine with the implicit
        # int/void* which ctypes uses, but some need setting here
        self.fdll.ftdi_get_error_string.restype = c_char_p
        self.fdll.ftdi_usb_get_strings.argtypes = (
            c_void_p, c_void_p,
            c_char_p, c_int, c_char_p, c_int, c_char_p, c_int)

    def _find_libftdi(self, libftdi_search=None):
        """
        find the libftdi path, suitable for ctypes.CDLL()

        :param libftdi_search: string or sequence of strings
            use to force a particular version of libftdi to be used
        """
        if libftdi_search is None:
            search_list = self._dll_list
        elif isinstance(libftdi_search, (str, bytes)):
            search_list = (libftdi_search,)
        else:
            search_list = libftdi_search

        ftdi_lib = None
        for dll in search_list:
            ftdi_lib = find_library(dll)
            if ftdi_lib is not None:
                break
        if ftdi_lib is None:
            raise FtdiError('libftdi library not found (search: {})'.format(search_list))
        return ftdi_lib

    def libftdi_version(self):
        """
        :return: the version of the underlying library being used
        :rtype: tuple (major, minor, micro, version_string, snapshot_string)
        """
        if hasattr(self.fdll, 'ftdi_get_library_version'):
            version = ftdi_version_info()
            self.fdll.ftdi_get_library_version(byref(version))
            return (version.major, version.minor, version.micro,
                    version.version_str, version.snapshot_str)
        else:
            # library versions <1.0 don't support this function...
            return (0, 0, 0,
                    'unknown - no ftdi_get_library_version()', 'unknown')

    def list_devices(self):
        """
        :return: (manufacturer, description, serial#) for each attached
            device, e.g.:

            [('FTDI', 'UM232R USB <-> Serial', 'FTE4FFVQ'),
            ('FTDI', 'UM245R', 'FTE00P4L')]

        :rtype: a list of string triples

        the serial number can be used to open specific devices
        """
        # ftdi_usb_find_all sets dev_list_ptr to a linked list
        # (*next/*usb_device) of usb_devices, each of which can
        # be passed to ftdi_usb_get_strings() to get info about
        # them.
        # this will contain the device info to return
        devices = []
        manuf = create_string_buffer(128)
        desc = create_string_buffer(128)
        serial = create_string_buffer(128)
        devlistptrtype = POINTER(ftdi_device_list)
        dev_list_ptr = devlistptrtype()

        # create context for doing the enumeration
        ctx = create_string_buffer(1024)
        if self.fdll.ftdi_init(byref(ctx)) != 0:
            msg = self.fdll.ftdi_get_error_string(byref(ctx))
            raise FtdiError(msg)

        try:
            for usb_vid, usb_pid in itertools.product(USB_VID_LIST, USB_PID_LIST):
                res = self.fdll.ftdi_usb_find_all(byref(ctx),
                                                  byref(dev_list_ptr),
                                                  usb_vid,
                                                  usb_pid)
                if res < 0:
                    msg = "%s (%d)" % (self.get_error_string(), res)
                    raise FtdiError(msg)
                elif res > 0:
                    # take a copy of the dev_list for subsequent list_free
                    dev_list_base = pointer(dev_list_ptr.contents)
                    # traverse the linked list...
                    try:
                        while dev_list_ptr:
                            res = self.fdll.ftdi_usb_get_strings(
                                byref(ctx),
                                dev_list_ptr.contents.dev,
                                manuf, 127, desc, 127, serial, 127)
                            # don't error on failure to get all the data
                            # error codes: -7: manuf, -8: desc, -9: serial
                            if res < 0 and res not in (-7, -8, -9):
                                msg = "%s (%d)" % (self.get_error_string(), res)
                                raise FtdiError(msg)
                            devices.append((manuf.value, desc.value, serial.value))
                            # step to next in linked-list
                            dev_list_ptr = cast(dev_list_ptr.contents.next,
                                                devlistptrtype)
                    finally:
                        self.fdll.ftdi_list_free(dev_list_base)
        finally:
            self.fdll.ftdi_deinit(byref(ctx))
        return devices
