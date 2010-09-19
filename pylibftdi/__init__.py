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

__VERSION__ = "0.4.1"
__AUTHOR__ = "Ben Bass"


__ALL__ = ['Driver', 'BitBangDriver', 'Bus', 'ALL_OUTPUTS', 'ALL_INPUTS']

import functools
from ctypes import *
from ctypes.util import find_library

class Refuser(object):
    def __getattribute__(self, key):
        # perhaps we should produce an appropriate quote at random...
        raise TypeError(object.__getattribute__(self, 'message'))
    def __setattr__(self, key, val):
        raise TypeError(object.__getattribute__(self, 'message'))
    def __call__(self, *o, **kw):
        raise TypeError(object.__getattribute__(self, 'message'))

class ParrotEgg(Refuser):
    message = "This object is not yet... (missing open()?)"

class DeadParrot(Refuser):
    message = "This object is no more!"

class FtdiError(Exception):
    pass

class Driver(object):
    def __init__(self):
        self.ctx = None
        self.fdll = ParrotEgg()
        self.opened = False
        # ftdi_usb_open_dev initialises the device baudrate
        # to 9600, which certainly seems to be a de-facto
        # standard for serial devices.
        self._baudrate = 9600

    def open(self):
        "open connection to a FTDI device"
        if self.opened:
            return self
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
        if fdll.ftdi_usb_open(byref(self.ctx), 0x0403, 0x6001) != 0:
            fdll.ftdi_deinit(byref(self.ctx))
            raise FtdiError(fdll.ftdi_get_error_string(byref(self.ctx)))
        # only at this point do we allow other things to access fdll.
        # (so if exception is thrown above, there is no access).
        self.fdll = fdll
        self.opened = True
        return self

    def close(self):
        "close our connection, free resources"
        self.opened = False
        if self.fdll.ftdi_usb_close(byref(self.ctx)) == 0:
            self.fdll.ftdi_deinit(byref(self.ctx))
        self.fdll = DeadParrot()

    @property
    def baudrate(self):
        return self._baudrate
    @baudrate.setter
    def baudrate(self, value):
        result = self.fdll.ftdi_set_baudrate(byref(self.ctx), value)
        if result == 0:
            self._baudrate = value

    def read(self, length):
        "read a string of upto length bytes from the FTDI device"
        buf = create_string_buffer(length)
        rlen = self.fdll.ftdi_read_data(byref(self.ctx), byref(buf), length)
        if rlen == -1:
            raise FtdiError(self.get_error_string())
        return buf.raw[:rlen]

    def write(self, data):
        "write given data string to the FTDI device"
        buf = create_string_buffer(data)
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
        >>> with FtdiDriver() as drv:
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
        "support for context manager"
        return self.open()

    def __exit__(self, exc_type, exc_val, tb):
        "support for context manager"
        self.close()

ALL_OUTPUTS = 0xFF
ALL_INPUTS = 0x00

class BitBangDriver(Driver):
    """
    simple subclass to support bit-bang mode
    
    Only uses async mode at the moment.
    
    Adds two read/write properties to the base class:
     direction: 8 bit input(0)/output(1) direction control.
     port: 8 bit IO port, as defined by direction.
    """
    def __init__(self, direction = ALL_OUTPUTS):
        super(BitBangDriver, self).__init__()
        self.direction = direction
        self._latch = 0

    def open(self):
        # in case someone sets the direction before we are open()ed,
        # we intercept this call...
        super(BitBangDriver, self).open()
        if self._direction:
            self.direction = self._direction
        return self

    @property
    def direction(self):
        return self._direction
    @direction.setter
    def direction(self, dir):
        assert 0 <= dir <= 255, 'invalid direction bitmask'
        self._direction = dir
        if self.opened:
            self.fdll.ftdi_set_bitmode(byref(self.ctx), dir, 0x01)

    @property
    def port(self):
        result = ord(super(BitBangDriver, self).read(1)[0])
        # replace the 'output' bits with current value of _latch -
        # the last written value. This makes read-modify-write
        # operations (e.g. 'drv.port |= 0x10') work as expected
        result = (result & ~self._direction) | (self._latch & self._direction)
        return result
    @port.setter
    def port(self, value):
        self._latch = value
        return super(BitBangDriver, self).write(chr(value))


class Bus(object):
    """
    This class is a descriptor for a bus of a given width starting
    at a given offset (0 = LSB).  Thet driver which does the actual
    reading and writing is assumed to be a BitBangDriver instance
    in the 'driver' attribute of the object to which this is attached.
    """
    def __init__(self, offset, width=1):
        self.offset = offset
        self.width = width
        self._mask = ((1<<width)-1)

    def __get__(self, obj, type):
        val = obj.driver.port
        return (val >> offset) & self._mask

    def __set__(self, obj, value):
        value = value & self._mask
        # in a multi-threaded environment, would
        # want to ensure following was locked, eg
        # by acquiring a driver lock
        val = obj.driver.port
        val &= ~(self._mask << self.offset)
        val |= value << self.offset
        obj.driver.port = val
