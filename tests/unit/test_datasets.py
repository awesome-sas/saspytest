"""
Unit tests for dataset assertion functions.
"""

import pytest

from saspytest.datasets import (
    assert_dataset_exists,
    assert_dataset_not_exists,
    assert_library_exists,
    assert_record_count,
    assert_columns_exist,
    assert_datasets_equal,
    get_dataset_as_df,
)


class TestAssertDatasetExists:
    def test_exists(self, mock_sas):
        mock_sas.symget.return_value = "1"
        assert_dataset_exists(mock_sas, "mydata")
        mock_sas.submit.assert_called_once()

    def test_not_exists(self, mock_sas):
        mock_sas.symget.return_value = "0"
        with pytest.raises(AssertionError, match="mydata"):
            assert_dataset_exists(mock_sas, "mydata")

    def test_missing_result_raises_actionable_error(self, mock_sas):
        mock_sas.symget.return_value = None
        with pytest.raises(AssertionError, match="did not produce"):
            assert_dataset_exists(mock_sas, "mydata")

    def test_custom_libref(self, mock_sas):
        mock_sas.symget.return_value = "1"
        assert_dataset_exists(mock_sas, "mydata", libref="USER")
        submitted = mock_sas.submit.call_args[0][0]
        assert "USER.mydata" in submitted

    def test_rejects_invalid_identifier(self, mock_sas):
        with pytest.raises(ValueError, match="dataset"):
            assert_dataset_exists(mock_sas, "data; drop _all_")

        mock_sas.submit.assert_not_called()

    def test_custom_message(self, mock_sas):
        mock_sas.symget.return_value = "0"
        with pytest.raises(AssertionError, match="custom"):
            assert_dataset_exists(mock_sas, "mydata", msg="custom")


class TestAssertDatasetNotExists:
    def test_not_exists(self, mock_sas):
        mock_sas.symget.return_value = "0"
        assert_dataset_not_exists(mock_sas, "missing")

    def test_exists_raises(self, mock_sas):
        mock_sas.symget.return_value = "1"
        with pytest.raises(AssertionError, match="should not exist"):
            assert_dataset_not_exists(mock_sas, "mydata")

    def test_missing_result_uses_custom_message(self, mock_sas):
        mock_sas.symget.return_value = None
        with pytest.raises(AssertionError, match="custom"):
            assert_dataset_not_exists(mock_sas, "mydata", msg="custom")


class TestAssertLibraryExists:
    def test_exists(self, mock_sas):
        mock_sas.symget.return_value = "0"
        assert_library_exists(mock_sas, "WORK")

    def test_not_exists(self, mock_sas):
        mock_sas.symget.return_value = "1"
        with pytest.raises(AssertionError, match="WORK"):
            assert_library_exists(mock_sas, "WORK")

    def test_missing_result_uses_custom_message(self, mock_sas):
        mock_sas.symget.return_value = None
        with pytest.raises(AssertionError, match="custom"):
            assert_library_exists(mock_sas, "WORK", msg="custom")


class TestAssertRecordCount:
    def test_correct_count(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "42"]
        assert_record_count(mock_sas, "mydata", 42)

    def test_incorrect_count(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "5"]
        with pytest.raises(AssertionError, match="expected 10 observations, got 5"):
            assert_record_count(mock_sas, "mydata", 10)

    def test_missing_dataset_does_not_default_to_zero(self, mock_sas):
        mock_sas.symget.side_effect = ["0"]
        with pytest.raises(AssertionError, match="was not found"):
            assert_record_count(mock_sas, "mydata", 0)

    def test_missing_count_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", None]
        with pytest.raises(AssertionError, match="did not produce"):
            assert_record_count(mock_sas, "mydata", 0)

    def test_invalid_count_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "not-a-count"]
        with pytest.raises(AssertionError, match="invalid record count"):
            assert_record_count(mock_sas, "mydata", 0)

    def test_custom_message(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "5"]
        with pytest.raises(AssertionError, match="custom"):
            assert_record_count(mock_sas, "mydata", 10, msg="custom")

    def test_uses_isolated_artifacts(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "42"]
        assert_record_count(mock_sas, "mydata", 42)

        submitted = mock_sas.submit.call_args[0][0]
        macro_names = [call.args[0] for call in mock_sas.symget.call_args_list]
        assert all(name.startswith("SASPYTEST_") for name in macro_names)
        assert len(macro_names) == len(set(macro_names))
        assert "SASPYTEST_" in submitted
        assert "%let nobs" not in submitted


