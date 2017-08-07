#!/usr/bin/env python
"""
Display values on input pins of a BitBangDevice.

TODO:
 * ANSI colours / display differences in bold

example - beep on pin 1 going high:
    $ pylibftdi/examples/pin_read.py -n 0.01 -m 1 -k 1 && beep

Copyright (c) 2011-2014 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

import itertools
import time
import sys
from pylibftdi import BitBangDevice, ALL_INPUTS


def get_value():
    """
    get the value of the pins
    """
    if not getattr(get_value, "dev", None):
        get_value.dev = BitBangDevice(direction=ALL_INPUTS)
    dev = getattr(get_value, "dev")
    return dev.port


def display_value(value):
    """
    display the given value
    """
    sys.stdout.write("\b" * 32)
    for n in range(8):
        sys.stdout.write("1 " if value & (1 << (7 - n)) else "0 ")
    sys.stdout.write("  (%d/0x%02X)" % (value, value))
    sys.stdout.flush()


def display_loop(interval=1, count=0, match=None, mask=0xFF):
    """
    display and compare the value

    :param interval: polling interval in seconds
    :param count: number of polls to do, or infinite if 0
    :param match: value to look for to exit early
    :param mask: mask of read value before comparing to match
    :return: 'ok'. either a match was made or none was requested
    :rtype: bool
    """
    if not count:
        count_iter = itertools.count()
    else:
        count_iter = range(count)

    try:
        for _ in count_iter:
            value = get_value()
            display_value(value)
            if match is not None and (value & mask == match):
                return True
            time.sleep(interval)
        return False
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\n')

    if match is not None:
        # we quit early while looking for a match
        return False
    else:
        # no match to do; no problem.
        return True


def main(args=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--interval", dest="interval",
                        default=1, type=float,
                        help="refresh interval, default 1 second")
    parser.add_argument("-c", "--count", dest="count",
                        default=0, type=int,
                        help="number of cycles to run for (0 = no limit - the default)")
    parser.add_argument("-m", "--match", dest="match",
                        help="value to match against (e.g. 0x1F, 7, etc)")
    parser.add_argument("-k", "--mask", dest="mask",
                        help="mask to match with (e.g. 0x07, 2, etc) - default 0xFF")
    args = parser.parse_args(args)

    if args.interval < 0.001:
        parser.error("interval must be >= 0.001")
    if args.count < 0:
        parser.error("count must be >= 0")
    mask = match = None
    if args.mask:
        if not args.match:
            parser.error("Must specify --match with mask")
        try:
            mask = int(args.mask, 0)
        except ValueError:
            parser.error("Could not interpret given mask")
    else:
        mask = 0xFF
    if args.match:
        try:
            match = int(args.match, 0)
        except ValueError:
            parser.error("Could not interpret given mask")
    ok = display_loop(args.interval, args.count, match, mask)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
