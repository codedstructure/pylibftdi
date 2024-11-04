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

from pylibftdi import add_custom_vid_pid
from pylibftdi.driver import USB_PID_LIST, USB_VID_LIST
from pylibftdi.serial_device import SerialDevice
from tests.test_common import CallCheckMixin, LoopDevice


class LoopSerialDevice(SerialDevice, LoopDevice):
    pass


SerialDevice = LoopSerialDevice  # type: ignore


# and now some test cases...
class SerialFunctions(CallCheckMixin, unittest.TestCase):
    def setUp(self):
        self.sd = SerialDevice()

    def _read_test(self, item):
        # check we ask for the modem status to get this
        self.assertCalls(lambda: getattr(self.sd, item), "ftdi_poll_modem_status")
        # check it isn't settable
        self.assertRaises(AttributeError, lambda: setattr(self.sd, "dsr", 1))

    def _write_test(self, item):
        # check writes call appropriate libftdi function
        self.assertCalls(lambda: setattr(self.sd, item, 1), "ftdi_set" + item)
        # check reads don't call anything
        self.assertCallsExact(lambda: getattr(self.sd, item), [])

    def test_cts(self):
        """check setting and getting cts"""
        self._read_test("cts")

    def test_dsr(self):
        """check setting and getting dsr"""
        self._read_test("dsr")

    def test_ri(self):
        """check setting and getting ri"""
        self._read_test("ri")

    def test_dtr(self):
        """check setting and getting dtr"""
        self._write_test("dtr")

    def test_rts(self):
        """check setting and getting rts"""
        self._write_test("rts")

    def test_add_custom_vid_pid(self):
        """check adding custom VID and PID"""
        initial_vid_list = USB_VID_LIST[:]
        initial_pid_list = USB_PID_LIST[:]
        add_custom_vid_pid(vids=[0x1234], pids=[0x5678])
        self.assertIn(0x1234, USB_VID_LIST)
        self.assertIn(0x5678, USB_PID_LIST)
        # Restore the original lists to avoid side effects on other tests
        USB_VID_LIST[:] = initial_vid_list
        USB_PID_LIST[:] = initial_pid_list


if __name__ == "__main__":
    unittest.main()
