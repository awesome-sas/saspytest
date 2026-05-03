"""
Unit tests for log assertion functions.

These tests validate log parsing without requiring a live SAS connection.
"""

import re

import pytest
from saspytest.logs import (
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    assert_no_warnings,
    assert_errors,
    assert_warnings,
)


class TestAssertLogContains:
    def test_contains_string(self):
        log = "NOTE: Data step completed."
        assert_log_contains(log, "Data step completed")

    def test_does_not_contain(self):
        log = "NOTE: Everything is fine."
        with pytest.raises(AssertionError, match="Pattern 'ERROR' not found"):
            assert_log_contains(log, "ERROR")

    def test_custom_message(self):
        log = "NOTE: OK."
        with pytest.raises(AssertionError, match="custom msg"):
            assert_log_contains(log, "MISSING", msg="custom msg")

    def test_regex_mode(self):
        log = "ERROR: File not found."
        assert_log_contains(log, r"ERROR\s*:", regex=True)

    def test_literal_mode_does_not_interpret_regex(self):
        assert_log_contains("NOTE: Value [1]", "[1]")

    def test_invalid_regex_propagates(self):
        with pytest.raises(re.error):
            assert_log_contains("NOTE: Value", "[", regex=True)


class TestAssertLogNotContains:
    def test_not_contains(self):
        log = "NOTE: Success."
        assert_log_not_contains(log, "ERROR")

    def test_contains_raises(self):
        log = "ERROR: Something failed."
        with pytest.raises(AssertionError, match="should not be in SAS log"):
            assert_log_not_contains(log, "ERROR")

    def test_regex_mode(self):
        log = "NOTE: Clean log."
        assert_log_not_contains(log, r"WARNING\s*:", regex=True)

    def test_invalid_regex_propagates(self):
        with pytest.raises(re.error):
            assert_log_not_contains("NOTE: Value", "[", regex=True)

    def test_custom_message(self):
        with pytest.raises(AssertionError, match="custom msg"):
            assert_log_not_contains("ERROR: Failure", "ERROR", msg="custom msg")


class TestAssertNoErrors:
    def test_clean_log(self):
        log = "NOTE: Data step used.\nNOTE: Procedure completed."
        assert_no_errors(log)

    def test_log_with_error(self):
        log = "ERROR: File WORK.MISSING.DATA does not exist."
        with pytest.raises(AssertionError, match="1 ERROR"):
            assert_no_errors(log)

    def test_multiple_errors(self):
        log = "ERROR: First issue.\nERROR: Second issue."
        with pytest.raises(AssertionError, match="2 ERROR"):
            assert_no_errors(log)

    def test_case_and_whitespace_variants(self):
        with pytest.raises(AssertionError, match="1 ERROR"):
            assert_no_errors("  error  : Failure\nNOTE: Finished")

    def test_numbered_sas_error(self):
        with pytest.raises(AssertionError, match="1 ERROR"):
            assert_no_errors("ERROR 180-322: Statement is not valid.")

    def test_error_word_in_note(self):
        # Ensure we don't match "ERROR" inside other words or notes
        log = "NOTE: The error rate is 0%."
        assert_no_errors(log)  # Should not match because pattern is word boundary + colon

    def test_custom_message(self):
        with pytest.raises(AssertionError, match="custom msg"):
            assert_no_errors("ERROR: Failure", msg="custom msg")


class TestAssertNoWarnings:
    def test_clean_log(self):
        log = "NOTE: Data step used."
        assert_no_warnings(log)

    def test_log_with_warning(self):
        log = "WARNING: Missing values detected."
        with pytest.raises(AssertionError, match="1 WARNING"):
            assert_no_warnings(log)

    def test_case_and_whitespace_variants(self):
        with pytest.raises(AssertionError, match="1 WARNING"):
            assert_no_warnings("  warning : Missing values\nNOTE: Finished")

    def test_numbered_sas_warning(self):
        with pytest.raises(AssertionError, match="1 WARNING"):
            assert_no_warnings("WARNING 123: Missing values")

    def test_custom_message(self):
        with pytest.raises(AssertionError, match="custom msg"):
            assert_no_warnings("WARNING: Caution", msg="custom msg")


