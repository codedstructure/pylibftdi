pylibftdi
=========

Copyright (c) 2010-2011 Ben Bass <benbass@codedstructure.net>

All rights reserved.


License information
-------------------

See the file "LICENSE" for information terms & conditions
for usage, and a DISCLAIMER OF ALL WARRANTIES.

All trademarks referenced herein are property of their respective
holders.

libFTDI itself is developed by Intra2net AG.  No association with
Intra2net is claimed or implied, but I have found their library
helpful and had fun with it...

History
-------
This package is the result of various bits of work using FTDI's
devices, primarily for controlling external devices.  Some of this
is documented on the codedstructure blog, codedstructure.blogspot.com

At least two other open-source Python FTDI wrappers exist, and each
of these may be best for some projects.

ftd2xx - http://pypi.python.org/pypi/ftd2xx
 - ctypes binding to FTDI's own D2XX driver
pyftdi - http://git.marcansoft.com/?p=pyftdi.git
 - a C extension libftdi binding

pylibftdi exists in the gap between these two projects; ftd2xx uses
the (closed-source) D2XX driver, but provides a high-level Python
interface, while pyftdi works with libftdi but is very low-level.
The aim for pylibftdi is to work with the libftdi, but to provide
a high-level Pythonic interface.  Various wrappers and utility
functions are also part of the distribution; following Python's
batteries included approach, there are various interesting devices
supported out-of-the-box.

Plans
-----
 * Add more examples: SPI devices, knight-rider effects, input devices...
 * Further support for serial usage (as opposed to BitBang)
 * Perhaps add support for D2XX driver, though the name then becomes a
   slight liability ;)

