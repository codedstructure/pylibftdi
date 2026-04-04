Developing pylibftdi
--------------------

How do I checkout and use the latest development version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    `pylibftdi` is currently developed on GitHub, though started out as a Mercurial
    repository on bitbucket.org. There may still be references to old bitbucket issues
    in the docs.

`pylibftdi` is developed using uv_, and a Dockerfile plus Makefile make development
tasks straightforward. In any case, start with a local clone of the repository::

    $ git clone https://github.com/codedstructure/pylibftdi
    $ cd pylibftdi

.. _uv: https://docs.astral.sh/uv/

Note that `pylibftdi` itself only requires the Python standard library for normal use.
The development dependencies (``pytest``, ``ruff``, ``mypy``) are declared in the
``[dependency-groups]`` section of ``pyproject.toml`` and are only needed for
development and testing.

There are then two main approaches, though pick and mix the different elements to suit:

**uv and docker**
If `make` and `docker` are available in your environment, the easiest way to do development
may be to simply run `make shell`. This creates an Ubuntu-based docker environment with
`libftdi`, `uv`, and other requirements pre-installed, and drops into a shell where the
current `pylibftdi` code is available.

`make` on its own will run through all the unittests and linting available for `pylibftdi`,
and is a useful check to make sure things haven't been broken.

The downside of running in a docker container is that USB support to actual FTDI devices
may be lacking...

**local install with uv**
With uv_ installed, run ``uv sync`` from the project root. This creates a ``.venv``
virtual environment, installs the development dependencies from ``uv.lock``, and
installs ``pylibftdi`` itself in editable mode — no separate activation step is needed
to run tools::

    .../pylibftdi$ uv sync
    .../pylibftdi$ uv run pytest
    .../pylibftdi$ uv run ruff check src tests

If you prefer to work inside an activated virtual environment::

    .../pylibftdi$ uv sync
    .../pylibftdi$ source .venv/bin/activate
    (pylibftdi) .../pylibftdi$ pytest

.. note::

    The ``uv.lock`` file pins all dependency versions for reproducible installs.
    To upgrade all dependencies to their latest allowed versions, run ``uv lock
    --upgrade``, or target a single package with ``uv lock --upgrade-package
    pytest``. Follow either with ``uv sync`` to apply the changes to the virtual
    environment.

How do I run the tests?
~~~~~~~~~~~~~~~~~~~~~~~

From the root directory of a cloned pylibftdi repository, run::

    .../pylibftdi$ uv run pytest

Or, with a virtualenv already activated::

    (pylibftdi) .../pylibftdi$ pytest

The standard ``unittest`` runner also works if preferred::

    (pylibftdi) .../pylibftdi$ python3 -m unittest discover

How do I make a PyPI release?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure the working tree is clean, all tests pass, and ``CHANGES.txt`` is up to date.
Update the version number in ``pyproject.toml``, sync uv, then tag the commit::

    .../pylibftdi$ vim pyproject.toml CHANGES.txt  # update with new version
    .../pylibftdi$ uv sync --upgrade
    .../pylibftdi$ make  # ensure everything works
    .../pylibftdi$ git add pyproject.toml uv.lock CHANGES.txt
    .../pylibftdi$ git commit -m "Release 0.x.0"
    .../pylibftdi$ git tag 0.x.0

Build the distribution artifacts using ``uv build`` (or ``make build``, which runs
the same command inside the docker container)::

    .../pylibftdi$ uv build

This produces a source distribution and a wheel under ``dist/``.

Publish to PyPI using ``uv publish``. A PyPI API token is required; either
export it as an environment variable or pass it directly::

    .../pylibftdi$ uv publish --token pypi-...

    # or via environment variable
    .../pylibftdi$ UV_PUBLISH_TOKEN=pypi-... uv publish

.. note::

    To do a dry run first, publish to TestPyPI::

        .../pylibftdi$ uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-...

    You can verify the result at https://test.pypi.org/project/pylibftdi/

Finally, push the tag::

    .../pylibftdi$ git push origin main --tags
