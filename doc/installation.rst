Installation
============

Unsurprisingly, `pylibftdi` depends on `libftdi`, and installing this varies
according to your operating system. Chances are that following one of the
following instructions will install the required prerequisites. If not, be
aware that libftdi in turn relies on `libusb`.

Installing pylibftdi itself is straightforward - it is a pure Python package
(using `ctypes` for bindings), and has no dependencies outside the Python
standard library for installation. Don't expect it to work happily without
`libftdi` installed though :-)

::

    $ pip install pylibftdi

Windows
-------

I've not tested pylibftdi on Windows, but recent libftdi binaries seem to be
available from the picusb_ project on google code.

.. _picusb: http://code.google.com/p/picusb

Mac OS X
--------

I suggest using homebrew_ to install libftdi::

    $ brew install libftdi

.. _homebrew: http://mxcl.github.com/homebrew/

Linux
-----

Debian package `libftdi-dev` should give you what you need.

One potential issue is with permissions to access the device, which can be
seen as a error when opening devices (with a '-4' error code).
The solution is to add udev rules to deal with the devices - the following
works for me under Arch linux::

   SUBSYSTEMS="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP=="users", MODE="0660"
   SUBSYSTEMS="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP=="users", MODE="0660"

Some FTDI devices may use other USB PIDs. Use `lsusb` or similar to
determine the exact values to use (or try checking `dmesg` output on
device insertion / removal).
You'll also probably find a more appropriate GROUP than 'users' depending
on your Linux distribution.
