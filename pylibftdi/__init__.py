"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi


libftdi can be found at:
 http://www.intra2net.com/en/developer/libftdi/
Neither libftdi or Intra2net are associated with this project;
if something goes wrong here, it's almost definitely my fault
rather than a problem with the libftdi library.
"""

__VERSION__ = "0.9"
__AUTHOR__ = "Ben Bass"


__ALL__ = ['Driver', 'Device', 'BitBangDevice', 'Bus', 'FtdiError',
           'ALL_OUTPUTS', 'ALL_INPUTS', 'BB_OUTPUT', 'BB_INPUT',
           'examples', 'tests']

from pylibftdi import _base, driver, util, bitbang

# Bring them in to package scope so we can treat pylibftdi
# as a module if we want.
FtdiError = _base.FtdiError
Bus = util.Bus
Driver = driver.Driver
Device = driver.Device
BitBangDevice = bitbang.BitBangDevice

ALL_OUTPUTS = bitbang.ALL_OUTPUTS
ALL_INPUTS = bitbang.ALL_INPUTS
BB_OUTPUT = bitbang.BB_OUTPUT
BB_INPUT = bitbang.BB_INPUT
FLUSH_BOTH = driver.FLUSH_BOTH
FLUSH_INPUT = driver.FLUSH_INPUT
FLUSH_OUTPUT = driver.FLUSH_OUTPUT

# LEGACY SUPPORT


class BitBangDriver(bitbang.BitBangDevice):
    def __init__(self, direction=ALL_OUTPUTS):
        import warnings
        warnings.warn('change BitBangDriver reference to BitBangDevice',
                      DeprecationWarning)
        return BitBangDevice.__init__(self, direction=direction, lazy_open=True)
