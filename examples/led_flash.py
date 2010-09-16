"""
Flash an LED connected via a FTDI UM232R/245R module using pylibftdi

Copyright (c) 2010 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

from pylibftdi import BitBangDriver

import time

def flash_forever(rate):
    "toggle bit zero at rate Hz"
    # put an LED with 1Kohm or similar series resistor
    # on D0 pin
    with BitBangDriver() as bb:
        while True:
            time.sleep(1.0/(2*rate))
            bb.port ^= 1

if __name__ == '__main__':
    flash_forever(1)