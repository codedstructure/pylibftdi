"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

from pylibftdi.driver import Device, FtdiError
from ctypes import c_ubyte, byref

ALL_OUTPUTS = 0xFF
ALL_INPUTS = 0x00
BB_OUTPUT = 1
BB_INPUT = 0


class BitBangDevice(Device):
    """
    simple subclass to support bit-bang mode

    Internally uses async mode at the moment, but provides a 'sync'
    flag (defaulting to True) which controls the behaviour of port
    reading and writing - if set, the FIFOs are ignored (read) or
    cleared (write) so operations will appear synchronous

    Adds two read/write properties to the base class:
     direction: 8 bit input(0)/output(1) direction control.
     port: 8 bit IO port, as defined by direction.
    """
    def __init__(self,
                 device_id=None,
                 direction=ALL_OUTPUTS,
                 lazy_open=False,
                 sync=True):
        # initialise the super-class, but don't open yet. We really want
        # two-part initialisation here - set up all the instance variables
        # here in the super class, then open it after having set more
        # of our own variables.
        super(BitBangDevice, self).__init__(device_id=device_id,
                                            mode='b',
                                            lazy_open=True)
        self.direction = direction
        self.sync = sync
        self._last_set_dir = None
        self._latch = 0
        if not lazy_open:
            self.open()

    def open(self):
        "open connection to a FTDI device"
        # in case someone sets the direction before we are open()ed,
        # we intercept this call...
        super(BitBangDevice, self).open()
        if self.direction != self._last_set_dir:
            self.direction = self._direction
        return self

    # direction property - 8 bit value determining whether an IO line
    # is output (if set to 1) or input (set to 0)
    @property
    def direction(self):
        """
        get or set the direction of each of the IO lines. LSB=D0, MSB=D7
        1 for output, 0 for input
        """
        return self._direction

    @direction.setter
    def direction(self, dir):
        if not (0 <= dir <= 255):
            raise FtdiError("invalid direction bitmask")
        self._direction = dir
        if not self.closed:
            self.ftdi_fn.ftdi_set_bitmode(dir, 0x01)
            self._last_set_dir = dir

    # port property - 8 bit read/write value
    @property
    def port(self):
        """
        get or set the state of the IO lines.  The value of output
        lines is persisted in this object for the purposes of reading,
        so read-modify-write operations (e.g. drv.port+=1) are valid.
        """
        if self.sync:
            pin_byte = c_ubyte()
            res = self.fdll.ftdi_read_pins(self.ctx, byref(pin_byte))
            if res != 0:
                raise FtdiError("Could not read device pins")
            result = pin_byte.value
        else:
            # the coercion to bytearray here is to make this work
            # transparently between Python2 and Python3 - equivalent
            # of ord() for Python2, a time-wasting do-nothing on Python3
            result = bytearray(super(BitBangDevice, self).read(1))[0]

        # replace the 'output' bits with current value of _latch -
        # the last written value. This makes read-modify-write
        # operations (e.g. 'drv.port |= 0x10') work as expected
        result = (result & ~self._direction) | (self._latch & self._direction)
        return result

    @port.setter
    def port(self, value):
        self._latch = value
        if self.sync:
            self.flush_output()
        return super(BitBangDevice, self).write(chr(value))
