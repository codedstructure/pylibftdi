"""
Flash an LED connected via a FTDI UM232R/245R module using pylibftdi

Optionally supply a flash rate (in Hz, default 1) as an argument

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

import time
import sys
from pylibftdi import BitBangDevice


def flash_forever(rate):
    """toggle bit zero at rate Hz"""
    # put an LED with 1Kohm or similar series resistor
    # on D0 pin
    with BitBangDevice() as bb:
        while True:
            time.sleep(1.0 / (2 * rate))
            bb.port ^= 1


def main():
    if len(sys.argv) > 1:
        rate = float(sys.argv[1])
        flash_forever(rate)
    else:
        flash_forever(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
