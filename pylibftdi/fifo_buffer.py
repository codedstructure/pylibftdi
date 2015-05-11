"""
fifo_buffer - provides an unbounded fifo buffer for reading and writing
bytestrings or text to and from a device

@codedstructure 2015
"""

import threading
from collections import deque

try:
    from collections.abc import Sized
except ImportError:
    from collections import Sized


class FifoBuffer(object):
    """
    A FIFO buffer for streaming bytes
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
