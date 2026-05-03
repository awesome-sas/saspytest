"""
Unit tests for macro variable assertion functions.
"""

import pytest

from saspytest.macros import assert_macro_value, assert_macro_exists


class TestAssertMacroValue:
    def test_equal_values(self, mock_sas):
        mock_sas.symget.return_value = "expected"
        assert_macro_value(mock_sas, "myvar", "expected")
        mock_sas.symget.assert_called_once_with("myvar")

    def test_strip_whitespace(self, mock_sas):
        mock_sas.symget.return_value = "  value  "
        assert_macro_value(mock_sas, "myvar", "value")

    def test_unequal_values(self, mock_sas):
        mock_sas.symget.return_value = "actual"
        with pytest.raises(AssertionError, match="myvar"):
            assert_macro_value(mock_sas, "myvar", "expected")

    def test_custom_message(self, mock_sas):
        mock_sas.symget.return_value = "x"
        with pytest.raises(AssertionError, match="custom"):
            assert_macro_value(mock_sas, "v", "y", msg="custom")

    def test_undefined_value_is_compared_as_none(self, mock_sas):
        mock_sas.symget.return_value = None
        assert_macro_value(mock_sas, "missing", "None")

    def test_rejects_invalid_macro_name(self, mock_sas):
        with pytest.raises(ValueError, match="macro_name"):
            assert_macro_value(mock_sas, "&myvar", "value")

        mock_sas.symget.assert_not_called()


class TestAssertMacroExists:
    def test_exists(self, mock_sas):
        mock_sas.symget.return_value = "value"
        assert_macro_exists(mock_sas, "myvar")

    def test_none_value(self, mock_sas):
        mock_sas.symget.return_value = None
        with pytest.raises(AssertionError, match="myvar"):
            assert_macro_exists(mock_sas, "myvar")

    def test_empty_string(self, mock_sas):
        mock_sas.symget.return_value = ""
        with pytest.raises(AssertionError, match="myvar"):
            assert_macro_exists(mock_sas, "myvar")

    def test_whitespace_only(self, mock_sas):
        mock_sas.symget.return_value = "   "
        # After strip in assert_macro_value it would be empty,
        # but assert_macro_exists checks raw value before strip.
        # Current implementation: value is not None and value != ''
        # So whitespace-only passes.
        assert_macro_exists(mock_sas, "myvar")

    def test_rejects_invalid_macro_name(self, mock_sas):
        with pytest.raises(ValueError, match="macro_name"):
            assert_macro_exists(mock_sas, "my-var")

        mock_sas.symget.assert_not_called()

    def test_custom_message(self, mock_sas):
        mock_sas.symget.return_value = None
        with pytest.raises(AssertionError, match="custom"):
            assert_macro_exists(mock_sas, "missing", msg="custom")
