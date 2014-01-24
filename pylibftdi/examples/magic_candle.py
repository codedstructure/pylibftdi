"""
Magic Candle - light falling on the LDR turns on the LED, which due
               to arrangement keeps the LED on until LDR/LED path
               is blocked

LDR (via a transistor switch - dark = '1') - D0
LED (via series resistor) - D1

pylibftdi - codedstructure 2013-2014
"""

import time

from pylibftdi.util import Bus
from pylibftdi import BitBangDevice


class Candle(object):
    is_dark = Bus(0)   # D0
    be_light = Bus(1)  # D1

    def __init__(self):
        # make the device connection, this is used
        # in the Bus descriptors. Also set direction
        # appropriately.
        self.device = BitBangDevice(direction=0xFE)

    def run(self):
        while True:
            time.sleep(0.05)
            self.be_light = not self.is_dark


if __name__ == '__main__':
    c = Candle()
    c.run()
