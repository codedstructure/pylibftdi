"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

import functools
# be disciplined so pyflakes can check us...
from ctypes import (CDLL, byref, c_char_p, create_string_buffer)
from ctypes.util import find_library

from pylibftdi._base import ParrotEgg, DeadParrot, FtdiError

class Driver(object):
    """
    This is where it all happens...
    We load the libftdi library, and use it.
    """
    def __init__(self, mode="b", encoding="latin1"):
        self.ctx = None
        self.fdll = ParrotEgg()
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

    def open(self):
        "open connection to a FTDI device"
        if self.opened:
            return
        # TODO: provide parameter to select required device
        # (if multiple are attached)
        ftdi_lib = find_library('ftdi')
        if ftdi_lib is None:
            raise FtdiError('libftdi library not found')
        fdll = CDLL(ftdi_lib)
        # most args/return types are fine with the implicit
        # int/void* which ctypes uses, but some need setting here
        fdll.ftdi_get_error_string.restype = c_char_p
        # Try to open the device.  If this fails, reset things to how
        # they were, but we can't use self.close as that assumes things
        # have already been setup.
        # sizeof(struct ftdi_context) seems to be 112 on x86_64, 84 on i386
        # provide a generous 1K buffer for (hopefully) all possibles...
        self.ctx = create_string_buffer(1024)
        if fdll.ftdi_init(byref(self.ctx)) != 0:
            raise FtdiError(fdll.ftdi_get_error_string(byref(self.ctx)))
        # FTDI vendor/product ids required here.
        if fdll.ftdi_usb_open(byref(self.ctx), 0x0403, 0x6001) != 0:
            fdll.ftdi_deinit(byref(self.ctx))
            raise FtdiError(fdll.ftdi_get_error_string(byref(self.ctx)))
        # only at this point do we allow other things to access fdll.
        # (so if exception is thrown above, there is no access).
        # - maybe this should all be in the constructor. RAII, you know.
        #   (except we don't have deterministic destructors. oh well.)
        self.fdll = fdll
        self.opened = True

    def close(self):
        "close our connection, free resources"
        self.opened = False
        if self.fdll.ftdi_usb_close(byref(self.ctx)) == 0:
            self.fdll.ftdi_deinit(byref(self.ctx))
        self.fdll = DeadParrot()


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
        in a nicely encapsulated way:
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

