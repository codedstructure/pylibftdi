
from pylibftdi.tests.test_common import unittest
from pylibftdi.util import Bus


class TestBus(unittest.TestCase):

    class MockDriver(object):
        port = 0

    class Bus1(object):
        a = Bus(0, 2)
        b = Bus(2, 1)
        c = Bus(3, 5)

        def __init__(self):
            self.driver = TestBus.MockDriver()

    def test_bus_write(self):
        test_bus = TestBus.Bus1()
        # test writing to the bus
        self.assertEqual(test_bus.driver.port, 0)
        test_bus.a = 3
        test_bus.b = 1
        test_bus.c = 31
        self.assertEqual(test_bus.driver.port, 255)
        test_bus.b = 0
        self.assertEqual(test_bus.driver.port, 251)
        test_bus.c = 16
        self.assertEqual(test_bus.driver.port, 131)

    def test_bus_read(self):
        test_bus = TestBus.Bus1()
        # test reading from the bus
        test_bus.driver.port = 0x55
        assert test_bus.a == 1
        assert test_bus.b == 1
        assert test_bus.c == 10
        test_bus.driver.port = 0xAA
        assert test_bus.a == 2
        assert test_bus.b == 0
        assert test_bus.c == 21
