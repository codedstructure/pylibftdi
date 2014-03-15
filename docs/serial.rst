Serial mode
===========

The default mode of pylibftdi devices is to behave as a serial UART device, similar to the 'COM1' device found on older PCs. Nowadays most PCs operate with serial devices over USB-serial adapters, which may often include their own FTDI chips. To remain compatible with the RS232 standard however, these adapters will often include level-shifting circuitry which is of no benefit in communicating with other circuits operating at the 3.3 or 5 volt levels the FTDI hardware uses.

The default serial configuration is 9600 baud, 8 data bits, 1 stop bit and no parity (sometimes referred to as 8-N-1_). This is the default configuration of the old 'COM' devices back to the days of the original IBM PC and MS-DOS.

.. _8-N-1: http://en.wikipedia.org/wiki/8-N-1


Setting line parameters
-----------------------

Changing line parameters other than the baudrate is supported via use of the underlying FTDI function calls.

The SerialDevice class
----------------------

While the standard ``Device`` class supports standard ``read`` and ``write`` methods, as well as a ``baudrate`` property, further functionality is provided by the ``SerialDevice`` class, available either as a top-level import from ``pylibftdi`` or through the ``serial_device`` module. This subclasses ``Device`` and adds additional properties to access various control and handshake lines.

The following properties are available:

    ======== ==================== =========
    property meaning              direction
    -------- -------------------- ---------
    ``cts``  Clear To Send        Input
    ``rts``  Ready To Send        Output
    ``dsr``  Data Set Ready       Input
    ``dtr``  Data Transmit Ready  Output
    ``ri``   Ring Indicator       Input
    ======== ==================== =========

Note that these lines are normally active-low, and ``pylibftdi`` makes no attempt to hide this from the user. It is impractical to try to 'undo' this inversion in any case, since it can be disabled in the EEPROM settings of the device. Just be aware if using these lines as GPIO that the electrical sense will be the opposite of the value read. The lines are intended to support handshaking rather than GPIO, so this is not normally an issue; if CTS is connected to RTS, then values written to RTS will be reflected in the value read from CTS.

Subclassing `Device` - A MIDI device
------------------------------------

To abstract application code from the details of any particular interface, it may be helpful to subclass the ``Device`` class, providing the required configuration in the ``__init__`` method to act in a certain way. For example, the MIDI_ protocol used by electronic music devices is an asynchronous serial protocol operating at 31250 baud, and with the same 8-N-1 parameters which pylibftdi defaults to.

.. _MIDI: http://www.midi.org

Creating a ``MidiDevice`` subclass of ``Device`` is straightforward::

    class MidiDevice(Device):
        "subclass of pylibftdi.Device configured for MIDI"

        def __init__(self, *o, **k):
            Device.__init__(self, *o, **k)
            self.baudrate = 31250

Note it is important that the superclass ``__init__`` is called first; calling it on an uninitialised ``Device`` would fail, and even if it succeeded, the superclass ``__init__`` method resets ``baudrate`` to 9600 anyway to ensure a consistent setup for devices which may have been previously used with different parameters.

Use of the ``MidiDevice`` class is simple - as a pylibftdi Device instance, it provides a file-based API. Simply ``read()`` and ``write()`` the data to an instance of the class::

    >>> m = MidiDevice()
    >>> m.write('\x90\x80\x80')
    >>> time.sleep(1)
    >>> m.write('\x80\x00')

