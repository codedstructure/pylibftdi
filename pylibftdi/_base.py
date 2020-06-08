"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2020 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: https://github.com/codedstructure/pylibftdi

"""

# This module contains things needed by at least one other
# module so as to prevent circular imports.

__ALL__ = ['FtdiError', 'LibraryMissingError']


class FtdiError(Exception):
    pass


class LibraryMissingError(FtdiError):
    pass
