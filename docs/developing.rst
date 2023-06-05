Developing pylibftdi
--------------------

How do I checkout and use the latest development version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`pylibftdi` is currently developed on GitHub, though started out as a Mercurial
repository on bitbucket.org. There may still be references to old bitbucket issues
in the docs.

`pylibftdi` is developed using poetry_, and a Dockerfile plus Makefile make use
development tasks straightforward. In any case, start with a local clone of the
repository::

    $ git clone https://github.com/codedstructure/pylibftdi
    $ cd pylibftdi

.. _poetry: https://python-poetry.org/

There are then two main approaches, though pick and mix the different elements to suit:

**poetry and docker**
If `make` and `docker` are available in your environment, the easiest way to do development
may be to simply run `make shell`. This creates an Ubuntu-based docker environment with
`libftdi`, `poetry`, and other requirements pre-installed, and drops into a shell where the
current `pylibftdi` code is installed.

`make` on its own will run through all the unittests and linting available for `pylibftdi`,
and is a useful check to make sure things haven't been broken.

The downside of running in a docker container is that USB support to actual FTDI devices
may be lacking...

**editable install with pip**
This assumes that the `venv` and `pip` packages are installed; on some (e.g. Ubuntu)
Linux environments, these may need installing as OS packages. Once installed, perform
an 'editable' install as follows::

    .../pylibftdi$ python3 -m venv env
    .../pylibftdi$ source env/bin/activate
    (env) .../pylibftdi$ python3 -m pip install -e .

Note this also creates a virtual environment within the project directory;
see here_

.. _here: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/

How do I run the tests?
~~~~~~~~~~~~~~~~~~~~~~~

From the root directory of a cloned pylibftdi repository, run the following::

    (env) .../pylibftdi$ python3 -m unittest discover
    .....................................
    ----------------------------------------------------------------------
    Ran 37 tests in 0.038s

    OK

Note that other test runners (such as `pytest`) will also run the tests and may be
easier to extend.

How can I determine and select the underlying libftdi library?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

