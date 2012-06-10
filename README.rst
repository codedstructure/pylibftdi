pylibftdi
=========

pylibftdi is a minimal Pythonic interface to FTDI devices using libftdi_.

.. _libftdi: http://www.intra2net.com/en/developer/libftdi/

:Features:

 - Supports Python 2 and Python 3
 - Supports parallel and serial devices
 - Support for multiple devices
 - File-like interface wherever appropriate
 - Cross-platform

:Limitations:

 - Currently only one port per device is used; I've not tested with dual
   port devices yet.
 - The API might change prior to reaching a 1.0 release.

Usage
-----

The primary interface is the ``Device`` class in the pylibftdi package; this
gives serial access on relevant FTDI devices (e.g. the UM232R), providing a
file-like interface (read, write).  Baudrate is controlled with the ``baudrate``
property.

If a Device instance is created with ``mode='t'`` (text mode) then read() and
write() can use the given ``encoding`` (defaulting to latin-1). This doesn't
make a lot of difference on Python 2 (and can be omitted), but allows easier
integration with passing unicode strings between devices in Python 3.

Multiple devices are supported by passing the desired device serial number (as
a string) in the ``device_id`` parameter - this is the first parameter in both
Device() and BitBangDevice() constructors. Alternatively the device 'description'
can be given, and an attempt will be made to match this if matching by serial
number fails.

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

There is support for a number of external devices and protocols, including
interfacing with HD44780 LCDs using the 4-bit interface.

History & Motivation
--------------------
This package is the result of various bits of work using FTDI's
devices, primarily for controlling external devices.  Some of this
is documented on the codedstructure blog, codedstructure.blogspot.com

At least two other open-source Python FTDI wrappers exist, and each
of these may be best for some projects.

 * ftd2xx_ - ctypes binding to FTDI's own D2XX driver
 * pyftdi_ - a C extension libftdi binding

.. _ftd2xx: http://pypi.python.org/pypi/ftd2xx
.. _pyftdi: http://git.marcansoft.com/?p=pyftdi.git

pylibftdi exists in the gap between these two projects; ftd2xx uses
the (closed-source) D2XX driver, but provides a high-level Python
interface, while pyftdi works with libftdi but is very low-level.
The aim for pylibftdi is to work with the libftdi, but to provide
a high-level Pythonic interface.  Various wrappers and utility
functions are also part of the distribution; following Python's
batteries included approach, there are various interesting devices
supported out-of-the-box - or at least there will be soon!

Plans
-----
 * Add more examples: SPI devices, knight-rider effects, input devices, MIDI...
 * Perhaps add support for D2XX driver, though the name then becomes a
   slight liability ;)
 * General code quality improvements: solid unit tests, decent documentation.

License
-------

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>

pylibftdi is released under the MIT licence; see the file "LICENSE.txt"
for information.

All trademarks referenced herein are property of their respective
holders.
libFTDI itself is developed by Intra2net AG.  No association with
Intra2net is claimed or implied, but I have found their library
helpful and had fun with it...

