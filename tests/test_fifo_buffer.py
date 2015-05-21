"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2015 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

This module contains some basic tests for the higher-level
functionality without requiring an actual hardware device
to be attached.
"""

import unittest
from pylibftdi.util import FifoBuffer


class TestFifoBuffer(unittest.TestCase):
    def setUp(self):
        self._buffer = FifoBuffer()

    def testShortReads(self):
        self.assertEqual(self._buffer.extract(2), '')
        self._buffer.insert('123')
        self._buffer.insert('456')
        self._buffer.insert('789')
        self.assertEqual(self._buffer.extract(2), '12')
        self.assertEqual(self._buffer.extract(1), '3')
        self.assertEqual(self._buffer.extract(3), '456')
        self.assertEqual(self._buffer.extract(2), '78')
        self.assertEqual(self._buffer.extract(2), '9')
        self.assertEqual(self._buffer.extract(2), '')

    def testLongReads(self):
        self.assertEqual(self._buffer.extract(2), '')
        self._buffer.insert('123')
        self._buffer.insert('456')
        self._buffer.insert('789')
        self.assertEqual(self._buffer.extract(1024), '123456789')
        self.assertEqual(self._buffer.extract(1024), '')

if __name__ == '__main__':
    unittest.main()
