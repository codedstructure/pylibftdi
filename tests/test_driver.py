"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for Driver class.
"""

from pylibftdi import LibraryMissingError
from pylibftdi.driver import Driver
from tests.test_common import unittest


class DriverTest(unittest.TestCase):
    """
    Test to ensure the Driver class accepts the correct arguments.
    """

    def setUp(self):
        """The default library names are stored in the Driver class as a
        class variable. This method will run before each unit test to reset
        the default library names. If other class variables are added to the
        Driver class, they should also be added here.
        """
        Driver._lib_search = {
            "libftdi": ["ftdi1", "libftdi1", "ftdi", "libftdi"],
            "libusb": ["usb-1.0", "libusb-1.0"],
        }

    def testNoneLibrary(self):
        """
        The Driver class can accept no library names passed in to
        the constructor. This uses the default libraries specified in the
        Driver class. This is the default and most typical behavior.
        """
        driver = Driver(libftdi_search=None)
        self.assertListEqual(
            driver._lib_search["libftdi"], ["ftdi1", "libftdi1", "ftdi", "libftdi"]
        )

    def testNoExplicitParameters(self):
        """
        The Driver class can accept no explicit parameters. Ensures
        that libftdi_search is set to None by default.
        """
        driver = Driver()
        self.assertListEqual(
            driver._lib_search["libftdi"], ["ftdi1", "libftdi1", "ftdi", "libftdi"]
        )

    def testStringLibrary(self):
        """
        The Driver class can accept a string library name and store the
        value in a list with a single element. You might use this when you
        know the exact name of the library (perhaps custom).
        """
        driver = Driver(libftdi_search="libftdi")
        self.assertListEqual(driver._lib_search["libftdi"], ["libftdi"])

    def testListLibrary(self):
        """
        The Driver class can accept a list of library names and store the
        values in a list. You might use this to support a limited number of
        platforms with different library names.
        """
        driver = Driver(libftdi_search=["ftdi1", "libftdi1"])
        self.assertListEqual(driver._lib_search["libftdi"], ["ftdi1", "libftdi1"])

    def testLoadLibrarySearchListEmpty(self):
        """
        If a Driver object calls _load_library where search_list is an empty
        list, LibraryMissingError will be raised.
        """
        # Use the default library names.
        driver = Driver(libftdi_search=None)
        # Try and find the library names for libftdi.
        with self.assertRaises(expected_exception=LibraryMissingError):
            driver._load_library(name="libftdi", search_list=[])

    def testLoadLibraryMissingLibraryName(self):
        """
        If a Driver object calls _load_library with with a name not in the
        default library names (Driver._lib_search), LibraryMissingError will
        be raised.
        """
        driver = Driver(libftdi_search=None)
        with self.assertRaises(expected_exception=LibraryMissingError):
            driver._load_library(name="non-existent-library", search_list=None)

    def testLoadLibrarySearchListNone(self):
        """
        If a Driver object calls _load_library with with a valid name (the key
        exists in Driver._lib_search) and search_list is None, the proper
        library will be returned.
        """
        driver = Driver(libftdi_search=None)
        try:
            # Assert that Driver can find both of the defaults.
            libftdi = driver._load_library(name="libftdi", search_list=None)
            libusb = driver._load_library(name="libusb", search_list=None)
            self.assertIsNotNone(obj=libftdi, msg="libftdi library not found")
            self.assertIsNotNone(obj=libusb, msg="libusb library not found")
        except LibraryMissingError:
            self.fail("LibraryMissingError raised for default library names.")


if __name__ == "__main__":
    unittest.main()
