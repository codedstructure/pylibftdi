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

Depending on your environment, you may want to use either the ``--user`` flag,
or prefix the command with ``sudo`` to gain root privileges.

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

On Debian like systems (including Ubuntu, Mint, Debian, etc), the package
`libftdi-dev` should give you what you need as far as the libftdi library
is concerned.

One potential issue is with permissions to access the device, which can be
seen as a error when opening devices (with a '-4' or '-8' error code).
The solution is to add udev rules to deal with the devices - the following
works for me under Arch linux::

   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP=="users", MODE="0660"
   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP=="users", MODE="0660"

Under other distributions, other group names are probably needed. On Ubuntu
(12.04 here) I use the ``dialout`` group. Create a file
``/etc/udev/rules.d/99-libftdi.rules`` containing::

   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP=="dialout", MODE="0660"
   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP=="dialout", MODE="0660"

Some FTDI devices may use other USB PIDs. Use `lsusb` or similar to
determine the exact values to use (or try checking `dmesg` output on
device insertion / removal). ``udevadm monitor --environment`` is also helpful,
but note that the environment 'keys' it gives are different to the attributes
(filenames within /sys/devices/...) which the ATTRS will match. Perhaps ENV{}
matches work just as well, though I've only tried matching on ATTRS.

Note that changed udev rules files will be picked up automatically by the udev
daemon, but will only be acted upon on device actions, so unplug/plug in the
device to check whether you're latest rules iteration actually works :-)

See http://wiki.debian.org/udev for more on writing udev rules.

Testing installation
--------------------

Connect your device, and run the following (as a regular user)::

    $ python -m pylibftdi.examples.list_devices

If all goes well, the program should report information about each connected
device. If no information is printed, but it is when run with ``sudo``, a
possibility is permissions problems - see the section under Linux above
regarding udev rules.

If the above works correctly, then try the following::

    $ python -m pylibftdi.examples.led_flash

Even without any LED connected, this should 'work' without any error - quit
with Ctrl-C. Likely errors at this point are either permissions problems
(e.g. udev rules not working), or not finding the device at all - although
the earlier stage is likely to have failed if this were the case.

Feel free to contact me (@codedstructure) if you have any issues with
installation, though be aware I don't have much in the way of Windows systems
to test.
