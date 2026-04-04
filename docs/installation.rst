Installation
============

Unsurprisingly, ``pylibftdi`` depends on ``libftdi``, and installing this varies
according to your operating system. Chances are that following one of the
following instructions will install the required prerequisites. If not, be
aware that libftdi in turn relies on ``libusb``.

Installing ``pylibftdi`` itself is straightforward - it is a pure Python package
(using ``ctypes`` for bindings), and has no dependencies outside the Python
standard library for installation. Don't expect it to work happily without
``libftdi`` installed though :-)

::

    $ pip install pylibftdi

Depending on your environment, you may want to set up a `virtual environment`_.

.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/

Windows
-------

I perform only limited testing of pylibftdi on Windows, but it should work
correctly provided the requirements of libftdi and libusb are correctly
installed.

Recent libftdi binaries for Windows seem to be available from the picusb_
project on Sourceforge. Download libftdi1-1.5_devkit_x86_x64_19July2020.zip
or later from that site, which includes the required drivers, or search for
'libftdi windows' for other options.

.. _picusb: https://sourceforge.net/projects/picusb/files/

Mac OS X
--------

I suggest using homebrew_ to install libftdi::

    $ brew install libftdi

.. _homebrew: https://brew.sh/

On macOS, Apple does not include a built-in FTDI driver (it was removed in
macOS Monterey), but FTDI's own VCP driver may be installed by other software
and will conflict with libftdi. See the Troubleshooting_ section for details.

.. _Troubleshooting: troubleshooting.html#macos

Linux
-----

There are two steps in getting a sensible installation in Linux systems:

1. Getting ``libftdi`` and its dependencies installed
2. Ensuring permissions allow access to the device without requiring root
   privileges. Symptoms of this not being done are programs only working
   properly when run with ``sudo``, giving '-4' or '-8' error codes in
   other cases.

Each of these steps will be slightly different depending on the distribution
in use.

Debian (Raspberry Pi) / Ubuntu etc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Debian-based systems (including Ubuntu, Raspberry Pi OS, etc), the
runtime library package provides what pylibftdi needs::

    $ sudo apt-get install libftdi1-2

The following works to give normal users access to FTDI devices without
needing root permissions:

1. Create a file ``/etc/udev/rules.d/99-libftdi.rules``. You will need sudo
   access to create this file.
2. Put the following in the file::

     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="dialout", MODE="0660"
     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", GROUP="dialout", MODE="0660"
     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6011", GROUP="dialout", MODE="0660"
     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP="dialout", MODE="0660"
     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", GROUP="dialout", MODE="0660"

The list of USB product IDs above matches the default used by ``pylibftdi``, but
some FTDI devices may use other USB PIDs. You could try removing the match on
``idProduct`` altogether, just matching on the FTDI vendor ID as follows::

     SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", GROUP="dialout", MODE="0660"

Or use ``lsusb`` or similar to determine the exact values to use (or try checking
``dmesg`` output on device insertion / removal).
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

See https://wiki.debian.org/udev for more on writing udev rules.

Arch Linux
~~~~~~~~~~

The ``libftdi`` package (sensibly enough) provides the ``libftdi`` library::

    $ sudo pacman -S libftdi

Similar udev rules to those above for Debian should be included (again in
``/etc/udev/rules.d/99-libftdi.rules`` or similar), though the GROUP directive
should be changed to set the group to 'users'::

   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="users", MODE="0660"
   SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", GROUP="users", MODE="0660"
   (etc...)

Testing installation
--------------------

Connect your device, and run the following (as a regular user)::

    $ python3 -m pylibftdi.examples.list_devices

If all goes well, the program should report information about each connected
device. If no information is printed, but it is when run with ``sudo``, a
possibility is permissions problems - see the section under Linux above
regarding ``udev`` rules.

If the above works correctly, then try the following::

    $ python3 -m pylibftdi.examples.led_flash

Even without any LED connected, this should 'work' without any error - quit
with Ctrl-C. Likely errors at this point are either permissions problems
(e.g. udev rules not working), or not finding the device at all - although
the earlier stage is likely to have failed if this were the case.
