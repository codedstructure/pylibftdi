Welcome to pylibftdi's documentation!
=====================================

pylibftdi is a simple library interacting with FTDI devices to provide
serial and parallel IO from Python.

The two main use cases it serves are:

* the need to control or monitor external equipment, for which a FTDI
  module may be a cheap and reliable starting point.

* the need to interact with existing devices which are known to contain
  FTDI chipsets for their USB interface.

FTDI (http://www.ftdichip.com) create devices (chipsets, modules,
cables etc) to interface devices to the USB port of your computer.

libftdi (http://www.intra2net.com/en/developer/libftdi/) is an open source
driver to communicate with these devices, and runs on top of libusb.
It works on Windows, Linux, and Mac OS X, and likely other systems too.

pylibftdi is a pure Python module which interfaces (via ctypes) to libftdi,
exposing a simple file-like API to connected devices. It supports serial and
parallel IO in a straight-forward way, and aims to be one of the simplest
ways of interacting with the world outside your PC.

Contents
========

.. toctree::
   :maxdepth: 2

   introduction
   quickstart
   installation
   basic_usage
   advanced_usage
   how_to
   troubleshooting
   pylibftdi

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

