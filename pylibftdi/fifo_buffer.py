"""
fifo_buffer - provides an unbounded fifo buffer for reading and writing
bytestrings or text to and from a device

@codedstructure 2015
"""

from collections import deque

try:
    from collections.abc import Sized
except ImportError:
    from collections import Sized


class FifoBuffer(deque):
    joiner = b''

    def extract(self, length):
        """
        Read 'length' bytes from the fifo
        """
        i = 0
        result = []
        while i < length:
            if self:
                item = self.popleft()
                i += len(item)
                result.append(item)
            else:
                break
        result_str = self.joiner.join(result)
        result_str, excess = result_str[:length], result_str[length:]
        if excess:
            self.appendleft(excess)
        return result_str

    def insert(self, data):
        """
        Insert given data string into the fifo
        """
        if isinstance(data, Sized):
            self.append(data)
        else:
            raise ValueError("Sized sequences only")

    def __len__(self):
        return sum(len(x) for x in self)


class FifoTextBuffer(FifoBuffer):
    joiner = u''
