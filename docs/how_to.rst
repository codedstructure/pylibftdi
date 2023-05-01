pylibftdi questions
===================

None of these are yet frequently asked, and perhaps they never will be...
But they are still questions, and they relate to pylibftdi.

Using pylibftdi - General
-------------------------

Can I use pylibftdi with device XYZ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the device XYZ is (or uses as it's ) an FTDI device, then possibly. A large
number of devices *will* work, but won't be recognised due to the limited
USB Vendor and Product IDs which pylibftdi checks for.

To see the vendor / product IDs which are supported, run the following::

    >>> from pylibftdi import USB_VID_LIST, USB_PID_LIST
    >>> print(', '.join(hex(pid) for pid in USB_VID_LIST))
    0x403
    >>> print(', '.join(hex(pid) for pid in USB_PID_LIST))
    0x6001, 0x6010, 0x6011, 0x6014, 0x6015

If a FTDI device with a VID / PID not matching the above is required, then
the device's values should be appended to the appropriate list after import::

    >>> from pylibftdi import USB_PID_LIST, USB_VID_LIST, Device
    >>> USB_PID_LIST.append(0x1234)
    >>>
    >>> dev = Device()  # will now recognise a device with PID 0x1234.

Which devices are recommended?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Using pylibftdi - Programming
-----------------------------

How do I set the baudrate?
~~~~~~~~~~~~~~~~~~~~~~~~~~

In both serial and parallel mode, the internal baudrate generator (BRG) is
set using the ``baudrate`` property of the ``Device`` instance. Reading this
will show the current baudrate (which defaults to 9600); writing to it
will attempt to set the BRG to that value.

On failure to set the baudrate, it will remain at its previous setting.

In parallel mode, the actual bytes-per-second rate of parallel data is
16x the programmed BRG value. This is an effect of the FTDI devices
themselves, and is not hidden by pylibftdi.

How do I send unicode over a serial connection?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


How do I use multiple-interface devices?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

What is the difference between the ``port`` and ``latch`` BitBangDevice properties?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`latch` reflects the current state of the output latch (i.e. the last value
written to the port), while ``port`` reflects input states as well. Writing to
either ``port`` or ``latch`` has an identical effect, so when pylibftdi is used
only for output, there is no effective difference, and ``port`` is recommended
for simplicity and consistency.

The place where it does make a difference is during read-modify-write
operations. Consider the following::

    >>> dev = BitBangDevice()  # 1
    >>> dev.direction = 0x81   # 2   # set bits 0 and 7 are output
    >>> dev.port = 0           # 3
    >>> for _ in range(255):   # 4
    >>>     dev.port += 1      # 5   # read-modify-write operation

In this (admittedly contrived!) scenario, if one of the input lines D1..D6
were held low, then they would cause the counter to effectively 'stop'. The
``+= 1`` operation would never actually set the bit as required (because it is
an input at 0), and the highest output bit would never get set.

Using ``dev.latch`` in lines 3 and 5 above would resolve this, as the
read-modify-write operation on line 5 is simply working on the in-memory
latch value, rather than reading the inputs, and it would simply count up from
0 to 255 in steps of one, writing the value to the device (which would be
ignored in the case of input lines).

Similar concepts exist in many microcontrollers, for example see
http://stackoverflow.com/a/2623498 for a possibly better explanation, though
in a slightly different context :)

If you aren't using read-modify-write operations (e.g. augmented assignment),
or you have a direction on the port of either ALL_INPUTS (0) or ALL_OUTPUTS
(1), then just ignore this section and use ``port`` :)

What is the purpose of the ``chunk_size`` parameter?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While libftdi is performing I/O to the device, it is not really running Python
code at all, but C library code via ctypes. If there is a significant amount of
data, especially at low baud-rates, this can be a significant delay during which
no Python bytecode is executed. The most obvious result of this is that no
signals are delivered to the Python process during this time, and interrupt
signals (Ctrl-C) will be ignored.

Try the following::

    >>> dev = Device()
    >>> dev.baudrate = 120  # nice and slow!
    >>> dev.write('helloworld' * 1000)

This should take approximately 10 seconds prior to returning, and crucially,
Ctrl-C interruptions will be deferred for all that time. By setting
``chunk_size`` on the device (which may be set either as a keyword parameter
during ``Device`` instantiation, or at a later point as an attribute of the
``Device`` instance), the I/O operations are performed in chunks of at most
the specified number of bytes. Setting it to 0, the default value, disables
this chunking.

Repeat the above command but prior to the write operation, set
``dev.chunk_size = 10``. A Ctrl-C interruption should now kick-in almost
instantly. There is a performance trade-off however; if using ``chunk_size`` is
required, set it as high as is reasonable for your application.

