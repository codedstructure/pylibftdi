"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2013 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import os
import itertools
import functools

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
        @param libftdi_search: string or sequence of strings
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
        return the version of the underlying library being used
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
        return a list of triples (manufacturer, description, serial#)
        for each attached device, e.g.:
        [('FTDI', 'UM232R USB <-> Serial', 'FTE4FFVQ'),
         ('FTDI', 'UM245R', 'FTE00P4L')]

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


class Device(object):
    """
    Represents a connection to a single FTDI device
    """

    def __init__(self, device_id=None, mode="b",
                 encoding="latin1", lazy_open=False,
                 chunk_size=0, interface_select=None,
                 **kwargs):
        """
        Device([device_id[, mode, [OPTIONS ...]]) -> Device instance

        represents a single FTDI device accessible via the libftdi driver.
        Supports a basic file-like interface (open/close/read/write, context
        manager support).

        device_id - an optional serial number of the device to open.
            if omitted, this refers to the first device found, which is
            convenient if only one device is attached, but otherwise
            fairly useless.

        mode - either 'b' (binary) or 't' (text). This primarily affects
            Python 3 calls to read() and write(), which will accept/return
            unicode strings which will be encoded/decoded according to the given...

        encoding - the codec name to be used for text operations.

        lazy_open - if True, then the device will not be opened immediately -
            the user must perform an explicit open() call prior to other
            operations.

        chunk_size - if non-zero, split read and write operations into chunks
            of this size. With large or slow accesses, interruptions (i.e.
            KeyboardInterrupt) may not happen in a timely fashion.

        interface_select - select interface to use on multi-interface devices
        """
        self._opened = False
        self.driver = Driver(**kwargs)
        self.fdll = self.driver.fdll
        # device_id is an optional serial number of the requested device.
        self.device_id = device_id
        # mode can be either 'b' for binary, or 't' for text.
        # if set to text, the values returned from read() will
        # be decoded using encoding before being returned as
        # strings; for binary the raw bytes will be returned.
        # This will only affect Python3.
        self.mode = mode
        # when giving a str to Device.write(), it is encoded.
        # default is latin1, because it provides
        # a one-to-one correspondence for code points 0-FF
        self.encoding = encoding
        # ftdi_usb_open_dev initialises the device baudrate
        # to 9600, which certainly seems to be a de-facto
        # standard for serial devices.
        self._baudrate = 9600
        # defining softspace allows us to 'print' to this device
        self.softspace = 0
        # chunk_size (if not 0) chunks the reads and writes
        # to allow interruption
        self.chunk_size = chunk_size
        # interface can be set for devices which have multiple interface
        # ports (e.g. FT4232, FT2232)
        self.interface_select = interface_select
        # lazy_open tells us not to open immediately.
        if not lazy_open:
            self.open()

    def __del__(self):
        "free the ftdi_context resource"
        if self._opened:
            self.close()

    def open(self):
        """
        open connection to a FTDI device
        """
        if self._opened:
            return

        # create context for this device
        self.ctx = create_string_buffer(1024)
        res = self.fdll.ftdi_init(byref(self.ctx))
        if res != 0:
            msg = "%s (%d)" % (self.get_error_string(), res)
            del self.ctx
            raise FtdiError(msg)

        if self.interface_select is not None:
            res = self.fdll.ftdi_set_interface(byref(self.ctx),
                                               self.interface_select)
            if res != 0:
                msg = "%s (%d)" % (self.get_error_string(), res)
                del self.ctx
                raise FtdiError(msg)

        # Try to open the device.  If this fails, reset things to how
        # they were, but we can't use self.close as that assumes things
        # have already been setup.
        # FTDI vendor/product ids required here.
        for usb_vid, usb_pid in itertools.product(USB_VID_LIST, USB_PID_LIST):
            open_args = [byref(self.ctx), usb_vid, usb_pid]
            if self.device_id is None:
                res = self.fdll.ftdi_usb_open(*tuple(open_args))
            else:
                # attempt to match device_id to serial number
                open_args.extend([0, c_char_p(self.device_id.encode('latin1'))])
                res = self.fdll.ftdi_usb_open_desc(*tuple(open_args))
                if res != 0:
                    # swap last two parameters and try again
                    #  - attempt to match device_id to description
                    open_args[-2], open_args[-1] = open_args[-1], open_args[-2]
                    res = self.fdll.ftdi_usb_open_desc(*tuple(open_args))
            if res != FTDI_ERROR_DEVICE_NOT_FOUND:
                # if we succeed (0) or get a specific error, don't continue
                # otherwise (-3) - look for another device
                break

        if res != 0:
            msg = "%s (%d)" % (self.get_error_string(), res)
            # free the context
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
            raise FtdiError(msg)

        # explicitly reset the device to serial mode in case
        # it had previously been used in bitbang mode
        # (some later driver versions might do this automatically)
        self.fdll.ftdi_set_bitmode(byref(self.ctx), 0, BITMODE_RESET)
        self._opened = True

    def close(self):
        "close our connection, free resources"
        if self._opened:
            self.fdll.ftdi_usb_close(byref(self.ctx))
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
        self._opened = False

    @property
    def baudrate(self):
        """
        get or set the baudrate of the FTDI device. Re-read after setting
        to ensure baudrate was accepted by the driver.
        """
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value):
        result = self.fdll.ftdi_set_baudrate(self.ctx, value)
        if result == 0:
            self._baudrate = value

    def _read(self, length):
        """
        actually do the low level reading

        returns a 'bytes' object
        """
        buf = create_string_buffer(length)
        rlen = self.fdll.ftdi_read_data(byref(self.ctx), byref(buf), length)
        if rlen < 0:
            raise FtdiError(self.get_error_string())
        byte_data = buf.raw[:rlen]

        return byte_data

    def read(self, length):
        """
        read(length) -> bytes/string of up to `length` bytes.

        read upto `length` bytes from the FTDI device
        :param length: maximum number of bytes to read
        :return: value read from device
        :rtype: bytes if self.mode is 'b', else decode with self.encoding
        """
        if not self._opened:
            raise FtdiError("read() on closed Device")

        # read the data
        if self.chunk_size != 0:
            remaining = length
            byte_data_list = []
            while remaining > 0:
                rx_bytes = self._read(min(remaining, self.chunk_size))
                if not rx_bytes:
                    break
                byte_data_list.append(rx_bytes)
                remaining -= len(rx_bytes)
            byte_data = b''.join(byte_data_list)
        else:
            byte_data = self._read(length)
        if self.mode == 'b':
            return byte_data
        else:
            # TODO: for some codecs, this may choke if we haven't read the
            # full required data. If this is the case we should probably trim
            # a byte at a time from the output until the decoding works, and
            # buffer the remainder for next time.
            return byte_data.decode(self.encoding)

    def _write(self, byte_data):
        """
        actually do the low level writing
        :param byte_data: data to be written
        :type byte_data: bytes
        :return: number of bytes written
        """
        buf = create_string_buffer(byte_data)
        written = self.fdll.ftdi_write_data(byref(self.ctx),
                                            byref(buf), len(byte_data))
        if written < 0:
            raise FtdiError(self.get_error_string())
        return written

    def write(self, data):
        """
        write(data) -> count of bytes actually written

        write given `data` string to the FTDI device

        :param data: string to be written
        :type data: string or bytes
        :return: count of bytes written, which may be less than `len(data)`
        """
        if not self._opened:
            raise FtdiError("write() on closed Device")

        try:
            byte_data = bytes(data)
        except TypeError:
            # this will happen if we are Python3 and data is a str.
            byte_data = data.encode(self.encoding)

        # actually write it
        if self.chunk_size != 0:
            remaining = len(byte_data)
            written = 0
            while remaining > 0:
                start = written
                length = min(remaining, self.chunk_size)
                result = self._write(byte_data[start: start + length])
                if result == 0:
                    # don't continue to try writing forever if nothing
                    # is actually being written
                    break
                else:
                    written += result
                    remaining -= result
        else:
            written = self._write(byte_data)
        return written

    def flush(self, flush_what=FLUSH_BOTH):
        """
        Instruct the FTDI device to flush its FIFO buffers

        By default both the input and output buffers will be
        flushed, but the caller can selectively chose to only
        flush the input or output buffers using `flush_what`:
          FLUSH_BOTH - (default)
          FLUSH_INPUT - (just the rx buffer)
          FLUSH_OUTPUT - (just the tx buffer)
        """
        if flush_what == FLUSH_BOTH:
            fn = self.fdll.ftdi_usb_purge_buffers
        elif flush_what == FLUSH_INPUT:
            fn = self.fdll.ftdi_usb_purge_rx_buffer
        elif flush_what == FLUSH_OUTPUT:
            fn = self.fdll.ftdi_usb_purge_tx_buffer
        else:
            raise ValueError("Invalid value passed to %s.flush()" %
                             self.__class__.__name__)
        res = fn(byref(self.ctx))
        if res != 0:
            msg = "%s (%d)" % (self.get_error_string(), res)
            raise FtdiError(msg)

    def flush_input(self):
        """
        flush the device input buffer
        """
        self.flush(FLUSH_INPUT)

    def flush_output(self):
        """
        flush the device output buffer
        """
        self.flush(FLUSH_OUTPUT)

    def get_error_string(self):
        """
        :return: error string from libftdi driver
        """
        return self.fdll.ftdi_get_error_string(byref(self.ctx))

    @property
    def ftdi_fn(self):
        """
        this allows the vast majority of libftdi functions
        which are called with a pointer to a ftdi_context
        struct as the first parameter to be called here
        preventing the need to leak self.ctx into the user
        code (and import byref from ctypes):

        >>> with Device() as dev:
        ...     # set 8 bit data, 2 stop bits, no parity
        ...     dev.ftdi_fn.ftdi_set_line_property(8, 2, 0)
        ...
        """
        # note this class is constructed on each call, so this
        # won't be particularly quick.  It does ensure that the
        # fdll and ctx objects in the closure are up-to-date, though.
        class FtdiForwarder(object):

            def __getattr__(innerself, key):
                return functools.partial(getattr(self.fdll, key),
                                         byref(self.ctx))
        return FtdiForwarder()

    def __enter__(self):
        """
        support for context manager.

        Note the device is opened and closed automatically
        when used in a with statement, and the device object
        itself is returned:
        >>> with Device(mode='t') as dev:
        ...     dev.write('Hello World!')
        ...
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, tb):
        "support for context manager"
        self.close()

    #
    # following are various properties and functions to make
    # this emulate a file-object more closely.
    #

    @property
    def closed(self):
        """
        The Python file API defines a read-only 'closed' attribute
        """
        return not self._opened

    def readline(self, size=0):
        """
        readline() for file-like compatibility.

        :param size: maximum amount of data to read looking for a line
        :return: a line of text, or size bytes if no line-ending found

        This only works for mode='t' on Python3
        """
        lsl = len(os.linesep)
        line_buffer = []
        while True:
            next_char = self.read(1)
            if next_char == '' or (size > 0 and len(line_buffer) > size):
                break
            line_buffer.append(next_char)
            if (len(line_buffer) >= lsl and
                    line_buffer[-lsl:] == list(os.linesep)):
                break
        return ''.join(line_buffer)

    def readlines(self, sizehint=None):
        """
        readlines() for file-like compatibility.
        """
        lines = []
        if sizehint is not None:
            string_blob = self.read(sizehint)
            lines.extend(string_blob.split(os.linesep))

        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines

    def writelines(self, lines):
        """
        writelines for file-like compatibility.
        """
        for line in lines:
            self.write(line)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            line = self.readline()
            if line:
                return line
            else:
                raise StopIteration
    next = __next__
