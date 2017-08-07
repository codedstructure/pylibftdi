"""
Report connected FTDI devices. This may be useful in obtaining
serial numbers to use as the device_id parameter of the Device()
constructor to communicate with a specific device when more than
one is present.

example usage:

    $ python pylibftdi/examples/list_devices.py
    FTDI:UB232R:FTAS1UN5
    FTDI:UM232R USB <-> Serial:FTE4FFVQ

To open a device specifically to communicate with the second of
these devices, the following would be used:

    >>> from pylibftdi import Device
    >>> dev = Device(device_id="FTE4FFVQ")
    >>>

Copyright (c) 2011-2014 Ben Bass <benbass@codedstructure.net>
All rights reserved.
"""

from pylibftdi import Driver


def get_ftdi_device_list():
    """
    return a list of lines, each a colon-separated
    vendor:product:serial summary of detected devices
    """
    dev_list = []
    for device in Driver().list_devices():
        # list_devices returns bytes rather than strings
        dev_info = map(lambda x: x.decode('latin1'), device)
        # device must always be this triple
        vendor, product, serial = dev_info
        dev_list.append("%s:%s:%s" % (vendor, product, serial))
    return dev_list


def main():
    for device in get_ftdi_device_list():
        print(device)


if __name__ == '__main__':
    main()
