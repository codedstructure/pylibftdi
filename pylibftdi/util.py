"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

# The Bus descriptor class is probably useful outside of
# pylibftdi.  It tries to be to Python what bitfields are
# to C. Its only requirement (which is fairly pylibftdi-ish)
# is a 'device' attribute on the object this is attached
# to, which has a 'port' property which is readable and
# writable.


class Bus(object):
    """
    This class is a descriptor for a bus of a given width starting
    at a given offset (0 = LSB).  The device which does the actual
    reading and writing is assumed to be a BitBangDevice instance
    in the 'device' attribute of the object to which this is attached.
    """
    def __init__(self, offset, width=1):
        self.offset = offset
        self.width = width
        self._mask = ((1 << width) - 1)

    def __get__(self, obj, type):
        val = obj.device.port
        return (val >> self.offset) & self._mask

    def __set__(self, obj, value):
        value = value & self._mask
        # in a multi-threaded environment, would
        # want to ensure following was locked, eg
        # by acquiring a device lock
        val = obj.device.port
        val &= ~(self._mask << self.offset)
        val |= value << self.offset
        obj.device.port = val


import threading
from collections import deque

try:
    from collections.abc import Sized
except ImportError:
    from collections import Sized


class FifoBuffer(object):
    """
    A FIFO buffer for streaming bytes

    provides an unbounded fifo buffer for reading and writing
    bytestrings or text to and from a device
    """

    def __init__(self):
        self._cond = threading.Condition()
        self._deque = deque()

    def extract(self, length, block=False):
        """
        Read upto 'length' bytes from the fifo

        :param length: - number of bytes to read
        :param block: - block waiting for any data to be ready
        """
        i = 0
        result = []
        while i < length:
            if self._deque:
                item = self._deque.popleft()
                i += len(item)
                result.append(item)
            else:
                if block and not result:
                    with self._cond:
                        if not self._deque:
                            # Use a timeout here to allow Ctrl-C interrupt
                            self._cond.wait(1)
                else:
                    break
        result_str = b''.join(result)
        result_str, excess = result_str[:length], result_str[length:]
        if excess:
            self._deque.appendleft(excess)
        return result_str

    def insert(self, data):
        """
        Insert given data string into the fifo
        """
        if isinstance(data, Sized):
            self._deque.append(data)
        else:
            raise ValueError("Sized sequences only")

        with self._cond:
            self._cond.notify()

    def __len__(self):
        return sum(len(x) for x in self._deque)
