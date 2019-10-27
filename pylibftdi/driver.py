"""
pylibftdi.driver - interface to the libftdi library

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import itertools
from collections import namedtuple

# be disciplined so pyflakes can check us...
from ctypes import (cdll, byref, c_int, c_char_p, c_void_p, c_uint16, cast,
                    create_string_buffer, Structure, POINTER)
from ctypes.util import find_library

from pylibftdi._base import FtdiError, LibraryMissingError


class libusb_version_struct(Structure):
    _fields_ = [('major', c_uint16),
                ('minor', c_uint16),
                ('micro', c_uint16),
                ('nano', c_uint16),
                ('rc', c_char_p),
                ('describe', c_char_p)]

libusb_version = namedtuple('libusb_version',
                            'major minor micro nano rc describe')


class ftdi_device_list(Structure):
    _fields_ = [('next', c_void_p),
                ('dev', c_void_p)]


class ftdi_version_info(Structure):
    _fields_ = [('major', c_int),
                ('minor', c_int),
                ('micro', c_int),
                ('version_str', c_char_p),
                ('snapshot_str', c_char_p)]


libftdi_version = namedtuple('libftdi_version',
                             'major minor micro version_str snapshot_str')


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
USB_PID_LIST = [0x6001, 0x6010, 0x6011, 0x6014, 0x6015]

FTDI_ERROR_DEVICE_NOT_FOUND = -3


class Driver(object):
    """
    This is where it all happens...
    We load the libftdi library, and use it.
    """

    # prefer libftdi1 if available. Windows uses 'lib' prefix.
    _lib_search = {
        'libftdi': ('ftdi1', 'libftdi1', 'ftdi', 'libftdi'),
        'libusb': ('usb-1.0', 'libusb-1.0')
    }

    def __init__(self, libftdi_search=None, **kwargs):
        """
        :param libftdi_search: force a particular version of libftdi to be used
            can specify either library name(s) or path(s)
        :type libftdi_search: string or sequence of strings
        """
        if libftdi_search is not None:
            self._lib_search['libftdi'] = libftdi_search

    def _load_library(self, name, search_list=None):
        """
        find and load the requested library

        :param name: library name
        :param search_list: sequence or string referring to library names
            library names or paths can be given
        :return: a CDLL object referring to the requested library
        """
        if search_list is None:
            search_list = self._lib_search.get(name, ())
        if isinstance(search_list, (str, bytes)):
            search_list = (search_list,)

        lib = None
        for dll in search_list:
            try:
                # Windows in particular can have find_library
                # not find things which work fine directly on
                # cdll access.
                lib = getattr(cdll, dll)
                break
            except OSError:
                lib_path = find_library(dll)
                if lib_path is not None:
                    lib = getattr(cdll, lib_path)
                    break
        if lib is None:
            raise LibraryMissingError('{} library not found (search: {})'.format(
                name, search_list))
        return lib

    @property
    def _libusb(self):
        """
        ctypes DLL referencing the libusb library, if it exists

        Note this is not normally used directly by pylibftdi, and is available
        primarily for diagnostic purposes.
        """
        if self._libusb_dll is None:
            self._libusb_dll = self._load_library('libusb')
            self._libusb_dll.libusb_get_version.restype = POINTER(libusb_version_struct)

        return self._libusb_dll
    _libusb_dll = None

    def libusb_version(self):
        """
        :return: namedtuple containing version info on libusb
        """
        ver = self._libusb.libusb_get_version().contents
        return libusb_version(ver.major, ver.minor, ver.micro, ver.nano,
                              ver.rc, ver.describe)

    @property
    def fdll(self):
        """
        ctypes DLL referencing the libftdi library

        This is the main interface to FTDI functionality.
        """
        if self._fdll is None:
            self._fdll = self._load_library('libftdi')
            # most args/return types are fine with the implicit
            # int/void* which ctypes uses, but some need setting here
            self._fdll.ftdi_get_error_string.restype = c_char_p
            self._fdll.ftdi_usb_get_strings.argtypes = (
                c_void_p, c_void_p,
                c_char_p, c_int, c_char_p, c_int, c_char_p, c_int)
        return self._fdll
    _fdll = None

    def libftdi_version(self):
        """
        :return: the version of the underlying library being used
        :rtype: tuple (major, minor, micro, version_string, snapshot_string)
        """
        if hasattr(self.fdll, 'ftdi_get_library_version'):
            version = ftdi_version_info()
            self.fdll.ftdi_get_library_version(byref(version))
            return libftdi_version(version.major, version.minor, version.micro,
                                   version.version_str, version.snapshot_str)
        else:
            # library versions <1.0 don't support this function...
            return libftdi_version(0, 0, 0,
                                   '< 1.0 - no ftdi_get_library_version()',
                                   'unknown')

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

        def _s(s):
            """From c_char_p / str you shall be / in Python2 or 3"""
            return str(s.decode())

        try:
            for usb_vid, usb_pid in itertools.product(USB_VID_LIST, USB_PID_LIST):
                res = self.fdll.ftdi_usb_find_all(byref(ctx),
                                                  byref(dev_list_ptr),
                                                  usb_vid,
                                                  usb_pid)
                if res < 0:
                    err_msg = self.fdll.ftdi_get_error_string(byref(ctx))
                    msg = "%s (%d)" % (err_msg, res)
                    raise FtdiError(msg)
                elif res > 0:
                    # take a copy of the dev_list for subsequent list_free
                    dev_list_base = byref(dev_list_ptr)
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
                                err_msg = self.fdll.ftdi_get_error_string(byref(ctx))
                                msg = "%s (%d)" % (err_msg, res)
                                raise FtdiError(msg)
                            devices.append((_s(manuf.value),
                                            _s(desc.value),
                                            _s(serial.value)))
                            # step to next in linked-list
                            dev_list_ptr = cast(dev_list_ptr.contents.next,
                                                devlistptrtype)
                    finally:
                        self.fdll.ftdi_list_free(dev_list_base)
        finally:
            self.fdll.ftdi_deinit(byref(ctx))
        return devices
