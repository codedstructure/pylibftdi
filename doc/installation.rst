Installation
============



Windows
------

libftdi

Mac OS X
--------

See codedstructure.net/pylibftdi/...

Linux
-----

One potential issue is with permissions to access the device, which can be
seen as a error when opening devices (with a '-4' error code).
The solution is to add udev rules to deal with the devices - the following
works for me under Arch linux:

   SUBSYSTEMS="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP=="users", MODE="0660"
   SUBSYSTEMS="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP=="users", MODE="0660"

Repeat for any other required USB PIDs. You'll probably find a more appropriate GROUP than 'users' depending on your Linux distribution.
