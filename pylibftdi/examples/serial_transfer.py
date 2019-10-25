#!/usr/bin/python -u
"""
test serial transfer between two devices

This module assumes two devices (e.g. FT232R based) are connected to the
host computer, with RX and TX of the two devices wired to each other so
they can communicate. It launches threads to send and receive traffic and
check that a random stream sent from one device is correctly received at
the other:

Testing 9600 baud
Half duplex d1->d2...
  Bytes TX: 10000  RX: 10000
  Checksum TX: ad7e985fdddfbc04e398daa781a9fad0  RX: ad7e985fdddfbc04e398daa781a9fad0
 SUCCESS
Half duplex d2->d1...
  Bytes TX: 10000  RX: 10000
  Checksum TX: 61338c11fe18642a07f196094646295f  RX: 61338c11fe18642a07f196094646295f
 SUCCESS
Full duplex d1<=>d2...
  Bytes TX: 10000  RX: 10000
  Checksum TX: 7dcc7ed3b89e46592c777ec42c330fd8  RX: 7dcc7ed3b89e46592c777ec42c330fd8
 SUCCESS
  Bytes TX: 10000  RX: 10000
  Checksum TX: 1a957192b8219aa02ad374dd518e37fd  RX: 1a957192b8219aa02ad374dd518e37fd
 SUCCESS

Copyright (c) 2015-2017 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

import time
import random
import hashlib
import threading
from itertools import islice

from pylibftdi import Device, FtdiError


class RandomStream(object):
    """
    Infinite iterator of random data which can be queried at any point
    for the checksum of the data already yielded
    """

    def __init__(self, block_size=1024):
        self._block_size = block_size
        # Note: `reset()` sets the initial attributes
        self.reset()

    @staticmethod
    def _rand_gen(size):
        """Return a `bytes` instance of `size` random byte"""
        return bytes(bytearray(random.getrandbits(8) for _ in range(size)))

    def reset(self):
        self.stream_hash = hashlib.md5()
        self.rand_buf = self._rand_gen(self._block_size)
        self.chk_tail = self.chk_head = 0
        self.bytecount = 0

    def _update_checksum(self):
        self.stream_hash.update(self.rand_buf[self.chk_tail:self.chk_head])
        self.chk_tail = self.chk_head

    def checksum(self):
        self._update_checksum()
        return self.stream_hash.hexdigest()

    def __iter__(self):
        while True:
            # Use slice rather than index to avoid bytes->int conversion
            # in Python3
            data = self.rand_buf[self.chk_head:self.chk_head+1:]
            self.chk_head += 1
            self.bytecount += 1
            yield data
            if self.chk_head == self._block_size:
                self._update_checksum()
                self.rand_buf = self._rand_gen(self._block_size)
                self.chk_head = self.chk_tail = 0


def test_rs():
    r = RandomStream()
    prev_checksum = 0
    stream_bytes = []
    for i in range(30):
        stream_bytes.append(b''.join(islice(r, 500)))
        assert r.checksum() != prev_checksum
    assert r.checksum() == r.checksum()
    assert hashlib.md5(b''.join(stream_bytes)).hexdigest() == r.checksum()


class HalfDuplexTransfer(object):
    """
    Test streaming bytes from one device to another
    """

    def __init__(self, source, dest, baudrate=9600, block_size=500):
        """
        Prepare for half-duplex transmission from source device to dest
        """
        self.source = source
        self.dest = dest
        self.source.baudrate = baudrate
        self.dest.baudrate = baudrate

        self.target = []
        self.wait_signal = threading.Event()
        self.running = threading.Event()

        self.rs = RandomStream()

        self.block_size = block_size
        self.test_duration = 10

        self.t1 = None
        self.t2 = None

        self.done = False

    def reader(self):
        # Tell writer we're ready for the deluge...
        self.wait_signal.set()

        # if we've just finished reading when self.done get's set by the
        # writer, we won't get the 'last' packet. But if we assume there's
        # always one more after done gets set, we'll get some ReadTimeouts....
        # Probably best to try one more time but catch & ignore ReadTimeout.
        while not self.done:
            data = self.dest.read(1024)
            self.target.append(data)

        try:
            data = self.dest.read(1024)
            self.target.append(data)
        except FtdiError:
            pass

    def writer(self):
        self.running.set()
        self.wait_signal.wait()

        end_time = time.time() + self.test_duration

        while time.time() < end_time:
            x = b''.join(list(islice(self.rs, self.block_size)))
            self.source.write(x)

        # Wait for the reader to catch up
        time.sleep(0.01)
        self.done = True

    def go(self, test_duration=None):
        if test_duration is not None:
            self.test_duration = test_duration

        self.t1 = threading.Thread(target=self.writer)
        self.t1.daemon = True
        self.t1.start()

        # We wait for the writer to be actually running (but not yet
        # writing anything) before we start the reader.
        self.running.wait()
        self.t2 = threading.Thread(target=self.reader)
        self.t2.daemon = True
        self.t2.start()

    def join(self):
        # Use of a timeout allows Ctrl-C interruption
        self.t1.join(timeout=1e6)
        self.t2.join(timeout=1e6)

    def results(self):
        result = b''.join(self.target)
        print("  Bytes TX: {}  RX: {}".format(self.rs.bytecount, len(result)))
        rx_chksum = hashlib.md5(b''.join(self.target)).hexdigest()
        print("  Checksum TX: {}  RX: {}".format(self.rs.checksum(), rx_chksum))
        if len(result) == self.rs.bytecount and self.rs.checksum() == rx_chksum:
            print(" SUCCESS")
        else:
            print(" FAIL")


def test_half_duplex_transfer(d1, d2, baudrate=9600):
    """
    Test half-duplex stream from d1 to d2, report on status
    """
    hd = HalfDuplexTransfer(d1, d2, baudrate)
    hd.go()
    hd.join()
    hd.results()


def test_full_duplex_transfer(d1, d2, baudrate=9600):
    """
    Start two half-duplex streams in opposite directions at the
    same time, check both are OK
    """
    hd1 = HalfDuplexTransfer(d1, d2, baudrate)
    hd1.go()
    hd2 = HalfDuplexTransfer(d2, d1, baudrate)
    hd2.go()
    hd1.join()
    hd1.results()
    hd2.join()
    hd2.results()


def main():
    d1 = Device(device_index=0)
    d2 = Device(device_index=1)

    for b in 9600, 38400, 115200:
        print("Testing {} baud".format(b))
        d1.flush()
        d2.flush()
        print("Half duplex d1->d2...")
        test_half_duplex_transfer(d1, d2, baudrate=b)
        d1.flush()
        d2.flush()
        print("Half duplex d2->d1...")
        test_half_duplex_transfer(d2, d1, baudrate=b)
        d1.flush()
        d2.flush()
        print("Full duplex d1<=>d2...")
        test_full_duplex_transfer(d1, d2, baudrate=b)


if __name__ == '__main__':
    test_rs()
    main()
