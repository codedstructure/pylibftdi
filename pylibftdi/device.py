"""
pylibftdi.device - access to individual FTDI devices

Copyright (c) 2010-2018 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import os
import sys
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


ERR_HELP_NOT_FOUND_FAIL = """
No device matching the given specification could be found.
Is the device connected?

Try running the following command to see if the device is listed:

    python -m pylibftdi.examples.list_devices
"""

ERR_HELP_LINUX_OPEN_FAIL = """
Could not access the FTDI device - this could be a permissions
issue accessing the device.

If the program works when run with root privileges (i.e. sudo)
this is likely to be the issue. Running as a normal user should
be possible by setting appropriate udev rules on the device.
"""

ERR_HELP_CLAIM_FAIL = """
Could not claim the FTDI USB device - either the device is
already open, or another driver is preventing libftdi from
claiming the device.
"""

ERR_HELP_LINUX_CLAIM_FAIL = ERR_HELP_CLAIM_FAIL + """
The Linux `ftdi_sio` driver is often the culprit here, and may be
unloaded with `sudo rmmod ftdi_sio`. However in recent libftdi
versions this should not be necessary, as a driver option to
switch out the driver temporarily is applied (unless
`auto_detach=False` is given in `Device` instantiation).
"""

ERR_HELP_MACOS_CLAIM_FAIL = ERR_HELP_CLAIM_FAIL + """
The following commands may be attempted in the terminal to unload
the builtin drivers:

    sudo kextunload -bundle-id com.apple.driver.AppleUSBFTDI
    sudo kextunload -bundle-id com.FTDI.driver.FTDIUSBSerialDriver

Reload these with the command 'kextload' replacing 'kextunload' above.

Note the second of these will only be present if the FTDI-provided
driver has been installed from their website:

    https://www.ftdichip.com/Drivers/VCP.htm
"""


# The only part of the ftdi context we need at this point is
# libusb_device_handle, so we don't encode the entire structure.
# Note the structure for 0.x is different (no libusb_context
# member), but we don't support auto_detach on 0.x which is
# the only case this is used.
class ftdi_context_partial(Structure):
    # This is for libftdi 1.0+
    _fields_ = [('libusb_context', c_void_p),
                ('libusb_device_handle', c_void_p)]


class Device(object):
    """
    Represents a connection to a single FTDI device
    """

    # If false, don't open the device as part of instantiation
    lazy_open = False

    # chunk_size (if not 0) chunks the reads and writes
    # to allow interruption
    chunk_size = 0

    # auto_detach is a flag to call libusb_set_auto_detach_kernel_driver
    # when we open the device
    auto_detach = True

    # defining softspace allows us to 'print' to this device
    softspace = 0

    def __init__(self, device_id=None, mode="b",
                 encoding="latin1", interface_select=None,
                 device_index=0, **kwargs):
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

        :param interface_select: select interface to use on multi-interface devices

        :param device_index: optional index of the device to open, in the
            event of multiple matches for other parameters (PID, VID,
            device_id). Defaults to zero (the first device found).

        The following parameters are only available as keyword parameters
        and override class attributes, so may be specified in subclasses.

        :param lazy_open: if True, then the device will not be opened immediately -
            the user must perform an explicit open() call prior to other
            operations.

        :param chunk_size: if non-zero, split read and write operations into chunks
            of this size. With large or slow accesses, interruptions (i.e.
            KeyboardInterrupt) may not happen in a timely fashion.

        :param auto_detach: default True, whether to automatically re-attach
            the kernel driver on device close.

        :param index: optional index into list_devices() to open.
            Useful in the event that multiple devices of differing VID/PID
            are attached, where `device_index` is insufficient to select
            as device indexing restarts at 0 for each VID/PID combination.
        """
        self._opened = False

        # Some behavioural attributes are extracted from kwargs and override
        # existing attribute defaults. This allows subclassing to easily
        # change these.
        for param in ['auto_detach', 'lazy_open', 'chunk_size']:
            if param in kwargs:
                setattr(self, param, kwargs.pop(param))

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
        # interface can be set for devices which have multiple interface
        # ports (e.g. FT4232, FT2232)
        self.interface_select = interface_select
        # device_index is an optional integer index of device to choose
        self.device_index = device_index
        # list_index (from parameter `index`) is an optional integer index
        # into list_devices() entries.
        self.list_index = kwargs.pop('index', None)

        # lazy_open tells us not to open immediately.
        if not self.lazy_open:
            self.open()

    def __del__(self):
        """free the ftdi_context resource"""
        if self._opened:
            self.close()

    def open(self):
        """
        open connection to a FTDI device
        """
        if self._opened:
            return

        if not self.device_id and self.list_index is not None:
            # Use serial number from list_index
            dev_list = self.driver.list_devices()
            try:
                # The third (index 2) field is serial number.
                self.device_id = dev_list[self.list_index][2]
            except IndexError:
                raise FtdiError("index provided not in range of list_devices() entries")

        # create context for this device
        # Note I gave up on attempts to use ftdi_new/ftdi_free (just using
        # ctx instead of byref(ctx) in first param of most ftdi_* functions) as
        # (at least for 64-bit) they only worked if argtypes was declared
        # (c_void_p for ctx), and that's too much like hard work to maintain.
        # So I've reverted to using create_string_buffer for memory management,
        # byref(ctx) to pass in the context instance, and ftdi_init() /
        # ftdi_deinit() pair to manage the driver resources. It's very nice
        # how layered the libftdi code is, with access to each layer.
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
            msg = self.handle_open_error(res)
            # free the context
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
            raise FtdiError(msg)

        if self.auto_detach and self.driver.libftdi_version().major > 0:
            # This doesn't reliably work on libftdi 0.x, so we ignore it
            ctx_p = cast(byref(self.ctx), POINTER(ftdi_context_partial)).contents
            dev = ctx_p.libusb_device_handle
            if dev:
                self.driver._libusb.libusb_set_auto_detach_kernel_driver(c_void_p(dev), 1)

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

    def handle_open_error(self, errcode):
        """
        return a (hopefully helpful) error message on a failed open()
        """
        err_help = ''
        if errcode == -3:
            err_help = ERR_HELP_NOT_FOUND_FAIL
        elif errcode == -4 and sys.platform == 'linux':
            err_help = ERR_HELP_LINUX_OPEN_FAIL
        elif errcode == -5:
            if sys.platform == 'linux':
                err_help = ERR_HELP_LINUX_CLAIM_FAIL
            elif sys.platform == 'darwin':
                err_help = ERR_HELP_MACOS_CLAIM_FAIL
            else:
                err_help = ERR_HELP_CLAIM_FAIL
        msg = "%s (%d)\n%s" % (self.get_error_string(), errcode, err_help)
        return msg

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
        """close our connection, free resources"""
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
        """support for context manager"""
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
            if next_char == '' or (0 < size < len(line_buffer)):
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
