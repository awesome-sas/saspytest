"""Tests for greetings.sas autocall macro."""

# pylint: disable=duplicate-code

from pathlib import Path

import pytest

from saspytest import (
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    submit_sas_file,
)

pytestmark = pytest.mark.integration

SAS_PATH = Path(__file__).resolve().parent / "greetings.sas"


def test_greetings_macro_includes_warning_on_missing_name(sas_session):
    """Macro should raise a warning when called without a name."""
    submit_sas_file(sas_session, SAS_PATH)

    result = sas_session.submit(r"%greetings();")
    log = result["LOG"]
    assert_log_contains(log, "WARNING: No name provided to GREETINGS macro.")
    assert_log_not_contains(log, "ERROR:")


def test_greetings_macro_logs_proper_greeting(sas_session):
    """Calling %greetings with a name writes NOTE and greeting to log."""
    submit_sas_file(sas_session, SAS_PATH)

    sas_session.submit("options notes;")

    result = sas_session.submit(r"%greetings(Mary);")
    log = result["LOG"]
    assert_no_errors(log)
    assert_log_contains(log, "NOTE: Invoking greetings macro for Mary")
    assert_log_contains(log, "Hello, Mary!")
