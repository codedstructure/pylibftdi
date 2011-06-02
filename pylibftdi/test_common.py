"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

import sys
if sys.version_info < (2,7):
    try:
        import unittest2 as unittest
    except ImportError:
        raise SystemExit("The test functionality is only supported in"
                "Python 2.7+ unless unittest2 is installed")
else:
    import unittest

VERBOSE = False

class SimpleMock(object):
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
        if VERBOSE:
            print("%s(*%s, **%s)" % (self.__name, o, k))
        return 0

class CallLog(object):

    fn_log = []

    @classmethod
    def reset(cls):
        del cls.fn_log[:]

    @classmethod
    def append(cls, value):
        cls.fn_log.append(value)

    @classmethod
    def get(cls):
        return cls.fn_log[:]

class CallCheckMixin(object):
    """
    this should be used as a mixin for unittest.TestCase classes,
    where it allows the calls through the MockDriver to be checked
    this does not support multi-threading.
    """
    def assertCalls(self, fn, methodname):
        CallLog.reset()
        fn()
        self.assertIn(methodname, CallLog.get())

    def assertCallsExact(self, fn, call_list):
        CallLog.reset()
        fn()
        self.assertEqual(call_list, CallLog.get())


# monkey patch the Driver class to be the mock thing above.
class MockDriver(object):
    def __init__(self, *o, **k):
        self.fdll = SimpleMock()


import pylibftdi.driver
from pylibftdi.driver import Device

class LoopDevice(Device):
    """
    a mock device object which overrides read and write
    to operate as an unbounded loopback pair
    """
    def __init__(self, *o, **k):
        super(LoopDevice, self).__init__(*o, **k)
        self.__buffer = []

    def _read(self, size):
        super(LoopDevice, self)._read(size)  # discard result
        result = bytes(bytearray(self.__buffer[:size]))
        self.__buffer = self.__buffer[size:]
        return result

    def _write(self, data):
        super(LoopDevice, self)._write(data)  # discard result
        self.__buffer.extend(bytearray(data))
        return len(data)

# importing this _does_ things...
pylibftdi.driver.Driver = MockDriver

if set(['-v', '--verbose']) & set(sys.argv):
    VERBOSE = True
