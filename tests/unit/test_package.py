"""Unit tests for package metadata and public package attributes."""

from importlib.metadata import version
from pathlib import Path
import tomllib

import saspytest


def test_public_version_matches_distribution_metadata():
    """The public version must come from the installed distribution metadata."""
    assert saspytest.__version__ == version("saspytest")


def test_public_version_matches_repository_metadata():
    """The checkout tests must run against the version declared by the checkout."""
    project_file = Path(__file__).parents[2] / "pyproject.toml"
    with project_file.open("rb") as stream:
        project_version = tomllib.load(stream)["project"]["version"]

    assert saspytest.__version__ == project_version


def test_all_public_exports_are_available():
    """Every name in the supported package export list must resolve."""
    assert all(hasattr(saspytest, name) for name in saspytest.__all__)
