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

MacOS (Mavericks and later)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Starting with OS X Mavericks, OS X includes kernel drivers which will reserve
the FTDI device by default. In addition, the FTDI-provided VCP driver will
claim the device by default. These need unloading before `libftdi` will be able`
to communicate with the device::

    sudo kextunload -bundle-id com.apple.driver.AppleUSBFTDI
    sudo kextunload -bundle-id com.FTDI.driver.FTDIUSBSerialDriver

Similarly to reload them::

    sudo kextload -bundle-id com.apple.driver.AppleUSBFTDI
    sudo kextload -bundle-id com.FTDI.driver.FTDIUSBSerialDriver

Earlier versions of ``pylibftdi`` (prior to 0.18.0) included scripts for
MacOS which unloaded / reloaded these drivers, but these complicated cross-platform
packaging so have been removed. If you are on using MacOS with programs which
need these drivers on a frequent basis (such as the Arduino IDE when using
older FTDI-based Arduino boards), consider implementing these yourself, along the
lines of the following (which assumes ~/bin is in your path)::

    cat << EOF > /usr/local/bin/ftdi_osx_driver_unload
    sudo kextunload -bundle-id com.apple.driver.AppleUSBFTDI
    sudo kextunload -bundle-id com.FTDI.driver.FTDIUSBSerialDriver
    EOF

    cat << EOF > /usr/local/bin/ftdi_osx_driver_reload
    sudo kextload -bundle-id com.apple.driver.AppleUSBFTDI
    sudo kextload -bundle-id com.FTDI.driver.FTDIUSBSerialDriver
    EOF

    chmod +x /usr/local/bin/ftdi_osx_driver_*


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

Note that on recent OS X, libftdi doesn't 'steal' the device, but instead
refuses to open it. The kernel devices can be seen as
`/dev/tty.usbserial-xxxxxxxx`, where `xxxxxxxx` is the device serial number.
FTDI's Application Note AN134_ details this further (see section 'Using
Apple-provided VCP or D2XX with OS X 10.9 & 10.10'). See the section above
under Installation for further details on resolving this.

.. _AN134: http://www.ftdichip.com/Support/Documents/AppNotes/AN_134_FTDI_Drivers_Installation_Guide_for_MAC_OSX.pdf

Gathering information
---------------------
Starting with pylibftdi version 0.15, an example script to gather system
information is included, which will help in any diagnosis required.

Run the following::

    python3 -m pylibftdi.examples.info

this will output a range of information related to the versions of libftdi
libusb in use, as well as the system platform and Python version, for example::

    pylibftdi version     : 0.18.0
    libftdi version       : libftdi_version(major=1, minor=4, micro=0, version_str='1.4', snapshot_str='unknown')
    libftdi library name  : libftdi1.so.2
    libusb version        : libusb_version(major=1, minor=0, micro=22, nano=11312, rc='', describe='http://libusb.info')
    libusb library name   : libusb-1.0.so.0
    Python version        : 3.7.3
    OS platform           : Linux-5.0.0-32-generic-x86_64-with-Ubuntu-19.04-disco

