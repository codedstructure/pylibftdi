"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2014 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""
from pylibftdi.device import Device

from ctypes import c_uint16, byref

CTS_MASK = 1 << 4
DSR_MASK = 1 << 5
RI_MASK = 1 << 6


class SerialDevice(Device):
    """
    simple subclass to support serial(rs232) lines

    cts, dsr, ri - input
    dtr, rts - output

    Note: These lines are all active-low by default, though this can be
    changed in the EEPROM settings. pylibftdi does not attempt to hide
    these settings, and simply writes out the given values (i.e. '1'
    will typically make an output line 'active' - and therefore low)
    """

    _dtr = None
    _rts = None

    @property
    def dtr(self):
        """
        set (or get the previous set) state of the DTR line

        :return: the state of the DTR line; None if not previously set
        """
        return self._dtr

    @dtr.setter
    def dtr(self, value):
        value &= 1
        if value != self._dtr:
            self.ftdi_fn.ftdi_setdtr(value)

        self._dtr = value

    @property
    def rts(self):
        """
        set (or get the previous set) state of the DTR line

        :return: the state of the RTS line; None if not previously set
        """
        return self._rts

    @rts.setter
    def rts(self, value):
        value &= 1
        if value != self._rts:
            self.ftdi_fn.ftdi_setrts(value)

        self._rts = value

    def _modem_status(self):
        status = c_uint16()
        self.ftdi_fn.ftdi_poll_modem_status(byref(status))
        return status.value

    @property
    def cts(self):
        """
        get the state of CTS (1 = 'active')
        """
        return int(bool(self._modem_status() & CTS_MASK))

    @property
    def dsr(self):
        """
        get the state of DSR (1 = 'active')
        """
        return int(bool(self._modem_status() & DSR_MASK))

    @property
    def ri(self):
        """
        get the state of RI (1 = 'active')
        """
        return int(bool(self._modem_status() & RI_MASK))
