"""Tests for the greeter SAS program."""

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

MACRO_PATH = Path(__file__).resolve().parent / "greetings.sas"
PROGRAM_PATH = Path(__file__).resolve().parent / "greeter.sas"


def test_greeter_program_logs_greeting(sas_session):
    """Ensure the macro is in session before running the program."""
    submit_sas_file(sas_session, MACRO_PATH)

    sas_session.submit("options notes;")

    result = submit_sas_file(sas_session, PROGRAM_PATH)
    log = result["LOG"]
    assert_no_errors(log)
    assert_log_contains(log, "NOTE: Starting greeter program.")
    assert_log_contains(log, "Hello, John!")
    assert_log_not_contains(log, "WARNING:")
