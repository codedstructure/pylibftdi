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

I perform only limited testing of pylibftdi on Windows, but it should work
correctly provided the requirements of libftdi and libusb are correctly
installed.

Recent libftdi binaries for Windows seem to be available from the picusb_
project on Sourceforge. Download libftdi1-1.1_devkit_x86_x64_21Feb2014.zip
or later from that site, which includes the required

.. _picusb: http://sourceforge.net/projects/picusb/files/

Installing libraries on Windows is easier with recent versions of Python
(2.7.9, 3.4+) installing `pip` directly, so the standard approach of
`pip install pylibftdi` will now easily work on Windows.

Mac OS X
--------

I suggest using homebrew_ to install libftdi::

    $ brew install libftdi

.. _homebrew: http://mxcl.github.com/homebrew/

On OS X Mavericks (and presumably future versions) Apple include a driver for
FTDI devices. This needs unloading before ``libftdi`` can access FTDI devices
directly. See the Troubleshooting_ section for instructions.

.. _Troubleshooting: troubleshooting.html#os-x-mavericks

Linux
-----

There are two steps in getting a sensible installation in Linux systems:

1. Getting ``libftdi`` and its dependencies installed
2. Ensuring permissions allow access to the device without requiring root
   privileges. Symptoms of this not being done are programs only working
   properly when run with ``sudo``, giving '-4' or '-8' error codes in
   other cases.

Each of these steps will be slightly different depending on the distribution
in use. I've tested ``pylibftdi`` on Debian Wheezy (on a Raspberry Pi),
Ubuntu (various versions, running on a fairly standard ThinkPad laptop),
and Arch Linux (running on a PogoPlug - one of the early pink ones).

Debian (Raspberry Pi) / Ubuntu etc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Debian like systems (including Ubuntu, Mint, Debian, etc), the package
`libftdi-dev` should give you what you need as far as the libftdi library
is concerned::

    $ sudo apt-get install libftdi-dev

The following works for both a Raspberry Pi (Debian Wheezy) and Ubuntu 12.04,
getting ordinary users (e.g. 'pi' on the RPi) access to the FTDI device without
needing root permissions:

1. Create a file ``/etc/udev/rules.d/99-libftdi.rules``. You will need sudo
   access to create this file.
2. Put the following in the file::

     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="dialout", MODE="0660"
     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP="dialout", MODE="0660"

Some FTDI devices may use other USB PIDs. You could try removing the match on
`idProduct` altogether, just matching on the FTDI vendor ID as follows::

     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", GROUP="dialout", MODE="0660"

Or use `lsusb` or similar to determine the exact values to use (or try checking
`dmesg` output on device insertion / removal).
``udevadm monitor --environment`` is also helpful, but note that the environment
'keys' it gives are different to the attributes (filenames within /sys/devices/...)
which the ATTRS will match.  Perhaps ENV{} matches work just as well, though I've
only tried matching on ATTRS.

Note that changed udev rules files will be picked up automatically by the udev
daemon, but will only be acted upon on device actions, so unplug/plug in the
device to check whether you're latest rules iteration actually works :-)

Also note that the udev rules above assume that your user is in the 'dialout'
group - if not, add it to your user with the following, though note that this
will not apply immediately, not a full reboot may be needed on some systems::

   sudo usermod -aG dialout $USER

See http://wiki.debian.org/udev for more on writing udev rules.

Arch Linux
~~~~~~~~~~

The `libftdi` package (sensibly enough) provides the `libftdi` library::

    $ sudo pacman -S libftdi

Similar udev rules to those above for Debian should be included (again in
``/etc/udev/rules.d/99-libftdi.rules`` or similar), though the GROUP directive
should be changed to set the group to 'users'::

   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="users", MODE="0660"
   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP="users", MODE="0660"

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

Feel free to contact me (@codedstructure on Twitter) if you have any issues with
installation, though be aware I don't have much in the way of Windows systems
to test.
