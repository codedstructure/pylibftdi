"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

from tests.test_common import LoopDevice, CallCheckMixin, unittest
from pylibftdi.device import Device
from pylibftdi import FtdiError

# and now some test cases...


class DeviceFunctions(CallCheckMixin, unittest.TestCase):
    def testContextManager(self):
        def _():
            with Device():
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
                "ftdi_usb_close",
                "ftdi_deinit",
            ],
        )

    def testOpen(self):
        # a lazy_open open() shouldn't do anything
        self.assertCallsExact(lambda: Device(lazy_open=True), [])
        # a non-lazy_open open() should open the port...
        self.assertCalls(lambda: Device(), "ftdi_usb_open_desc_index")
        # should be the same with device_id...
        self.assertCalls(lambda: Device("bogus"), "ftdi_usb_open_desc_index")
        # should be the same with device_id...
        self.assertCalls(lambda: Device(device_index=2), "ftdi_usb_open_desc_index")

    def testOpenInterface(self):
        self.assertCalls(lambda: Device(interface_select=1), "ftdi_set_interface")
        # check that opening a specific interface does that
        self.assertNotCalls(lambda: Device(), "ftdi_set_interface")

    def testReadWrite(self):
        with Device() as dev:
            self.assertCalls(lambda: dev.write("xxx"), "ftdi_write_data")
            self.assertCalls(lambda: dev.read(10), "ftdi_read_data")

    def testFlush(self):
        with Device() as dev:
            self.assertCalls(dev.flush_input, "ftdi_usb_purge_rx_buffer")
            self.assertCalls(dev.flush_output, "ftdi_usb_purge_tx_buffer")
            self.assertCalls(dev.flush, "ftdi_usb_purge_buffers")

    def testClose(self):
        d = Device()
        d.close()
        self.assertRaises(FtdiError, d.write, "hello")
        d = Device()
        d.close()
        self.assertRaises(FtdiError, d.read, 1)


class LoopbackTest(unittest.TestCase):
    """
    these all require mode='t' to pass in Python3
    """

    def testPrint(self):
        d = LoopDevice(mode="t")
        d.write("Hello")
        d.write(" World\n")
        d.write("Bye")
        self.assertEqual(d.readline(), "Hello World\n")
        self.assertEqual(d.readline(), "Bye")

    def testPrintBytes(self):
        d = LoopDevice(mode="t")
        d.write(b"Hello")
        d.write(b" World\n")
        d.write(b"Bye")
        self.assertEqual(d.readline(), "Hello World\n")
        self.assertEqual(d.readline(), "Bye")

    def testLines(self):
        d = LoopDevice(mode="t")
        lines = ["Hello\n", "World\n", "And\n", "Goodbye\n"]
        d.writelines(lines)
        self.assertEqual(d.readlines(), lines)

    def testLinesBytes(self):
        d = LoopDevice(mode="t")
        lines = [b"Hello\n", b"World\n", b"And\n", b"Goodbye\n"]
        d.writelines(lines)
        self.assertEqual(d.readlines(), [str(line, "ascii") for line in lines])

    def testIterate(self):
        d = LoopDevice(mode="t")
        lines = ["Hello\n", "World\n", "And\n", "Goodbye\n"]
        d.writelines(lines)
        for idx, line in enumerate(d):
            self.assertEqual(line, lines[idx])

    def testBuffer(self):
        d = LoopDevice(mode="t", chunk_size=3)
        d.write("Hello")
        d.write(" World\n")
        d.write("Bye")
        self.assertEqual(d.readline(), "Hello World\n")
        self.assertEqual(d.readline(), "Bye")

    def testReadLineBytes(self):
        """
        Device.readline() when in byte mode should raise a TypeError.
        This method should only be used in text mode.
        """
        d = LoopDevice(mode="b")
        d.write(b"Hello\n")
        with self.assertRaises(TypeError):
            d.readline()

    def testReadLinesBytes(self):
        """
        Device.readlines() when in byte mode should raise a TypeError.
        This method should only be used in text mode.
        """
        d = LoopDevice(mode="b")
        d.write(b"Hello\n")
        with self.assertRaises(TypeError):
            d.readlines()


if __name__ == "__main__":
    unittest.main()
