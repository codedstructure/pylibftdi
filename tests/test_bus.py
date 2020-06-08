"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

from tests.test_common import unittest
from pylibftdi.util import Bus


class TestBus(unittest.TestCase):

    class MockDevice(object):
        port = 0

    class Bus1(object):
        a = Bus(0, 2)
        b = Bus(2, 1)
        c = Bus(3, 5)

        def __init__(self):
            self.device = TestBus.MockDevice()

    def test_bus_write(self):
        test_bus = TestBus.Bus1()
        # test writing to the bus
        self.assertEqual(test_bus.device.port, 0)
        test_bus.a = 3
        test_bus.b = 1
        test_bus.c = 31
        self.assertEqual(test_bus.device.port, 255)
        test_bus.b = 0
        self.assertEqual(test_bus.device.port, 251)
        test_bus.c = 16
        self.assertEqual(test_bus.device.port, 131)

    def test_bus_read(self):
        test_bus = TestBus.Bus1()
        # test reading from the bus
        test_bus.device.port = 0x55
        assert test_bus.a == 1
        assert test_bus.b == 1
        assert test_bus.c == 10
        test_bus.device.port = 0xAA
        assert test_bus.a == 2
        assert test_bus.b == 0
        assert test_bus.c == 21


if __name__ == "__main__":
    unittest.main()
