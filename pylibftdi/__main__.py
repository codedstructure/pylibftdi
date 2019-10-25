"""
pylibftdi.__main__

This module exists to support `python -im pylibftdi` as a REPL with appropriate
modules and constants already loaded.

e.g.

    $ python3 -im pylibftdi
    >>> d = Device()
    >>> d.write('Hello World')
"""

from pylibftdi import *
