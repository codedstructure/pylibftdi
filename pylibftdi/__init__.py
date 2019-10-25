"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2019 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

libftdi can be found at: http://www.intra2net.com/en/developer/libftdi/

Neither libftdi nor Intra2net are associated with this project;
if something goes wrong here, it's almost definitely my fault
rather than a problem with the libftdi library.
"""

__VERSION__ = "0.18.0"
__AUTHOR__ = "Ben Bass"


__ALL__ = ['Driver', 'Device', 'BitBangDevice', 'Bus',
           'FtdiError', 'MissingLibraryError',
           'ALL_OUTPUTS', 'ALL_INPUTS', 'BB_OUTPUT', 'BB_INPUT',
           'USB_VID_LIST', 'USB_PID_LIST']

from pylibftdi import _base, driver, device, util, bitbang, serial_device

# Bring them in to package scope so we can treat pylibftdi
# as a module if we want.
FtdiError = _base.FtdiError
LibraryMissingError = _base.LibraryMissingError
Bus = util.Bus
Driver = driver.Driver
Device = device.Device
SerialDevice = serial_device.SerialDevice
BitBangDevice = bitbang.BitBangDevice
USB_VID_LIST = driver.USB_VID_LIST
USB_PID_LIST = driver.USB_PID_LIST

ALL_OUTPUTS = bitbang.ALL_OUTPUTS
ALL_INPUTS = bitbang.ALL_INPUTS
BB_OUTPUT = bitbang.BB_OUTPUT
BB_INPUT = bitbang.BB_INPUT
FLUSH_BOTH = driver.FLUSH_BOTH
FLUSH_INPUT = driver.FLUSH_INPUT
FLUSH_OUTPUT = driver.FLUSH_OUTPUT

# Use these for interface_select on multiple-interface devices
INTERFACE_ANY = 0
INTERFACE_A = 1
INTERFACE_B = 2
INTERFACE_C = 3
INTERFACE_D = 4
