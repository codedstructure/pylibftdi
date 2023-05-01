"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

import unittest

from pylibftdi import FtdiError
from pylibftdi.bitbang import BitBangDevice

from tests.test_common import CallCheckMixin, LoopDevice


class LoopBitBangDevice(BitBangDevice, LoopDevice):
    pass


BitBangDevice = LoopBitBangDevice  # type: ignore


# and now some test cases...
class BitBangFunctions(CallCheckMixin, unittest.TestCase):
    def testContextManager(self):
        def _():
            with BitBangDevice():
                pass

        self.assertCallsExact(
            _,
            [
                "ftdi_init",
                "ftdi_usb_open_desc_index",
                "ftdi_set_bitmode",
                "ftdi_setflowctrl",
                "ftdi_set_baudrate",
                "ftdi_set_latency_timer",
                "ftdi_set_bitmode",
                "ftdi_usb_close",
                "ftdi_deinit",
            ],
        )

    def testOpen(self):
        """
        check same opening things as a normal Device still work
        for BitBangDevice
        """
        # a lazy_open open() shouldn't do anything
        self.assertCallsExact(lambda: BitBangDevice(lazy_open=True), [])
        # a non-lazy_open open() should open the port...
        self.assertCalls(lambda: BitBangDevice(), "ftdi_usb_open_desc_index")
        # and set the bit mode
        self.assertCalls(lambda: BitBangDevice(), "ftdi_set_bitmode")
        # and given a device_id, it should do a open_desc
        self.assertCalls(lambda: BitBangDevice("bogus"), "ftdi_usb_open_desc_index")

    def testInitDirection(self):
        # check that a direction can be given on open and is honoured
        for dir_test in (0, 1, 4, 12, 120, 255):
            dev = BitBangDevice(direction=dir_test)
            self.assertEqual(dev.direction, dir_test)
            self.assertEqual(dev._direction, dir_test)
            self.assertEqual(dev._last_set_dir, dir_test)
        # check an invalid direction on open gives error
        self.assertRaises(FtdiError, lambda: BitBangDevice(direction=300))

    def testDirection(self):
        dev = BitBangDevice()
        # check that a direction can be given on open and is honoured
        for dir_test in (0, 1, 4, 12, 120, 255):

            def assign_dir(dir_test=dir_test):
                dev.direction = dir_test

            self.assertCalls(assign_dir, "ftdi_set_bitmode")
            self.assertEqual(dev.direction, dir_test)
            self.assertEqual(dev._direction, dir_test)
            self.assertEqual(dev._last_set_dir, dir_test)
        # check an invalid direction on open gives error

        def _():  # noqa
            dev.direction = 300

        self.assertRaises(FtdiError, _)

    def testPort(self):
        dev = BitBangDevice()
        # check that a direction can be given on open and is honoured
        for port_test in (0, 1, 4, 12, 120, 255):

            def assign_port(port_test=port_test):
                dev.port = port_test

            self.assertCalls(assign_port, "ftdi_write_data")
            self.assertEqual(dev._latch, port_test)
            self.assertEqual(dev.port, port_test)

    def testBitAccess(self):
        dev = BitBangDevice(direction=0xF0)
        _ = dev.latch  # absorb the first ftdi_read_pins
        self.assertCallsExact(lambda: dev.port | 2, ["ftdi_read_pins"])
        self.assertCallsExact(lambda: dev.port & 2, ["ftdi_read_pins"])

    def testLatchReadModifyWrite(self):
        dev = BitBangDevice(direction=0x55)
        self.assertCallsExact(lambda: dev.latch, ["ftdi_read_pins"])
        self.assertCallsExact(lambda: dev.latch, [])

        def x():
            dev.latch += 1
            dev.latch += 1
            dev.latch += 1

        self.assertCallsExact(
            x,
            [
                "ftdi_usb_purge_tx_buffer",
                "ftdi_write_data",
                "ftdi_usb_purge_tx_buffer",
                "ftdi_write_data",
                "ftdi_usb_purge_tx_buffer",
                "ftdi_write_data",
            ],
        )

    def testAsyncLatchReadModifyWrite(self):
        dev = BitBangDevice(direction=0x55, sync=False)
        self.assertCallsExact(lambda: dev.latch, ["ftdi_read_pins"])
        self.assertCallsExact(lambda: dev.latch, [])

        def x():
            dev.latch += 1
            dev.latch += 1
            dev.latch += 1

        self.assertCallsExact(
            x, ["ftdi_write_data", "ftdi_write_data", "ftdi_write_data"]
        )

    def testAugmentedAccess(self):
        dev = BitBangDevice(direction=0xAA)
        _ = dev.latch  # absorb the first ftdi_read_pins

        def _1():
            dev.port &= 2

        def _2():
            dev.port |= 2

        self.assertCallsExact(
            _1, ["ftdi_read_pins", "ftdi_usb_purge_tx_buffer", "ftdi_write_data"]
        )
        self.assertCallsExact(
            _2, ["ftdi_read_pins", "ftdi_usb_purge_tx_buffer", "ftdi_write_data"]
        )


if __name__ == "__main__":
    unittest.main()
