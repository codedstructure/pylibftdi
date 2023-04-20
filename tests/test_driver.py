"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

This module contains some basic tests for Driver class.
"""

import unittest
from pylibftdi.driver import Driver

class DriverTest(unittest.TestCase):
    """
    Test to ensure the Driver class accepts the correct arguments. 
    """

    def testNoneLibrary(self):
        """
        The Driver class can accept no library names passed in to
        the constructor. This uses the default libraries specified in the
        Driver class. This is the default and most typical behavior.
        """
        driver = Driver(libftdi_search=None)
        self.assertListEqual(driver._lib_search['libftdi'], \
                        ['ftdi1', 'libftdi1', 'ftdi', 'libftdi'])

    def testNoExplicitParameters(self):
        """
        The Driver class can accept no explicit parameters. Ensures 
        that libftdi_search is set to None by default.
        """
        driver = Driver()
        self.assertListEqual(driver._lib_search['libftdi'], \
                        ['ftdi1', 'libftdi1', 'ftdi', 'libftdi'])

    def testStringLibrary(self):
        """
        The Driver class can accept a string library name and store the
        value in a list with a single element. You might use this when you
        know the exact name of the library (perhaps custom).
        """
        driver = Driver(libftdi_search='libftdi')
        self.assertListEqual(driver._lib_search['libftdi'], ['libftdi'])

    def testListLibrary(self):
        """
        The Driver class can accept a list of library names and store the
        values in a list. You might use this to support a limited number of
        platforms with different library names.
        """
        driver = Driver(libftdi_search=['ftdi1', 'libftdi1'])
        self.assertListEqual(driver._lib_search['libftdi'], ['ftdi1', 'libftdi1'])


if __name__ == "__main__":
    unittest.main()