Using pylibftdi - Interfacing
-----------------------------

How do I control an LED?
~~~~~~~~~~~~~~~~~~~~~~~~

pylibftdi devices generally have sufficient output current to sink or source
the 10mA or so which a low(ish) current LED will need. A series resistor is
essential to protect both the LED and the FTDI device itself; a value between
220 and 470 ohms should be sufficient depending on required brightness / LED
efficiency.

How do I control a higher current device?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FTDI devices will typically provide a few tens of milli-amps, but beyond that
things either just won't work, or the device could be damaged. For medium
current operation, a standard bipolar transistor switch will suffice; for
larger loads a MOSFET or relay should be used. (Note a relay will require a
low-power transistor switch anyway). Search online for something like
'mosfet logic switch' or 'transistor relay switch' for more details.

What is the state of an unconnected input pin?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This depends on the device and the EEPROM configuration values. Most devices
will have weak (typ. 200Kohm) pull-ups on input pins, so there is no harm
leaving them floating. Consult the datasheet for your device for definitive
information, but you can always just leave an (unconnected) device and read
it's pins when set as inputs; chances are they will read 255 / 0xFF::

    >>> dev = BitBangDevice(direction=0)
    >>> dev.port
    255

While not recommended for anything serious, this does allow the possibility
of reading a input switch state by simply connecting a switch between an input
pin and ground (possibly with a low value - e.g. 100 ohm -  series resistor to
prevent accidents should it be set to an output and set high...). Note that
with a normal push-to-make switch, the value will read '1' when the switch is
not pressed; pressing it will set the input line value to '0'.

Developing pylibftdi
--------------------

How do I checkout and use the latest development version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`pylibftdi` is currently developed on GitHub, though started out as a Mercurial
repository on bitbucket.org. There may still be references to old bitbucket issues
in the docs.

To use / develop on the latest version, it must first be cloned locally, after
which it can be 'installed'. Clone the repository to a local directory and
install (with the 'develop' target ideally) as follows::

    $ git clone https://github.com/codedstructure/pylibftdi
    $ cd pylibftdi
    $ python3 -m venv env
    $ source env/bin/activate
    (env) $ python3 -m pip install -e .

Note this also creates a virtual environment within the project directory;
see here_

.. _here: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/

Note for now there is only the main branch, so need to worry about which
branch is required.

How do I run the tests?
~~~~~~~~~~~~~~~~~~~~~~~

Tests aren't included in the distutils distribution, so clone the
repository and run from there. pylibftdi supports Python 3.7+::

    $ git clone https://github.com/codedstructure/pylibftdi
    <various output stuff>
    $ cd pylibftdi
    $ python3 -m unittest discover
    ..........................
    ----------------------------------------------------------------------
    Ran 26 tests in 0.007s

    OK

How can I determine and select the underlying libftdi library?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since pylibftdi 0.12, the Driver exposes a ``libftdi_version`` method,
which returns a tuple whose first three entries correspond to major, minor,
and micro versions of the libftdi driver being used.

With the recent (early 2013) release of libftdi1 - which can coexist with
the earlier 0.x versions - it is now possible to select which library to
load when instantiating the Driver::

    Python 2.7.2 (default, Jun 20 2012, 16:23:33)
    [GCC 4.2.1 Compatible Apple Clang 4.0 (tags/Apple/clang-418.0.60)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from pylibftdi import Driver
    >>> Driver().libftdi_version()
    (1, 0, 0, '1.0', 'v1.0-6-gafb9082')
    >>> Driver('ftdi').libftdi_version()
    (0, 99, 0, '0.99', 'v0.17-305-g50d77f8')
    >>> Driver('libftdi1').libftdi_version()
    (1, 0, 0, '1.0', 'v1.0-6-gafb9082')
    >>> Driver(('libftdi1', 'libftdi')).libftdi_version()
    (1, 0, 0, '1.0', 'v1.0-6-gafb9082')
    >>> Driver(('libftdi', 'libftdi1')).libftdi_version()
    (0, 99, 0, '0.99', 'v0.17-305-g50d77f8')
    >>> Driver(('libftdi', 'libftdi1')).libftdi_version()

``pylibftdi`` now prefers libftdi1 over libftdi, if both are installed. Since
different OSs require different parameters to be given to find a library,
the default search list given to ctypes.util.find_library is as follows::

    Driver._dll_list = ('ftdi1', 'libftdi1', 'ftdi', 'libftdi')

This covers Windows (which requires the 'lib' prefix), Linux (which requires
its absence), and Mac OS X, which is happy with either.
