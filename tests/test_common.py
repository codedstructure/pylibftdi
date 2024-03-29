"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

import gc
import logging
import sys

from tests.call_log import CallLog


class SimpleMock:
    """
    This is a simple mock plugin for fdll which logs any calls
    made through it to fn_log, which is currently rather ugly
    global state.
    """

    def __init__(self, name="<base>"):
        self.__name = name

    def __getattr__(self, key):
        return SimpleMock(key)

    def __call__(self, *o, **k):
        CallLog.append(self.__name)
        logging.debug(f"{self.__name}(*{o}, **{k})")
        return 0


class CallCheckMixin:
    """
    this should be used as a mixin for unittest.TestCase classes,
    where it allows the calls through the MockDriver to be checked
    this does not support multi-threading.
    """

    def setUp(self):
        super().setUp()

    def assertCalls(self, fn, methodname):
        CallLog.reset()
        fn()
        self.assertIn(methodname, CallLog.get())

    def assertNotCalls(self, fn, methodname):
        CallLog.reset()
        fn()
        self.assertNotIn(methodname, CallLog.get())

    def assertCallsExact(self, fn, call_list):
        # ensure any pending Device.__del__ calls get triggered before running fn
        gc.collect()
        CallLog.reset()
        fn()
        self.assertEqual(call_list, CallLog.get())


import pylibftdi.driver  # noqa


# monkey patch the Driver class to be the mock thing above.
class MockDriver:
    def __init__(self, *o, **k):
        self.fdll = SimpleMock()

    def libftdi_version(self):
        return pylibftdi.driver.libftdi_version(1, 2, 3, 0, 0)


# importing this _does_ things...
pylibftdi.device.Driver = MockDriver  # type: ignore

from pylibftdi.device import Device  # noqa


class LoopDevice(Device):
    """
    a mock device object which overrides read and write
    to operate as an unbounded loopback pair
    """

    def __init__(self, *o, **k):
        super().__init__(*o, **k)
        self.__buffer = []

    def _read(self, size):
        super()._read(size)  # discard result
        result = bytes(bytearray(self.__buffer[:size]))
        self.__buffer = self.__buffer[size:]
        return result

    def _write(self, data):
        super()._write(data)  # discard result
        self.__buffer.extend(bytearray(data))
        return len(data)


verbose = {"-v", "--verbose"} & set(sys.argv)
logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
