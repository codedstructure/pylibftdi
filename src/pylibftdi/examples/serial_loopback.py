#!/usr/bin/env python3 -u
"""
test serial loopback; assumes Rx and Tx are connected

Copyright (c) 2010-2020 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

import os
import sys
import time

from pylibftdi import SerialDevice


def test_string(length):
    return os.urandom(length)


class LoopbackTester:
    def __init__(self):
        self.device = SerialDevice(chunk_size=16)

    def test_loopback(self, length):
        test_str = test_string(length)
        if self.device.write(test_str) != len(test_str):
            sys.stdout.write("*")
        time.sleep(0.1)
        result = ""
        for _ in range(5):
            result = self.device.read(length)
            time.sleep(0.1)
            if result:
                break
        if result != test_str:
            self.device.flush()
            time.sleep(0.25)
        return result == test_str

    def test_iter(self, lengths):
        self.device.flush()
        time.sleep(0.1)
        for length in lengths:
            yield self.test_loopback(length)

    def bisect(self):
        xmin, xmax = 1, 5000
        last_test = None
        while True:
            test = (xmin + xmax) // 2
            if test == last_test:
                break
            if self.test_loopback(test):
                xmin = test
            else:
                xmax = test
            last_test = test
        return test

    def main(self):
        print("Determining largest non-streamed buffer size")
        for bd in [9600, 31250, 115200, 1152000]:
            print(f"Baudrate: {bd}")
            self.device.baudrate = bd
            result = self.bisect()
            print(f"Buffer size: {result}")


if __name__ == "__main__":
    tester = LoopbackTester()
    tester.main()
