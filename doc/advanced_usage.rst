Advanced Usage
==============

``libftdi`` function access
---------------------------

Three attributes of ``Device`` instances are documented which allow direct
access to the underlying ``libftdi`` functionality.

#. ``fdll`` - this is a reference to the loaded ``libftdi`` library, loaded
   via ctypes. This should be used with the normal ctypes protocols.
#. ``ctx`` - this is a reference to the context of the current device
   context. It is managed as a raw ctypes byte-string, so can be modified
   if required at the byte-level using appropriate ``ctypes`` methods.
#. ``ftdi_fn`` - a convenience function wrapper, this is the preferred
   method for accessing library functions for a specific device instance.
   This is a function forwarder to the local ``fdll`` attribute, but also
   wraps the device context and passes it as the first argument. In this
   way, using ``device.ftdi_fn.ft_xyz`` is more like the D2XX driver
   provided by FTDI, in which the device context is passed in at
   initialisation time and then the client no longer needs to care about it.
   A call to::

    >>> device.ftdi_fn.ft_xyz(1, 2, 3)

   is equivalent to the following::

    >>> device.fdll.ft_xyz(ctypes.byref(device.ctx), 1, 2, 3)

   but has the advantages of being shorter and not requiring ctypes to be
   in scope.

    incorrect operations using any of these attributes of devices
    are liable to crash the Python interpreter

Examples
~~~~~~~~

The following example shows opening a device in serial mode, switching
temporarily to bit-bang mode, then back to serial and writing a string.
Why this would be wanted is anyone's guess ;-)

::

    >>> from pylibftdi import Device
    >>>
    >>> with Device() as dev:
    >>>    dev.fn.ftdi_set_bitmode(1, 0x01)
    >>>    dev.write('\x00\x01\x00')
    >>>    dev.fn.ftdi_set_bitmode(0, 0x00)
    >>>    dev.write('Hello World!!!')


The libftdi_ documentation should be consulted in conjunction with the
ctypes_ reference for guidance on using these features.

.. _libftdi: http://www.intra2net.com/en/developer/libftdi/documentation/
.. _ctypes: http://docs.python.org/library/ctypes.html

