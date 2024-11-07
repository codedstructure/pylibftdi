"""
pylibftdi.__main__

This module exists to support `python -im pylibftdi` as a REPL with appropriate
modules and constants already loaded.

e.g.

    $ python3 -im pylibftdi
    >>> d = Device()
    >>> d.write('Hello World')
"""

# This should be aligned with `__all__` in pylibftdi/__init__.py
from pylibftdi import (  # noqa
    ALL_INPUTS,
    ALL_OUTPUTS,
    BB_INPUT,
    BB_OUTPUT,
    USB_PID_LIST,
    USB_VID_LIST,
    BitBangDevice,
    Bus,
    Device,
    Driver,
    FtdiError,
)
