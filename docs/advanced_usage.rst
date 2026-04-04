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
    >>>    dev.ftdi_fn.ftdi_set_bitmode(1, 0x01)
    >>>    dev.write('\x00\x01\x00')
    >>>    dev.ftdi_fn.ftdi_set_bitmode(0, 0x00)
    >>>    dev.write('Hello World!!!')


The libftdi_ documentation should be consulted in conjunction with the
ctypes_ reference for guidance on using these features.

.. _libftdi: http://www.intra2net.com/en/developer/libftdi/documentation/
.. _ctypes: http://docs.python.org/library/ctypes.html

Selecting the underlying libftdi library
----------------------------------------

Since pylibftdi 0.12, the Driver exposes ``libftdi_version()`` and ``libusb_version()``
methods, which return a tuple whose first three entries correspond to major, minor,
and micro versions of the libftdi driver being used.

Note there are two major versions of `libftdi` - libftdi1 can coexist with
the earlier 0.x versions - it is now possible to select which library to
load when instantiating the Driver. Note on at least Ubuntu Linux, the `libftdi1`
*OS package* actually refers to `libftdi 0.20` (or similar), whereas `libftdi1-2`
refers to the more recent 1.x release (currently 1.5)::

    Python 3.10.6 (main, May 29 2023, 11:10:38) [GCC 11.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from pylibftdi import Driver
    >>> Driver().libftdi_version()
    libftdi_version(major=1, minor=5, micro=0, version_str='1.5', snapshot_str='unknown')
    >>> Driver("ftdi1").libftdi_version()
    libftdi_version(major=1, minor=5, micro=0, version_str='1.5', snapshot_str='unknown')
    >>> Driver("ftdi").libftdi_version()
    libftdi_version(major=0, minor=0, micro=0, version_str='< 1.0 - no ftdi_get_library_version()', snapshot_str='unknown')

If both are installed, ``pylibftdi`` prefers libftdi1 (e.g. libftdi 1.5) over libftdi (e.g. 0.20).
Since different OSs require different parameters to be given to find a library,
the default search list given to ctypes.util.find_library is defined by the
`Driver._lib_search` attribute, and this may be updated as appropriate.
By default it is as follows::

    _lib_search = {
        "libftdi": ["ftdi1", "libftdi1", "ftdi", "libftdi"],
        "libusb": ["usb-1.0", "libusb-1.0"],
    }

This covers Windows (which requires the 'lib' prefix), Linux (which requires
its absence), and Mac OS X, which is happy with either.
