"""Tests for greetings.sas autocall macro."""

from pathlib import Path

import pytest

from saspytest import (
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    submit_sas_file,
)

pytestmark = pytest.mark.integration

MACRO_PATH = Path(__file__).resolve().parents[2] / "macros" / "greetings.sas"


def test_greetings_macro_includes_warning_on_missing_name(sas_session):
    """Macro should raise a warning when called without a name."""
    # First, load the macro definition
    submit_sas_file(sas_session, MACRO_PATH)

    result = sas_session.submit(r"%greetings();")
    log = result["LOG"]
    assert_log_contains(log, "WARNING: No name provided to GREETINGS macro.")
    assert_log_not_contains(log, "ERROR:")


def test_greetings_macro_logs_proper_greeting(sas_session):
    """Calling %greetings with a name writes NOTE and greeting to log."""
    submit_sas_file(sas_session, MACRO_PATH)

    # Ensure notes are enabled.
    sas_session.submit("options notes;")

    result = sas_session.submit(r"%greetings(Mary);")
    log = result["LOG"]
    assert_no_errors(log)
    assert_log_contains(log, "NOTE: Invoking greetings macro for Mary")
    assert_log_contains(log, "Hello, Mary!")
