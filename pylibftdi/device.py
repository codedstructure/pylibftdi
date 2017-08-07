"""
pylibftdi.device - access to individual FTDI devices

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import os
import codecs
import functools
import itertools

from ctypes import (byref, create_string_buffer, c_char_p,
                    c_void_p, Structure, cast, POINTER)

from pylibftdi._base import FtdiError
from pylibftdi.driver import (
    Driver, USB_VID_LIST, USB_PID_LIST,
    FTDI_ERROR_DEVICE_NOT_FOUND, BITMODE_RESET,
    FLUSH_BOTH, FLUSH_INPUT, FLUSH_OUTPUT)


# The only part of the ftdi context we need at this point is
# libusb_device_handle, so we don't encode the entire structure.
class ftdi_context_partial(Structure):
    _fields_ = [('libusb_context', c_void_p),
                ('libusb_device_handle', c_void_p)]


class Device(object):
    """
    Represents a connection to a single FTDI device
    """

    def __init__(self, device_id=None, mode="b",
                 encoding="latin1", lazy_open=False,
                 chunk_size=0, interface_select=None,
                 device_index=0, auto_detach=True, **kwargs):
        """
        Device([device_id[, mode, [OPTIONS ...]]) -> Device instance

        represents a single FTDI device accessible via the libftdi driver.
        Supports a basic file-like interface (open/close/read/write, context
        manager support).

        :param device_id: an optional serial number of the device to open.
            if omitted, this refers to the first device found, which is
            convenient if only one device is attached, but otherwise
            fairly useless.

        :param mode: either 'b' (binary) or 't' (text). This primarily affects
            Python 3 calls to read() and write(), which will accept/return
            unicode strings which will be encoded/decoded according to the given...

        :param encoding: the codec name to be used for text operations.

        :param lazy_open: if True, then the device will not be opened immediately -
            the user must perform an explicit open() call prior to other
            operations.

        :param chunk_size: if non-zero, split read and write operations into chunks
            of this size. With large or slow accesses, interruptions (i.e.
            KeyboardInterrupt) may not happen in a timely fashion.

        :param interface_select: select interface to use on multi-interface devices

        :param device_index: optional index of the device to open, in the
            event of multiple matches for other parameters (PID, VID,
            device_id). Defaults to zero (the first device found).

        :param auto_detach: default True, whether to automatically re-attach
            the kernel driver on device close.
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
        self.mode = mode
        # when giving a str to Device.write(), it is encoded.
        # default is latin1, because it provides
        # a one-to-one correspondence for code points 0-FF
        self.encoding = encoding
        self.encoder = codecs.getincrementalencoder(self.encoding)()
        self.decoder = codecs.getincrementaldecoder(self.encoding)()
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
        # device_index is an optional integer index of device to choose
        self.device_index = device_index
        # auto_detach is a flag to call libusb_set_auto_detach_kernel_driver
        # when we open the device
        self.auto_detach = auto_detach
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
        res = self._open_device()

        if res != 0:
            msg = "%s (%d)" % (self.get_error_string(), res)
            # free the context
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
            raise FtdiError(msg)

        if self.auto_detach:
            ctx_p = cast(byref(self.ctx), POINTER(ftdi_context_partial)).contents
            dev = ctx_p.libusb_device_handle
            if dev:
                self.driver._libusb.libusb_set_auto_detach_kernel_driver(dev, 1)

        # explicitly reset the device to serial mode with standard settings
        # - no flow control, 9600 baud - in case it had previously been used
        # in bitbang mode (some later driver versions might do bits of this
        # automatically)
        self.ftdi_fn.ftdi_set_bitmode(0, BITMODE_RESET)
        self.ftdi_fn.ftdi_setflowctrl(0)
        self.baudrate = 9600
        # reset the latency timer to 16ms (device default, but kernel device
        # drivers can set a different - e.g. 1ms - value)
        self.ftdi_fn.ftdi_set_latency_timer(16)
        self._opened = True

    def _open_device(self):
        """
        Actually open the target device

        :return: status of the open command (0 = success)
        :rtype: int
        """
        # FTDI vendor/product ids required here.
        res = None
        for usb_vid, usb_pid in itertools.product(USB_VID_LIST, USB_PID_LIST):
            open_args = [byref(self.ctx), usb_vid, usb_pid,
                         0, 0, self.device_index]
            if self.device_id is None:
                res = self.fdll.ftdi_usb_open_desc_index(*tuple(open_args))
            else:
                # attempt to match device_id to serial number
                open_args[-2] = c_char_p(self.device_id.encode('latin1'))
                res = self.fdll.ftdi_usb_open_desc_index(*tuple(open_args))
                if res != 0:
                    # swap (description, serial) parameters and try again
                    #  - attempt to match device_id to description
                    open_args[-3], open_args[-2] = open_args[-2], open_args[-3]
                    res = self.fdll.ftdi_usb_open_desc_index(*tuple(open_args))
            if res != FTDI_ERROR_DEVICE_NOT_FOUND:
                # if we succeed (0) or get a specific error, don't continue
                # otherwise (-3) - look for another device
                break

        return res

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
        result = self.fdll.ftdi_set_baudrate(byref(self.ctx), value)
        if result == 0:
            self._baudrate = value

    def _read(self, length):
        """
        actually do the low level reading

        :return: bytes read from the device
        :rtype: bytes
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
            return self.decoder.decode(byte_data)

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
            byte_data = self.encoder.encode(data)

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

        :param flush_what: select what to flush:
            `FLUSH_BOTH` (default);
            `FLUSH_INPUT` (just the rx buffer);
            `FLUSH_OUTPUT` (just the tx buffer)
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
            lines.extend(string_blob.splitlines())

        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines

    def writelines(self, lines):
        """
        writelines for file-like compatibility.

        :param lines: sequence of lines to write
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