class TestAssertColumnsExist:
    def test_all_exist(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "ID NAME AGE"]
        assert_columns_exist(mock_sas, "mydata", ["id", "name"])

    def test_missing_column(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "ID NAME"]
        with pytest.raises(AssertionError, match="missing columns"):
            assert_columns_exist(mock_sas, "mydata", ["id", "missing"])

    def test_case_insensitive(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "UPPERCASE"]
        assert_columns_exist(mock_sas, "mydata", ["uppercase"])

    def test_missing_dataset_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["0"]
        with pytest.raises(AssertionError, match="was not found"):
            assert_columns_exist(mock_sas, "mydata", ["id"])

    def test_missing_columns_result_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", None]
        with pytest.raises(AssertionError, match="did not produce"):
            assert_columns_exist(mock_sas, "mydata", ["id"])

    def test_uses_isolated_artifacts(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "ID NAME"]
        assert_columns_exist(mock_sas, "mydata", ["id"])

        submitted = mock_sas.submit.call_args[0][0]
        assert "SASPYTEST_" in submitted
        assert "out=_cols_" not in submitted
        assert "set _cols_" not in submitted

    def test_rejects_invalid_column_identifier(self, mock_sas):
        with pytest.raises(ValueError, match=r"columns\[0\]"):
            assert_columns_exist(mock_sas, "mydata", ["not valid"])

        mock_sas.submit.assert_not_called()

    def test_custom_message(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "ID"]
        with pytest.raises(AssertionError, match="custom"):
            assert_columns_exist(mock_sas, "mydata", ["missing"], msg="custom")


class TestAssertDatasetsEqual:
    def test_equal(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", "0"]
        assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_not_equal(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", "1"]
        with pytest.raises(AssertionError, match="not equal"):
            assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_missing_first_dataset_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["0", "1"]
        with pytest.raises(AssertionError, match="ds1.*was not found"):
            assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_missing_second_dataset_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "0"]
        with pytest.raises(AssertionError, match="ds2.*was not found"):
            assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_missing_sysinfo_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", None]
        with pytest.raises(AssertionError, match="did not produce"):
            assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_invalid_sysinfo_raises_actionable_error(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", "not-a-number"]
        with pytest.raises(AssertionError, match="invalid PROC COMPARE SYSINFO"):
            assert_datasets_equal(mock_sas, "ds1", "ds2")

    def test_custom_message(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", "1"]
        with pytest.raises(AssertionError, match="custom"):
            assert_datasets_equal(mock_sas, "ds1", "ds2", msg="custom")

    def test_uses_isolated_artifacts(self, mock_sas):
        mock_sas.symget.side_effect = ["1", "1", "0"]
        assert_datasets_equal(mock_sas, "ds1", "ds2")

        submitted = mock_sas.submit.call_args[0][0]
        assert "SASPYTEST_" in submitted
        assert "out=_diff_" not in submitted

    def test_rejects_invalid_library_identifier(self, mock_sas):
        with pytest.raises(ValueError, match="libref1"):
            assert_datasets_equal(mock_sas, "ds1", "ds2", libref1="TOO_LONG1")

        mock_sas.submit.assert_not_called()


class TestGetDatasetAsDf:
    def test_returns_dataframe(self, mock_sas):
        expected_df = {"col1": [1, 2]}
        mock_sas.sd2df.return_value = expected_df
        result = get_dataset_as_df(mock_sas, "mydata")
        assert result == expected_df
        mock_sas.sd2df.assert_called_once_with("mydata", "WORK")

    def test_custom_libref(self, mock_sas):
        mock_sas.sd2df.return_value = None
        get_dataset_as_df(mock_sas, "mydata", libref="USER")
        mock_sas.sd2df.assert_called_once_with("mydata", "USER")

    def test_rejects_invalid_dataset_identifier(self, mock_sas):
        with pytest.raises(ValueError, match="dataset"):
            get_dataset_as_df(mock_sas, "my.data")

        mock_sas.sd2df.assert_not_called()
