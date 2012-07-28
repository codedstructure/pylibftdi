Quick Start
===========

Install pylibftdi
-----------------

See the _installation instructions for more detailed requirements, but
hopefully things will work by just running the following::

    $ pip install pylibftdi

Connect and enumerate FTDI devices
----------------------------------

Connect the FTDI device to a free USB port. Run the ``list_devices`` example
to enumerate connected FTDI devices::

    $ python -m pylibftdi.examples.list_devices

For each connected device, this will show manufacturer, model identifier,
and serial number. With a single device connected, the output maybe
something like the following:

    ``FTDI:UM232H:FTUBIOWF``

Though hopefully with a different serial number, or else you've either
stolen mine, or you are me...

Test some actual IO (well, at least O)
--------------------------------------

Connect an LED between D0 of your bit-bang capable device and ground, via a
330 - 1K ohm resistor as appropriate.

Test the installation and functioning of pylibftdi with the following::

    $ python -m pylibftdi.examples.led_flash

The LED should now flash at approximately 1Hz.
