"""Tests for the convert_numbers SAS program."""

# pylint: disable=duplicate-code

from pathlib import Path

import pytest

from saspytest import (
    assert_columns_exist,
    assert_dataset_exists,
    assert_datasets_equal,
    assert_macro_value,
    assert_no_errors,
    assert_record_count,
    submit_sas_file,
)

pytestmark = pytest.mark.integration

PROGRAM_PATH = Path(__file__).resolve().parents[2] / "programs" / "convert_numbers.sas"


def test_convert_numbers_program_creates_expected_output(sas_session, _roman_assets):
    """Program should create the expected Roman numeral output dataset."""
    result = sas_session.submit(f"""
        libname verify "{_roman_assets["root"] / "testdata"}";
        """)
    assert_no_errors(result["LOG"])

    result = submit_sas_file(sas_session, PROGRAM_PATH)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas_session, "SASPYTEST_ROMAN_INPUT")
    assert_dataset_exists(sas_session, "SASPYTEST_ROMAN_OUTPUT")
    assert_record_count(sas_session, "SASPYTEST_ROMAN_OUTPUT", 5)
    assert_columns_exist(sas_session, "SASPYTEST_ROMAN_OUTPUT", ["number", "roman"])
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_STATUS", "COMPLETE")
    assert_datasets_equal(
        sas_session,
        "SASPYTEST_ROMAN_OUTPUT",
        "SASPYTEST_ROMAN_EXPECTED",
        libref1="WORK",
        libref2="VERIFY",
    )
