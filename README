pylibftdi
=========

Copyright (c) 2010 Ben Bass <benbass@codedstructure.net>

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

Changes
-------
0.4.1
 * fix release issue
0.4
 * fixed embarrassing bug which caused things not to work on Linux 
   (is now find_library('ftdi') instead of find_library('libftdi'))
 * lots of error checking, new FtdiError exception. Before it just
   tended to segfault if things weren't just-so.
 * get_error() is now get_error_string().  It's still early enough
   to change the API, and if I thought it was get_error_string
   multiple times when I wrote the error checking code, it probably
   should be the more natural thing.
0.3
 * added some examples
 * new Bus class in pylibftdi (though it probably belongs somewhere else)
 * first release on PyPI
0.2
 * fixed various bugs
 * added ftdi_fn and set_baudrate functions in Driver class
 * changed interface in BitBangDriver to direction/port properties
   rather than overriding the read/write functions, which are therefore
   still available as in the Driver class.
0.1
 * first release. Tested with libftdi 0.18 on Mac OS X 10.6 and Linux
  (stock EEEPC 701 Xandros Linux, Ubuntu 10.04)
