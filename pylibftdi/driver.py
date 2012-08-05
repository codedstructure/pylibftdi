"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>
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


class UsbDevList(Structure):
    _fields_ = [('next', c_void_p),
                ('usb_dev', c_void_p)]

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

# Default USB IDs
USB_VID = 0x0403
USB_PID = 0x6001
# However, a list of IDs is actually matched against.
USB_VID_LIST = [USB_VID]
USB_PID_LIST = [USB_PID, 0x6014]


class Driver(object):
    """
    This is where it all happens...
    We load the libftdi library, and use it.
    """

    _instance = None
    _need_init = True

    def __new__(cls, *o, **k):
        # make this a singleton. There is only a single
        # reference to the dynamic library.
        if Driver._instance is None:
            Driver._instance = object.__new__(cls)
        return Driver._instance

    def __init__(self):
        if self._need_init:
            ftdi_lib = find_library('ftdi')
            if ftdi_lib is None:
                raise FtdiError('libftdi library not found')
            fdll = CDLL(ftdi_lib)
            # most args/return types are fine with the implicit
            # int/void* which ctypes uses, but some need setting here
            fdll.ftdi_get_error_string.restype = c_char_p
            fdll.ftdi_usb_get_strings.argtypes = (c_void_p, c_void_p,
                                                  c_char_p, c_int,
                                                  c_char_p, c_int,
                                                  c_char_p, c_int)
            self.fdll = fdll
        self._need_init = False

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
        devlistptrtype = POINTER(UsbDevList)
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
                    raise FtdiError(self.fdll.ftdi_get_error_string(byref(ctx)))
                elif res > 0:
                    # take a copy of the dev_list for subsequent list_free
                    dev_list_base = pointer(dev_list_ptr.contents)
                    # traverse the linked list...
                    try:
                        while dev_list_ptr:
                            self.fdll.ftdi_usb_get_strings(byref(ctx),
                                    dev_list_ptr.contents.usb_dev,
                                    manuf, 127, desc, 127, serial, 127)
                            devices.append((manuf.value, desc.value, serial.value))
                            # step to next in linked-list if not
                            dev_list_ptr = cast(dev_list_ptr.contents.next,
                                                devlistptrtype)
                    finally:
                        self.fdll.ftdi_list_free(dev_list_base)
        finally:
            self.fdll.ftdi_deinit(byref(ctx))
        return devices


class Device(object):
    """
    Device([device_id[, mode [, encoding [, lazy_open]]]) -> Device instance

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

    lazy_open - if True, then the device will not be opened immediately - the
      user must perform an explicit open() call prior to other operations.
    """
    def __init__(self, device_id=None, mode="b",
                 encoding="latin1", lazy_open=False,
                 buffer_size=0, interface=None):
        self._opened = False
        self.driver = Driver()
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
        # buffer_size (if not 0) chunks the reads and writes
        # to allow interruption
        self.buffer_size = buffer_size
        # interface can be set for devices which have multiple interface
        # ports (e.g. FT4232, FT2232)
        self.interface = interface
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

        if self.interface is not None:
            self.fdll.ftdi_set_interface(byref(self.ctx), self.interface)

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
            if res == 0:
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
        if rlen == -1:
            raise FtdiError(self.get_error_string())
        byte_data = buf.raw[:rlen]

        return byte_data

    def read(self, length):
        """
        read(length) -> bytes/string of up to `length` bytes.

        read upto `length` bytes from the FTDI device
        return type depends on self.mode - if 'b' return
        raw bytes, else decode according to self.encoding
        """
        if not self._opened:
            raise FtdiError("read() on closed Device")

        # read the data
        if self.buffer_size != 0:
            remaining = length
            byte_data_list = []
            while remaining > 0:
                rx_bytes = self._read(min(remaining, self.buffer_size))
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
        """
        buf = create_string_buffer(byte_data)
        written = self.fdll.ftdi_write_data(byref(self.ctx),
                                            byref(buf), len(byte_data))
        return written

    def write(self, data):
        """
        write(data) -> count of bytes actually written

        write given `data` string to the FTDI device
        returns count of bytes written, which may be less than `len(data)`
        """
        if not self._opened:
            raise FtdiError("read() on closed Device")

        try:
            byte_data = bytes(data)
        except TypeError:
            # this will happen if we are Python3 and data is a str.
            byte_data = data.encode(self.encoding)

        # actually write it
        if self.buffer_size != 0:
            remaining = len(byte_data)
            written = 0
            while remaining > 0:
                start = written
                length = min(remaining, self.buffer_size)
                result = self._write(byte_data[start: start + length])
                if result == -1:
                    written == result
                    break
                elif result == 0:
                    # don't continue to try writing forever if nothing
                    # is actually being written
                    break
                else:
                    written += result
                    remaining -= result
        else:
            written = self._write(byte_data)
        if written == -1:
            raise FtdiError(self.get_error_string())
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
        "return error string from libftdi driver"
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
        >>>     # set 8 bit data, 2 stop bits, no parity
        >>>     dev.ftdi_fn.ftdi_set_line_property(8, 2, 0)
        >>>     ...
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
        >>>     dev.write('Hello World!')
        >>>
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
