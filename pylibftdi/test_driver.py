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

fn_log = []
class SimpleMock(object):
    """
    This is a simple mock plugin for fdll which logs any calls
    made through it to fn_log, which is currently rather ugly
    global state.
    """
    def __init__(self, name="<base>"):
        self.__name = name

    def __getattr__(self, key):
        return self.__dict__.get(key, SimpleMock(key))

    def __setattr__(self, key, value):
        return self.__dict__.__setitem__(key, value)

    def __call__(self, *o, **k):
        fn_log.append(self.__name)
        if VERBOSE:
            print("%s(*%s, **%s)" % (self.__name, o, k))
        return 0

def get_calls(fn):
    "return the called function names which the fdll mock object made"
    del fn_log[:]
    fn()
    return fn_log



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
        Device.__init__(self, *o, **k)
        self.__buffer = []

    def read(self, size=None):
        Device.read(self, size)
        if size is None:
            result = ''.join(self.__buffer)
            self.__buffer = []
        else:
            result = ''.join(self.__buffer[:size])
            self.__buffer = self.__buffer[size:]
        return result

    def write(self, data):
        Device.write(self, data)
        self.__buffer.extend(list(data))
        return len(data)


# and now some test cases...

class DeviceFunctions(unittest.TestCase):

    def setUp(self):
        pylibftdi.driver.Driver = MockDriver

    def assertCalls(self, fn, methodname):
        del fn_log[:]
        fn()
        self.assertIn(methodname, fn_log)

    def testContextManager(self):
        def _():
            with Device() as dev:
                pass
        self.assertEqual(get_calls(_),
                ['ftdi_init', 'ftdi_usb_open',
                 'ftdi_usb_close', 'ftdi_deinit'])

    def testOpen(self):
        # a lazy_open open() shouldn't do anything
        self.assertEqual(get_calls(lambda: Device(lazy_open=True)), [])
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

    def setUp(self):
        pylibftdi.driver.Driver = MockDriver

    def testPrint(self):
        d = LoopDevice()
        d.write('Hello')
        d.write(' World\n')
        d.write('Bye')
        self.assertEqual(d.readline(), 'Hello World\n')
        self.assertEqual(d.readline(), 'Bye')

    def testLines(self):
        d = LoopDevice()
        lines = ['Hello\n', 'World\n', 'And\n', 'Goodbye\n']
        d.writelines(lines)
        self.assertEqual(d.readlines(), lines)

    def testIterate(self):
        d = LoopDevice()
        lines = ['Hello\n', 'World\n', 'And\n', 'Goodbye\n']
        d.writelines(lines)
        for idx,line in enumerate(d):
            self.assertEqual(line, lines[idx])


if __name__ == "__main__":
    if set(['-v', '--verbose']) & set(sys.argv):
        VERBOSE = True
    unittest.main()
