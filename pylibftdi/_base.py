"""
pylibftdi - python wrapper for libftdi

Copyright (c) 2010-2012 Ben Bass <benbass@codedstructure.net>
See LICENSE file for details and (absence of) warranty

pylibftdi: http://bitbucket.org/codedstructure/pylibftdi

"""

# This module contains things needed by at least one other
# module so as to prevent circular imports.

__ALL__ = ['Refuser', 'ParrotEgg', 'DeadParrot', 'FtdiError']


class Refuser(object):

    def __getattribute__(self, key):
        # perhaps we should produce an appropriate quote at random...
        raise TypeError(object.__getattribute__(self, 'message'))

    def __setattr__(self, key, val):
        raise TypeError(object.__getattribute__(self, 'message'))

    def __call__(self, *o, **kw):
        raise TypeError(object.__getattribute__(self, 'message'))


class ParrotEgg(Refuser):
    message = "This object is not yet... (missing open()?)"


class DeadParrot(Refuser):
    message = "This object is no more!"


class FtdiError(Exception):
    pass
