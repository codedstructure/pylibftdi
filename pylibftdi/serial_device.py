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
    modem_status - return a two byte bitfield of various values

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
        set (or get the previous set) state of the RTS line

        :return: the state of the RTS line; None if not previously set
        """
        return self._rts

    @rts.setter
    def rts(self, value):
        value &= 1
        if value != self._rts:
            self.ftdi_fn.ftdi_setrts(value)

        self._rts = value

    @property
    def modem_status(self):
        """
        Layout of the first byte:
        B0..B3 - must be 0
        B4 Clear to send (CTS) 0 = inactive 1 = active
        B5 Data set ready (DTS) 0 = inactive 1 = active
        B6 Ring indicator (RI) 0 = inactive 1 = active
        B7 Receive line signal detect (RLSD) 0 = inactive 1 = active

        Layout of the second byte:
        B0 Data ready (DR)
        B1 Overrun error (OE)
        B2 Parity error (PE)
        B3 Framing error (FE)
        B4 Break interrupt (BI)
        B5 Transmitter holding register (THRE)
        B6 Transmitter empty (TEMT)
        B7 Error in RCVR FIFO

        '{:016b}'.format(d.modem_status)
        '0110000000000001'
        - b5,b6 set in MSB ('2nd byte'), b0 set in first byte
        (despite the libftdi docs saying this shouldn't be set)
        """
        status = c_uint16()
        self.ftdi_fn.ftdi_poll_modem_status(byref(status))
        return status.value

    @property
    def cts(self):
        """
        get the state of CTS (1 = 'active')
        """
        return int(bool(self.modem_status & CTS_MASK))

    @property
    def dsr(self):
        """
        get the state of DSR (1 = 'active')
        """
        return int(bool(self.modem_status & DSR_MASK))

    @property
    def ri(self):
        """
        get the state of RI (1 = 'active')
        """
        return int(bool(self.modem_status & RI_MASK))
