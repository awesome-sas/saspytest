"""Pytest support library for testing SAS programs through saspy.

The package provides pytest session fixtures, SAS log and dataset assertions,
macro-variable assertions, and file-transfer helpers. The shared session fixture
is available for efficient test runs, while ``require_new_sas_session`` provides
an isolated session when a test needs one.
"""

from importlib.metadata import version as _package_version

__version__ = _package_version("saspytest")

# Session management
from .session import (
    get_sas_session,
    close_sas_session,
    reset_sas_session,
    create_new_sas_session,
    reset_test_state,
    cleanup_test_artifacts,
    # Note: pytest fixtures (sas_session, clean_sas_workspace, require_new_sas_session)
    # are intentionally NOT exported here to avoid interfering with pytest's
    # fixture discovery when tests use `from saspytest import ...`.
)

# File handling
from .files import (
    upload_file,
    download_file,
    submit_sas_file,
)

# Macro assertions
from .macros import assert_macro_value, assert_macro_exists

# Log assertions
from .logs import (
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    assert_no_warnings,
    assert_errors,
    assert_warnings,
)

# Dataset assertions
from .datasets import (
    assert_dataset_exists,
    assert_dataset_not_exists,
    assert_library_exists,
    assert_record_count,
    assert_columns_exist,
    assert_datasets_equal,
    get_dataset_as_df,
)

__all__ = [
    # Session management
    "get_sas_session",
    "close_sas_session",
    "create_new_sas_session",
    # Fixture names are intentionally omitted from exports
    "reset_sas_session",
    "reset_test_state",
    "cleanup_test_artifacts",
    # File handling
    "upload_file",
    "download_file",
    "submit_sas_file",
    # Macro assertions
    "assert_macro_value",
    "assert_macro_exists",
    # Log assertions
    "assert_log_contains",
    "assert_log_not_contains",
    "assert_no_errors",
    "assert_no_warnings",
    "assert_errors",
    "assert_warnings",
    # Dataset assertions
    "assert_dataset_exists",
    "assert_dataset_not_exists",
    "assert_library_exists",
    "assert_record_count",
    "assert_columns_exist",
    "assert_datasets_equal",
    "get_dataset_as_df",
]
