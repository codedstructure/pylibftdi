"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi


libftdi can be found at:
 http://www.intra2net.com/en/developer/libftdi/
Neither libftdi or Intra2net are associated with this project;
if something goes wrong here, it's almost definitely my fault
rather than a problem with the libftdi library.
"""

__VERSION__ = "0.6"
__AUTHOR__ = "Ben Bass"


__ALL__ = ['Driver', 'BitBangDriver', 'Bus', 'FtdiError',
           'ALL_OUTPUTS', 'ALL_INPUTS', 'BB_OUTPUT', 'BB_INPUT']

from pylibftdi import _base, driver, util, bitbang

# Bring them in to package scope so we can treat pylibftdi
# as a module if we want.
FtdiError = _base.FtdiError
Bus = util.Bus
Driver = driver.Driver
BitBangDriver = bitbang.BitBangDriver

ALL_OUTPUTS = bitbang.ALL_OUTPUTS
ALL_INPUTS = bitbang.ALL_INPUTS
BB_OUTPUT = bitbang.BB_OUTPUT
BB_INPUT = bitbang.BB_INPUT

