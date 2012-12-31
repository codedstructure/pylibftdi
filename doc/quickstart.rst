Quick Start
===========

Install pylibftdi
-----------------

See the installation_ instructions for more detailed requirements, but
hopefully things will work by just running the following::

    $ pip install pylibftdi

.. _installation: installation.html

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

Test some actual IO
-------------------

Output example
~~~~~~~~~~~~~~

Connect an LED between D0 of your bit-bang capable device and ground, via a
330 - 1K ohm resistor as appropriate.

Test the installation and functioning of pylibftdi with the following::

    $ python -m pylibftdi.examples.led_flash

The LED should now flash at approximately 1Hz.

Input example
~~~~~~~~~~~~~

To test some input, remove any connections from the port lines initially,
then run the following, which reads and prints the status of the input lines
regularly::

    $ python -m pylibftdi.examples.pin_read

The ``pin_read`` example is a complete command line application which can
be used to monitor for particular values on the attached device pins, and
output an appropriate error code on match. Repeat the above with a trailing
``--help`` for info.
