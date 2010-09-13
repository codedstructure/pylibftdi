"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi


libftdi can be found at:
 http://www.intra2net.com/en/developer/libftdi/
Neither libftdi or Intra2net are associated with this project;
if something goes wrong here, it's almost definitely my fault
rather than a problem with the libftdi library.
"""

__VERSION__ = "0.1"
__AUTHOR__ = "Ben Bass"



__ALL__ = ['Driver', 'BitBangDriver', 'ALL_OUTPUTS', 'ALL_INPUTS']

from ctypes import *
from ctypes.util import find_library

class DeadParrot(object):
    def __getattribute__(self, key):
        # perhaps we should produce an appropriate quote at random...
        raise TypeError("This object is no more!")
    def __setattr__(self, key, val):
        raise TypeError("This object is no more!")
    def __call__(self, *o, **kw):
        raise TypeError("This object is no more!")


class Driver(object):
    def __init__(self):
        self.ctx = None
        self.fdll = None
        self.opened = False

    def open(self):
        "open connection to a FTDI device"
        if self.opened:
            return self
        # TODO: provide parameter to select required device
        # (if multiple are attached)
        self.fdll = CDLL(find_library('libftdi'))
        # most args/return types are fine with the implicit
        # int/void* which ctypes uses, but some need setting here
        self.fdll.ftdi_get_error_string.restype = c_char_p
        # sizeof(struct ftdi_context) seems to be 112 on x86_64, 84 on i386
        # provide a generous 1K buffer for (hopefully) all possibles...
        self.ctx = create_string_buffer(1024)
        self.fdll.ftdi_init(byref(self.ctx))
        self.fdll.ftdi_usb_open(byref(self.ctx), 0x0403, 0x6001)
        self.opened = True
        return self

    def close(self):
        "close our connection, free resources"
        self.opened = False
        self.fdll.ftdi_usb_close(byref(self.ctx))
        self.fdll.ftdi_deinit(byref(self.ctx))
        self.fdll = DeadParrot()

    def read(self, length):
        "read a string of upto length bytes from the FTDI device"
        z = create_string_buffer(length)
        self.fdll.ftdi_read_data(byref(self.ctx), byref(z), length)
        return z.value

    def write(self, data):
        "write given data string to the FTDI device"
        z = create_string_buffer(data)
        return self.fdll.ftdi_write_data(byref(self.ctx), byref(z), len(data))

    def get_error(self):
        "return error string from libftdi driver"
        return self.fdll.ftdi_get_error_string(self.ctx)

    def __enter__(self):
        "support for context manager"
        return self.open()

    def __exit__(self, exc_type, exc_val, tb):
        "support for context manager"
        self.close()

ALL_OUTPUTS = 0xFF
ALL_INPUTS = 0x00

class BitBangDriver(Driver):
    def __init__(self, direction = ALL_OUTPUTS):
        super(BitBangDriver, self).__init__()
        self.direction = direction

    @property
    def direction(self):
        return self._direction
    @direction.setter
    def direction(self, dir):
        self._direction = dir
        if self.opened:
            self.fdll.ftdi_set_bitmode(byref(self.ctx), dir, 0x01)

    def open(self):
        super(BitBangDriver, self).open()
        if self._direction:
            self.direction = self._direction
        return self

    def read(self):
        return ord(super(BitBangDriver, self).read(1)[0])

    def write(self, value):
        return super(BitBangDriver, self).write(chr(value))