Bit-bang mode
=============

Bit-bang mode allows the programmer direct access (both read and write) to the state of the IO lines from a compatible FTDI device.

The interface provided by FTDI is intended to mirror the type of usage on a microcontroller, and is similar to the 'user port' on many old 8-bit computers such as the BBC Micro and Commodore 64.

The basic model is to have two 8 bit ports - one for data, and one for 'direction'. The data port maps each of the 8 bits to 8 independent IO signals, each of which can be configured separately as an 'input' or an 'output'.

In pylibftdi, the data port is given by the ``port`` attribute of a BitBangDevice instance, and the direction control is provided by the ``direction`` attribute. Both these attributes are implemented as Python properties, so no method calls are needed on them - simple read and write in Python-land converts to read and write in the physical world seen by the FTDI device.

The direction register maps to 

where each bit maps to a separate digital signal, 

Read-Modify-Write
-----------------

Port vs Latch

Via the augmented assignment operations, pylibftdi ``BitBangDevice`` instances support read-modify-write operations, such as arithmetic (``+=`` etc), bitwise (``&=``), and other logical operations such as shift (``<<=``)

Examples
~~~~~~~~

::

    >>> from pylibftdi import BitBangDevice
    >>>
    >>> with BitBangDevice('FTE00P4L') as bb:
    ...     bb.direction = 0x0F  # four LSB are output(1), four MSB are input(0)
    ...     bb.port |= 2         # set bit 1
    ...     bb.port &= 0xFE      # clear bit 0


    >>> with BitBangDevice() as bb:
    ...     bb.port = 1
    ...     while True:
    ...         # Rotate the value in bb.port
    ...         bb.port = ((bb.port << 1) | ((bb.port >> 8) & 1)) & 0xFF
    ...         time.sleep(1)


The `Bus` class
---------------

Dealing with bit masks and shifts gets messy quickly. Some languages such as C and C++ provide direct support for accessing bits - or series of consecutive bits - with bitfields. The ``Bus`` class provides the facility to provide a similar level of support to pylibftdi ``BitBangDevice`` classes.

As an example, consider an HD44780 LCD display. These have a data channel of either 4 or 8 bits, and a number of additional status lines - ``rs`` which acts as a register select pin - indicating whether a data byte is a command (0) or data (1), and ``e`` - clock enable.::

    class LCD(object):
        """
        The UM232R/245R is wired to the LCD as follows:
           DB0..3 to LCD D4..D7 (pin 11..pin 14)
           DB6 to LCD 'RS' (pin 4)
           DB7 to LCD 'E' (pin 6)
        """
        data = Bus(0, 4)
        rs = Bus(6)
        e = Bus(7)

