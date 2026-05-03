"""Tests for the number_to_roman macro."""

from pathlib import Path

import pytest

from saspytest import assert_errors, assert_macro_value, assert_no_errors, submit_sas_file

pytestmark = pytest.mark.integration

MACRO_PATH = Path(__file__).resolve().parents[2] / "macros" / "number_to_roman.sas"


def test_number_to_roman_converts_known_values(sas_session, _roman_assets):
    """Macro should convert representative values correctly."""
    submit_sas_file(sas_session, MACRO_PATH)

    result = sas_session.submit("""
        %let SASPYTEST_ROMAN_1 = %number_to_roman(1);
        %let SASPYTEST_ROMAN_4 = %number_to_roman(4);
        %let SASPYTEST_ROMAN_9 = %number_to_roman(9);
        %let SASPYTEST_ROMAN_58 = %number_to_roman(58);
        %let SASPYTEST_ROMAN_944 = %number_to_roman(944);
        """)

    assert_no_errors(result["LOG"])
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_1", "I")
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_4", "IV")
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_9", "IX")
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_58", "LVIII")
    assert_macro_value(sas_session, "SASPYTEST_ROMAN_944", "CMXLIV")


def test_number_to_roman_rejects_values_above_range(sas_session, _roman_assets):
    """Macro should reject values above 999."""
    submit_sas_file(sas_session, MACRO_PATH)

    result = sas_session.submit("""
        %let SASPYTEST_ROMAN_INVALID = %number_to_roman(1000);
        """)

    assert_errors(result["LOG"], ["number_to_roman only supports values between 1 and 999"])


def test_number_to_roman_rejects_zero(sas_session, _roman_assets):
    """Macro should reject values below 1."""
    submit_sas_file(sas_session, MACRO_PATH)

    result = sas_session.submit("""
        %let SASPYTEST_ROMAN_INVALID = %number_to_roman(0);
        """)

    assert_errors(result["LOG"], ["number_to_roman only supports values between 1 and 999"])
