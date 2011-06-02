"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

from test_common import (LoopDevice, Device, CallCheckMixin, unittest)

# and now some test cases...

class DeviceFunctions(unittest.TestCase, CallCheckMixin):

    def testContextManager(self):
        def _():
            with Device() as dev:
                pass
        self.assertCallsExact(_,
                ['ftdi_init', 'ftdi_usb_open',
                 'ftdi_usb_close', 'ftdi_deinit'])

    def testOpen(self):
        # a lazy_open open() shouldn't do anything
        self.assertCallsExact(lambda: Device(lazy_open=True), [])
        # a non-lazy_open open() should open the port...
        self.assertCalls(lambda: Device(), 'ftdi_usb_open')
        # and given a device_id, it should do a open_desc
        self.assertCalls(lambda: Device('bogus'), 'ftdi_usb_open_desc')

    def testReadWrite(self):
        with Device() as dev:
            self.assertCalls(lambda : dev.write('xxx'), 'ftdi_write_data')
            self.assertCalls(lambda : dev.read(10), 'ftdi_read_data')

    def testFlush(self):
        with Device() as dev:
            self.assertCalls(dev.flush_input, 'ftdi_usb_purge_rx_buffer')
            self.assertCalls(dev.flush_output, 'ftdi_usb_purge_tx_buffer')
            self.assertCalls(dev.flush, 'ftdi_usb_purge_buffers')

class LoopbackTest(unittest.TestCase):
    """
    these all require mode='t' to pass in Python3
    """

    def testPrint(self):
        d = LoopDevice(mode='t')
        d.write('Hello')
        d.write(' World\n')
        d.write('Bye')
        self.assertEqual(d.readline(), 'Hello World\n')
        self.assertEqual(d.readline(), 'Bye')

    def testLines(self):
        d = LoopDevice(mode='t')
        lines = ['Hello\n', 'World\n', 'And\n', 'Goodbye\n']
        d.writelines(lines)
        self.assertEqual(d.readlines(), lines)

    def testIterate(self):
        d = LoopDevice(mode='t')
        lines = ['Hello\n', 'World\n', 'And\n', 'Goodbye\n']
        d.writelines(lines)
        for idx,line in enumerate(d):
            self.assertEqual(line, lines[idx])


if __name__ == "__main__":
    unittest.main()
