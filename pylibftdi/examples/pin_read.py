"""
Display values on input pins of a BitBangDevice.

TODO: add configurable delay, display differences in bold
(make command line options compatible with 'watch')

Copyright (c) 2011-2012 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

from pylibftdi import BitBangDevice, ALL_INPUTS
import time
import sys

d = BitBangDevice(direction=ALL_INPUTS)

while True:
    time.sleep(0.01)
    value = d.port
    sys.stdout.write("\b" * 32)
    for n in range(8):
        sys.stdout.write("1 " if value & (1 << (7 - n)) else "0 ")
    sys.stdout.write("  (%d/0x%02X)" % (value, value))
    sys.stdout.flush()
