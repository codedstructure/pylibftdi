#!/usr/bin/python -u
"""
test serial loopback; assumes Rx and Tx are connected

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

import os
import sys
import time

from pylibftdi import Device


# TODO:
# make this threaded - a writer stream, which sends known data with
# occasional sync blocks, and a reader which reads and waits for a sync-block
# then signals the writer if it gets stuck.

def test_string(length):
    return os.urandom(length)


class LoopbackTester(object):
    def __init__(self):
        self.device = Device()

    def test_loopback(self, lengths):
        self.device.flush()
        time.sleep(0.1)
        for l in lengths:
            test_str = test_string(l)
            if self.device.write(test_str) != len(test_str):
                sys.stdout.write('*')
            time.sleep(0.1)
            result = ''
            for _ in range(3):
                result = self.device.read(l)
                if result:
                    break
            if result != test_str:
                self.device.flush()
                time.sleep(0.25)
            yield result == test_str

    def main(self):
        for bd in [9600, 31250, 115200, 1152000]:
            self.device.baudrate = bd

            for result in self.test_loopback(range(1, 50) + range(100, 500, 100) +
                                             range(1000, 5000, 1000)):
                if result:
                    sys.stdout.write('+')
                else:
                    sys.stdout.write('!')
            sys.stdout.write('\n')


if __name__ == '__main__':
    tester = LoopbackTester()
    tester.main()
