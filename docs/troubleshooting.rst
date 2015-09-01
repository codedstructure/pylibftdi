pylibftdi troubleshooting
=========================

Once up-and-running, pylibftdi is designed to be very simple, but sometimes
getting it working in the first place can be more difficult.

Error messages
--------------

``FtdiError: unable to claim usb device. Make sure the default FTDI driver is not in use (-5)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This indicates a conflict with FTDI's own drivers, and is (as far as I know)
mainly a problem on Mac OS X, where they can be disabled (until reboot) by
unloading the appropriate kernel module.

TODO:   investigate ways of unloading the driver in the background e.g. as
a part of some pylibftdi application startup itself?.  The need to do this
action as root may make things trickier.

OS X Mavericks, Yosemite and later
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Starting with OS X Mavericks, OS X includes kernel drivers which will reserve
the FTDI device by default. This needs unloading before `libftdi` will be able
to communicate with the device::

    sudo kextunload -bundle-id com.apple.driver.AppleUSBFTDI

Similarly to reload it::

    sudo kextload -bundle-id com.apple.driver.AppleUSBFTDI

OS X Mountain Lion and earlier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Whereas Mavericks includes an FTDI driver directly, earlier versions of OS X
did not, and if this issue occurred it would typically as a result of
installing some other program - for example the Arduino IDE.

As a result, the kernel module may have different names, but `FTDIUSBSerialDriver.kext`
is the usual culprit. Unload the kernel driver as follows::

    sudo kextunload /System/Library/Extensions/FTDIUSBSerialDriver.kext

To reload the kernel driver, do the following::

    sudo kextload /System/Library/Extensions/FTDIUSBSerialDriver.kext

If you aren't using whatever program might have installed it, the driver
could be permanently removed (to prevent the need to continually unload it),
but this is dangerous::

    sudo rm /System/Library/Extensions/FTDIUSBSerialDriver.kext

Scripts are installed to perform these actions which are installed with
pylibftdi; run `ftdi_osx_driver_unload` to unload the kernel driver and
`ftdi_osx_driver_reload` to reload it. These commands are useful when
other programs require frequent access to FTDI devices; the Arduino IDE
running with FTDI devices (note many newer Arduino models use native USB
rather than FTDI interfaces).

Diagnosis
---------

Getting a list of USB devices

Mac OS X
~~~~~~~~

Start 'System Information', then select Hardware > USB, and look for your
device. On the command line, ``system_profiler SPUSBDataType`` can be used.
In the following example I've piped it into ``grep -C 7 FTDI``, to print 7
lines either side of a match on the string 'FTDI'::

    ben$ system_profiler SPUSBDataType | grep -C 7 FTDI
            UM232H:

              Product ID: 0x6014
              Vendor ID: 0x0403  (Future Technology Devices International Limited)
              Version: 9.00
              Serial Number: FTUBIOWF
              Speed: Up to 480 Mb/sec
              Manufacturer: FTDI
              Location ID: 0x24710000 / 7
              Current Available (mA): 500
              Current Required (mA): 90

            USB Reader:

              Product ID: 0x4082

Linux
~~~~~
Use ``lsusb``. Example from my laptop::

    ben@ben-laptop:~$ lsusb
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
    Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
    Bus 003 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 004 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 005 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 006 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 007 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 008 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    Bus 008 Device 011: ID 0a5c:217f Broadcom Corp. Bluetooth Controller
    Bus 002 Device 009: ID 17ef:481d Lenovo 
    Bus 002 Device 016: ID 0403:6014 Future Technology Devices International, Ltd FT232H Single HS USB-UART/FIFO IC


Where did my ttyUSB devices go?
-------------------------------
When a `pylibftdi.Device()` is opened, any kernel device which was previously
present will become unavailable. On Linux for example, a serial-capable FTDI
device will (via the `ftdi_sio` driver) create a device node such as
`/dev/ttyUSB0` (or ttyUSB1,2,3 etc). This device allows use of the FTDI device
as a simple file in the Linux filesystem which can be read and written.
Various programs such as the Arduino IDE (at least when communicating with
some board variants) and libraries such as `PySerial` will use this device.
Once libftdi opens a device, the corresponding entry in /dev/ will disappear.
Prior to `pylibftdi` version 0.16, the simplest way to get the device node to
reappear would be to unplug and replug the USB device itself. Starting from
0.16, this should no longer be necessary as the kernel driver (which exports
`/dev/ttyUSB...`) is reattached when the `pylibftdi` device is closed. This
behaviour can be controlled by the `auto_detach` argument (which is defaulted
to `True`) to the `Device` class; setting it to `False` reverts to the old
behaviour.

Gathering information
---------------------
Starting with pylibftdi version 0.15, an example script to gather system
information is included, which will help in any diagnosis required.

Run the following::

    python -m pylibftdi.examples.info

this will output a range of information related to the versions of libftdi
libusb in use, as well as the system platform and Python version, for example::

    pylibftdi version     : 0.16.0pre
    libftdi version       : libftdi_version(major=1, minor=1, micro=0, version_str='1.1', snapshot_str='v1.1-12-g2ecba57')
    libftdi library name  : libftdi1.so.2
    libusb version        : libusb_version(major=1, minor=0, micro=17, nano=10830, rc='', describe='http://libusbx.org')
    libusb library name   : libusb-1.0.so.0
    Python version        : 2.7.6
    OS platform           : Linux-3.13.0-55-generic-x86_64-with-Ubuntu-14.04-trusty
