"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

# The Bus descriptor class is probably useful outside of
# pylibftdi.  It tries to be to Python what bitfields are
# to C. Its only requirement (which is fairly pylibftdi-ish)
# is a 'driver' attribute on the object this is attached
# to, which has a 'port' property which is readable and
# writable.


class Bus(object):
    """
    This class is a descriptor for a bus of a given width starting
    at a given offset (0 = LSB).  The driver which does the actual
    reading and writing is assumed to be a BitBangDriver instance
    in the 'driver' attribute of the object to which this is attached.
    """
    def __init__(self, offset, width=1):
        self.offset = offset
        self.width = width
        self._mask = ((1 << width) - 1)

    def __get__(self, obj, type):
        val = obj.driver.port
        return (val >> self.offset) & self._mask

    def __set__(self, obj, value):
        value = value & self._mask
        # in a multi-threaded environment, would
        # want to ensure following was locked, eg
        # by acquiring a driver lock
        val = obj.driver.port
        val &= ~(self._mask << self.offset)
        val |= value << self.offset
        obj.driver.port = val
