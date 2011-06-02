"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

from test_common import (LoopDevice, CallCheckMixin, unittest)
from pylibftdi.bitbang import BitBangDevice
from pylibftdi import FtdiError

class TestBitBangDevice(BitBangDevice, LoopDevice):
    pass

BitBangDevice = TestBitBangDevice

# and now some test cases...
class BitBangFunctions(unittest.TestCase, CallCheckMixin):

    def testContextManager(self):
        def _():
            with BitBangDevice() as dev:
                pass
        self.assertCallsExact(_,
                ['ftdi_init', 'ftdi_usb_open',
                 'ftdi_set_bitmode',
                 'ftdi_usb_close', 'ftdi_deinit'])

    def testOpen(self):
        """
        check same opening things as a normal Device still work
        for BitBangDevice
        """
        # a lazy_open open() shouldn't do anything
        self.assertCallsExact(lambda: BitBangDevice(lazy_open=True), [])
        # a non-lazy_open open() should open the port...
        self.assertCalls(lambda: BitBangDevice(), 'ftdi_usb_open')
        # and set the bit mode
        self.assertCalls(lambda: BitBangDevice(), 'ftdi_set_bitmode')
        # and given a device_id, it should do a open_desc
        self.assertCalls(lambda: BitBangDevice('bogus'), 'ftdi_usb_open_desc')

    def testInitDirection(self):
        # check that a direction can be given on open and is honoured
        for dir_test in (0,1,4,12,120,255):

            dev = BitBangDevice(direction = dir_test)
            self.assertEqual(dev.direction, dir_test)
            self.assertEqual(dev._direction, dir_test)
            self.assertEqual(dev._last_set_dir, dir_test)
        # check an invalid direction on open gives error
        self.assertRaises(FtdiError, lambda: BitBangDevice(direction=300))

    def testDirection(self):
        dev = BitBangDevice()
        # check that a direction can be given on open and is honoured
        for dir_test in (0,1,4,12,120,255):
            def _(dt):
                dev.direction = dt
            self.assertCalls(lambda : _(dir_test), 'ftdi_set_bitmode')
            self.assertEqual(dev.direction, dir_test)
            self.assertEqual(dev._direction, dir_test)
            self.assertEqual(dev._last_set_dir, dir_test)
        # check an invalid direction on open gives error
        def _():
            dev.direction = 300
        self.assertRaises(FtdiError, _)

    def testPort(self):
        dev = BitBangDevice()
        # check that a direction can be given on open and is honoured
        for port_test in (0,1,4,12,120,255):
            def _(pt):
                dev.port = pt
            self.assertCalls(lambda : _(port_test), 'ftdi_write_data')
            self.assertEqual(dev._latch, port_test)
            self.assertEqual(dev.port, port_test)
        # XXX: this is incomplete.
        # could check for various directions and how that impacts
        # port read / write, as well as r/m/w operations.

if __name__ == "__main__":
    unittest.main()

