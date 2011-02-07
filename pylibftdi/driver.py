"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

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
        [('ftdi', 'um245r', 'fte00p4l'),
         ('ftdi', 'um232r usb <-> serial', 'fte4ffvq')]

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

        ctx = create_string_buffer(1024)
        self.fdll.ftdi_init(byref(ctx))

        try:
            res = self.fdll.ftdi_usb_find_all(byref(ctx), byref(dev_list_ptr), 0x0403, 0x6001)
            if res < 0:
                raise FtdiError(self.fdll.ftdi_get_error_string(byref(ctx)))
            elif res > 0:
                # take a copy of the dev_list for subsequent list_free
                dev_list_base = pointer(dev_list_ptr.contents)
                # traverse the linked list...
                try:
                    while dev_list_ptr:
                        self.fdll.ftdi_usb_get_strings(byref(ctx), dev_list_ptr.contents.usb_dev,
                                manuf,127, desc,127, serial,127)
                        devices.append((manuf.value, desc.value, serial.value))
                        # step to next in linked-list if not
                        dev_list_ptr = cast(dev_list_ptr.contents.next, devlistptrtype)
                finally:
                    self.fdll.ftdi_list_free(dev_list_base)
        finally:
            self.fdll.ftdi_deinit(byref(ctx))
        return devices

class Device(object):
    def __init__(self, mode="b", encoding="latin1"):
        self.driver = Driver()
        self.fdll = self.driver.fdll
        self.opened = False
        # mode can be either 'b' for binary, or 't' for text.
        # if set to text, the values returned from read() will
        # be decoded using encoding before being returned as
        # strings; for binary the raw bytes will be returned.
        # This will only affect Python3.
        self.mode = mode
        # when giving a str to Driver.write(), it is encoded.
        # default is latin1, because it provides
        # a one-to-one correspondence for code points 0-FF
        self.encoding = encoding
        # ftdi_usb_open_dev initialises the device baudrate
        # to 9600, which certainly seems to be a de-facto
        # standard for serial devices.
        self._baudrate = 9600

    def __del__(self):
        "tell driver to free the ftdi_context resource"
        if self.opened:
            self.close()

    def open(self, device_id=None):
        """open connection to a FTDI device
        device_id: [optional] serial number (string) of device to be opened
        """
        if self.opened:
            return

        # create context for this device
        self.ctx = create_string_buffer(1024)
        if self.fdll.ftdi_init(byref(self.ctx)) != 0:
            msg = self.get_error_string()
            del self.ctx
            raise FtdiError(msg)

        # Try to open the device.  If this fails, reset things to how
        # they were, but we can't use self.close as that assumes things
        # have already been setup.
        # FTDI vendor/product ids required here.
        open_args = [byref(self.ctx), 0x0403, 0x6001]
        if device_id is None:
            res = self.fdll.ftdi_usb_open(*tuple(open_args))
        else:
            open_args.extend([0, c_char_p(device_id.encode('latin1'))])
            res = self.fdll.ftdi_usb_open_desc(*tuple(open_args))

        if res != 0:
            msg = self.get_error_string()
            # free the context
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
            raise FtdiError(msg)

        self.opened = True

    def close(self):
        "close our connection, free resources"
        if self.opened:
            self.fdll.ftdi_deinit(byref(self.ctx))
            del self.ctx
        self.opened = False

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


    def read(self, length):
        """
        read upto length bytes from the FTDI device
        return type depends on self.mode - if 'b' return
        raw bytes, else decode according to self.encoding
        """
        buf = create_string_buffer(length)
        rlen = self.fdll.ftdi_read_data(byref(self.ctx), byref(buf), length)
        if rlen == -1:
            raise FtdiError(self.get_error_string())
        byte_data = buf.raw[:rlen]
        if self.mode == 'b':
            return byte_data
        else:
            return byte_data.decode(self.encoding)

    def write(self, data):
        "write given data string to the FTDI device"
        try:
            byte_data = bytes(data)
        except TypeError:
            # this will happen if we are Python3 and data is a str.
            byte_data = data.encode(self.encoding)
        buf = create_string_buffer(byte_data)
        written = self.fdll.ftdi_write_data(byref(self.ctx),
                                            byref(buf), len(data))
        if written == -1:
            raise FtdiError(self.get_error_string())
        return written


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

        >>> with Driver() as drv:
        >>>     # set 8 bit data, 2 stop bits, no parity
        >>>     drv.ftdi_fn.ftdi_set_line_property(8, 2, 0)
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
        Note the driver is opened and closed automatically
        when used in a with statement, and the driver object
        itself is returned:
        >>> with Driver(mode='t') as drv:
        >>>     drv.write('Hello World!')
        >>>
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, tb):
        "support for context manager"
        self.close()

