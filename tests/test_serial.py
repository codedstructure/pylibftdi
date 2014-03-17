"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

from tests.test_common import (LoopDevice, CallCheckMixin, unittest)
from pylibftdi.serial_device import SerialDevice
from pylibftdi import FtdiError


class TestSerialDevice(SerialDevice, LoopDevice):
    pass

SerialDevice = TestSerialDevice


# and now some test cases...
class SerialFunctions(CallCheckMixin, unittest.TestCase):

    def setUp(self):
        self.sd = SerialDevice()

    def _read_test(self, item):
        # check we ask for the modem status to get this
        self.assertCalls(lambda: getattr(self.sd, item), 'ftdi_poll_modem_status')
        # check it isn't settable
        self.assertRaises(AttributeError, lambda: setattr(self.sd, 'dsr', 1))

    def _write_test(self, item):
        # check writes call appropriate libftdi function
        self.assertCalls(lambda: setattr(self.sd, item, 1), 'ftdi_set' + item)
        # check reads don't call anything
        self.assertCallsExact(lambda: getattr(self.sd, item), [])

    def test_cts(self):
        """check setting and getting cts"""
        self._read_test('cts')

    def test_dsr(self):
        """check setting and getting dsr"""
        self._read_test('dsr')

    def test_ri(self):
        """check setting and getting ri"""
        self._read_test('ri')

    def test_dtr(self):
        """check setting and getting dtr"""
        self._write_test('dtr')

    def test_rts(self):
        """check setting and getting rts"""
        self._write_test('rts')

if __name__ == "__main__":
    unittest.main()
