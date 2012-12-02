pylibftdi questions
===================

None of these are yet frequently asked, and perhaps they never will be...
But they are still questions, and they relate to pylibftdi.

Which devices are recommended?
------------------------------

While I used to do a lot of soldering, I prefer the cleaner way of
breadboarding nowadays. As such I can strongly recommend the FTDI DIP
modules which plug into a breadboard nice and easy, can be self-powered
from USB, and can be re-used for dozens of different projects.

I've used (and test against) the following, all of which have 0.1" pin
spacing in two rows 0.5" or 0.6" apart, so will sit across the central
divide of any breadboard:

UB232R
  a small 8 pin device with mini-USB port; serial and CBUS bit-bang.

UM245R
  a 24-pin device with parallel FIFO modes. Full-size USB type B socket.

UM232R
  a 24-pin device with serial and bit-bang modes. Full-size USB type B
  socket.

UM232H
  this contains a more modern FT232H device, and libftdi support is
  fairly recent (requires 0.20 or later). Supports USB 2.0 Hi-Speed mode
  though, and lots of interesting modes (I2C, SPI, JTAG...) which I've not
  looked at yet. Mini-USB socket.

Personally I'd go with the UM232R device for compatibility. It works great
with both UART and bit-bang IO, which I target as the two main use-cases
for pylibftdi. The UM232H is certainly feature-packed though, and I hope
to support some of the more interesting modes in future.

How do I set the baudrate?
--------------------------

In both serial and parallel mode, the internal baudrate generator (BRG) is
set using the ``baudrate`` property of the ``Device`` instance. Reading this
will show the current baudrate (which defaults to 9600); writing to it
will attempt to set the BRG to that value.

On failure to set the baudrate, it will remain at its previous setting.

In parallel mode, the actual bytes-per-second rate of parallel data is
16x the programmed BRG value. This is an effect of the FTDI devices
themselves, and is not hidden by pylibftdi.

How do I send unicode over a serial connection?
-----------------------------------------------

If a ``Device`` instance is created with ``mode='t'``, then text-mode is
activated. This is analogous to opening files; after all, the API is
intentionally modelled on file objects whereever possible.

When text-mode is used, an encoding can be specified. The default is
``latin-1`` for the very practical reason that it is transparent to 8-bit
binary data; by default a text-mode serial connection looks just like a
binary mode one.

An alternative encoding can be used provided in the same constructor call
used to instantiate the ``Device`` class, e.g.::

    >>> dev = Device(mode='t', encoding='utf-8')

Read and write operations will then return / take unicode values.

Whether it is sensible to try and send unicode over a ftdi connection is
a separate issue... At least consider doing codec operations at a higher
level in your application.

How do I run the tests?
-----------------------

Tests aren't included in the distutils distribution, so clone the
repository and run from there. pylibftdi supports Python 2.6/2.7 as well
as Python 3.2+, so these tests can be run for each Python version::

    $ hg clone http://bitbucket.org/codedstructure/pylibftdi
    <various output stuff>
    $ cd pylibftdi
    $ python2.7 -m unittest discover
    ................
    ----------------------------------------------------------------------
    Ran 16 tests in 0.011s

    OK
    $ python3.3 -m unittest discover
    ................
    ----------------------------------------------------------------------
    Ran 16 tests in 0.015s

    OK
    $

How do I use multiple-interface devices?
----------------------------------------

Some FTDI devices have multiple interfaces, for example the FT2232H has 2
and the FT4232H has four. In terms of accessing them, they can be
considered as independent devices; once a connection is established to one
of them, it is isolated from the other interfaces.

To select which interface to use when opening a connection to a specific
interface on a multiple-interface device, use the ``interface_select``
parameter of the Device (or BitBangDevice) class constructor.
The value should be one of the following values. Symbolic constants are
provided in the pylibftdi namespace.

    ==================== =============
    ``interface_select`` Meaning
    -------------------- -------------
    INTERFACE_ANY (0)    Any interface
    INTERFACE_A (1)      INTERFACE A
    INTERFACE_B (2)      INTERFACE B
    INTERFACE_C (3)      INTERFACE C
    INTERFACE_D (4)      INTERFACE D
    ==================== =============

You should be able to open multiple ``Device``\s with different
``interface_select`` settings.
*Thanks to Daniel Forer for testing multiple device support.*
