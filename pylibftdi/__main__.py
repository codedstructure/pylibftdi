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
    Driver,
    Device,
    BitBangDevice,
    Bus,
    FtdiError,
    ALL_OUTPUTS,
    ALL_INPUTS,
    BB_OUTPUT,
    BB_INPUT,
    USB_VID_LIST,
    USB_PID_LIST,
)
