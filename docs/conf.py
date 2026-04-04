import os
import sys
from importlib.metadata import PackageNotFoundError, version as _version

sys.path.insert(0, os.path.abspath("../src"))

project = "pylibftdi"
copyright = "2010-2026, Ben Bass"
try:
    release = _version("pylibftdi")
except PackageNotFoundError:
    # Package not installed; install it first (e.g. `pip install -e .`)
    # Once Python 3.11+ is required, tomllib could read pyproject.toml directly.
    import warnings

    warnings.warn(
        "pylibftdi package not found; install it before building docs. "
        "Version will be reported as 'unknown'.",
        stacklevel=1,
    )
    release = "unknown"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

autodoc_member_order = "groupwise"
autodoc_default_options = {
    "special-members": "__init__",
}

source_suffix = ".rst"
root_doc = "index"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"
