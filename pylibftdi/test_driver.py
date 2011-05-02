

import pylibftdi.driver

fn_log = []
class SimpleMock(object):
    def __init__(self, name="<base>"):
        self.__name = name

    def __getattr__(self, key):
        return self.__dict__.get(key, SimpleMock(key))

    def __setattr__(self, key, value):
        return self.__dict__.setdefault(key, value)

    def __call__(self, *o, **k):
        fn_log.append(self.__name)
        print("%s(*%s, **%s)" % (self.__name, o, k))
        return 0

class Driver(object):
    def __init__(self, *o, **k):
        self.fdll = SimpleMock()

def assertCalls(fn, methodname):
    del fn_log[:]
    fn()
    assert methodname in fn_log

pylibftdi.driver.Driver = Driver

from pylibftdi import Device

with Device() as dev:
    assertCalls(lambda : dev.write('xxx'), 'ftdi_write_data')
    assertCalls(lambda : dev.read(10), 'ftdi_read_data')
    assertCalls(dev.flush_input, 'ftdi_usb_purge_rx_buffer')
    assertCalls(dev.flush_output, 'ftdi_usb_purge_tx_buffer')
    assertCalls(dev.flush, 'ftdi_usb_purge_buffers')