class TestAssertErrors:
    def test_expected_error_found(self, capsys):
        log = "ERROR: File WORK.MISSING.DATA does not exist."
        assert_errors(log, ["does not exist"])
        captured = capsys.readouterr()
        assert "Expected errors found" in captured.out

    def test_expected_error_not_found(self):
        log = "ERROR: Some other error."
        with pytest.raises(AssertionError, match="Expected error messages not found"):
            assert_errors(log, ["does not exist"])

    def test_no_errors_at_all(self):
        log = "NOTE: Clean."
        with pytest.raises(AssertionError, match="Expected 1 error"):
            assert_errors(log, ["something"])

    def test_multiple_expected_errors(self, capsys):
        log = "ERROR: First failure.\nERROR: Second failure."
        assert_errors(log, ["First failure", "Second failure"])
        captured = capsys.readouterr()
        assert "2 total" in captured.out

    def test_empty_expected_messages_passes_when_error_exists(self, capsys):
        assert_errors("ERROR: Failure", [])
        assert "Expected errors found" in capsys.readouterr().out

    def test_empty_expected_messages_fails_without_error(self):
        with pytest.raises(AssertionError, match="Expected 0 error"):
            assert_errors("NOTE: Clean", [])

    def test_custom_message_is_used_for_missing_error(self):
        with pytest.raises(AssertionError, match="custom error message"):
            assert_errors("ERROR: Other failure", ["Expected"], msg="custom error message")

    def test_multiline_log_checks_each_error_line(self):
        log = "NOTE: Start\nERROR: First failure\nNOTE: Continued processing\nERROR: Second failure"
        assert_errors(log, ["First failure", "Second failure"])

    def test_numbered_sas_error_is_extracted(self):
        assert_errors("ERROR 180-322: Statement is not valid.", ["Statement is not valid"])

    def test_embedded_error_marker_is_not_extracted(self):
        with pytest.raises(AssertionError, match="found none"):
            assert_errors("NOTERROR: text", ["text"])


class TestAssertWarnings:
    def test_expected_warning_found(self, capsys):
        log = "WARNING: Low disk space."
        assert_warnings(log, ["Low disk space"])
        captured = capsys.readouterr()
        assert "Expected warnings found" in captured.out

    def test_expected_warning_not_found(self):
        log = "WARNING: Some other warning."
        with pytest.raises(AssertionError, match="Expected warning messages not found"):
            assert_warnings(log, ["Low disk space"])

    def test_no_warnings_at_all(self):
        log = "NOTE: Clean."
        with pytest.raises(AssertionError, match="Expected 1 warning"):
            assert_warnings(log, ["something"])

    def test_empty_expected_messages_passes_when_warning_exists(self, capsys):
        assert_warnings("WARNING: Caution", [])
        assert "Expected warnings found" in capsys.readouterr().out

    def test_empty_expected_messages_fails_without_warning(self):
        with pytest.raises(AssertionError, match="Expected 0 warning"):
            assert_warnings("NOTE: Clean", [])

    def test_custom_message_is_used_for_missing_warning(self):
        with pytest.raises(AssertionError, match="custom warning message"):
            assert_warnings("WARNING: Other caution", ["Expected"], msg="custom warning message")

    def test_case_insensitive_expected_message(self):
        assert_warnings("warning : Low disk space", ["LOW DISK SPACE"])

    def test_numbered_sas_warning_is_extracted(self):
        assert_warnings("WARNING 123: Missing values", ["Missing values"])

    def test_embedded_warning_marker_is_not_extracted(self):
        with pytest.raises(AssertionError, match="found none"):
            assert_warnings("NOTWARNING: text", ["text"])
