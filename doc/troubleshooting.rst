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

OS X Mountain Lion and earlier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unload the kernel driver::

    sudo kextunload /System/Library/Extensions/FTDIUSBSerialDriver.kext

To reload the kernel driver, do the following::

    sudo kextload /System/Library/Extensions/FTDIUSBSerialDriver.kext

To permanently remove the driver, just delete it::

    sudo rm /System/Library/Extensions/FTDIUSBSerialDriver.kext

OS X Mavericks
~~~~~~~~~~~~~~

Whereas earlier versions of OS X didn't include an FTDI driver directly -
it would typically be installed as part of some other program - Mavericks
includes this in the operating system itself. For this reason, it's probably
a bad idea to delete it, but it can be unloaded as follows::

    sudo kextunload -bundle-id com.apple.driver.AppleUSBFTDI

Similarly to reload it::

    sudo kextload -bundle-id com.apple.driver.AppleUSBFTDI


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
