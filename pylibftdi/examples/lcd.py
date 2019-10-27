"""
Write a string (argv[1] if run from command line) to a HD44780
LCD module connected via a FTDI UM232R/245R module using pylibftdi

example usage:

# while true;
>   do python lcd.py $( awk '{print $1}' /proc/loadavg);
>   sleep 5;
> done

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

from pylibftdi import BitBangDevice, Bus


class LCD(object):
    """
    The UM232R/245R is wired to the LCD as follows:
       DB0..3 to LCD D4..D7 (pin 11..pin 14)
       DB6 to LCD 'RS' (pin 4)
       DB7 to LCD 'E' (pin 6)
    """
    data = Bus(0, 4)
    rs = Bus(6)
    e = Bus(7)

    def __init__(self, device):
        # The Bus descriptor assumes we have a 'device'
        # attribute which provides a port
        self.device = device

    def _trigger(self):
        """generate a falling edge"""
        self.e = 1
        self.e = 0

    def init_four_bit(self):
        """
        set the LCD's 4 bit mode, since we only have
        8 data lines and need at least 2 to strobe
        data into the module and select between data
        and commands.
        """
        self.rs = 0
        self.data = 3
        for _ in range(3):
            self._trigger()
        self.data = 2
        self._trigger()

    def _write_raw(self, rs, x):
        # rs determines whether this is a command
        # or a data byte. Write the data as two
        # nibbles. Ahhh... nibbles. QBasic anyone?
        self.rs = rs
        self.data = x >> 4
        self._trigger()
        self.data = x & 0x0F
        self._trigger()

    def write_cmd(self, x):
        self._write_raw(0, x)

    def write_data(self, x):
        self._write_raw(1, x)


def display(string, device_id=None):
    """
    Display the given string on an attached LCD
    an optional `device_id` can be given.
    """
    with BitBangDevice(device_id) as bb:

        # These LCDs are quite slow - and the actual baudrate
        # is 16x this in bitbang mode...
        bb.baudrate = 60

        lcd = LCD(bb)
        lcd.init_four_bit()

        # 001xxxxx - function set
        lcd.write_cmd(0x20)
        # 00000001 - clear display
        lcd.write_cmd(0x01)
        # 000001xx - entry mode set
        # bit 1: inc(1)/dec(0)
        # bit 0: shift display
        lcd.write_cmd(0x06)
        # 00001xxx - display config
        # bit 2: display on
        # bit 1: display cursor
        # bit 0: blinking cursor
        lcd.write_cmd(0x0C)

        for i in string:
            lcd.write_data(ord(i))


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        display(sys.argv[1])
    else:
        print("Usage: %s 'display string'")
