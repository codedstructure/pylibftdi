Basic Usage
===========

`pylibftdi` is a minimal Pythonic interface to FTDI devices using libftdi_.
Rather than simply expose all the methods of the underlying library directly,
it aims to provide a simpler API for the main use-cases of serial and parallel
IO, while still allowing the use of the more advanced functions of the library.

.. _libftdi: http://www.intra2net.com/en/developer/libftdi/

General
-------

The primary interface is the ``Device`` class in the ``pylibftdi`` package; this
gives serial access on relevant FTDI devices (e.g. the UM232R), providing a
file-like interface (read, write).  Baudrate is controlled with the ``baudrate``
property.

If a Device instance is created with ``mode='t'`` (text mode) then read() and
write() can use the given ``encoding`` (defaulting to latin-1). This allows
easier integration with passing unicode strings between devices.

Multiple devices are supported by passing the desired device serial number (as
a string) in the ``device_id`` parameter - this is the first parameter in both
Device() and BitBangDevice() constructors. Alternatively the device 'description'
can be given, and an attempt will be made to match this if matching by serial
number fails.

In the event that multiple devices (perhaps of identical type) have the same
description and serial number, the ``device_index`` parameter may be given to
open matching devices by numerical index; this defaults to zero, meaning the
first matching device.

Examples
~~~~~~~~

::

    >>> from pylibftdi import Device
    >>>
    >>> with Device(mode='t') as dev:
    ...     dev.baudrate = 115200
    ...     dev.write('Hello World')

The pylibftdi.BitBangDevice wrapper provides access to the parallel IO mode of
operation through the ``port`` and ``direction`` properties.  These provide an
8 bit IO port including all the relevant bit operations to make things simple.

::

    >>> from pylibftdi import BitBangDevice
    >>>
    >>> with BitBangDevice('FTE00P4L') as bb:
    ...     bb.direction = 0x0F  # four LSB are output(1), four MSB are input(0)
    ...     bb.port |= 2         # set bit 1
    ...     bb.port &= 0xFE      # clear bit 0

There is support for a number of external devices and protocols, specifically
for interfacing with HD44780 LCDs using the 4-bit interface.

