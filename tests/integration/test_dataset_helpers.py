"""Live-SAS coverage for dataset assertions and workspace cleanup."""

import pytest

from saspytest import (
    assert_columns_exist,
    assert_dataset_exists,
    assert_dataset_not_exists,
    assert_datasets_equal,
    assert_library_exists,
    assert_record_count,
    get_dataset_as_df,
)
from saspytest.session import cleanup_test_artifacts

pytestmark = pytest.mark.integration


def test_dataset_existence_and_library_paths(sas_session):
    """Validate existing, missing, mixed-case, and unassigned SAS objects."""
    sas = sas_session
    result = sas.submit("""
        data SASPYTEST_MixedCase;
            length customer_id 8;
            customer_id = 1;
        run;
        """)
    assert "ERROR:" not in result["LOG"]

    assert_dataset_exists(sas, "saspytest_mixedcase")
    assert_dataset_not_exists(sas, "SASPYTEST_MISSING")
    assert_library_exists(sas, "WORK")

    with pytest.raises(AssertionError, match="should exist but was not found"):
        assert_dataset_exists(sas, "SASPYTEST_MISSING")

    with pytest.raises(AssertionError, match="should not exist"):
        assert_dataset_not_exists(sas, "SASPYTEST_MixedCase")

    with pytest.raises(AssertionError, match="was not assigned"):
        assert_library_exists(sas, "SASPYNO")

    with pytest.raises(ValueError, match="dataset.*identifier"):
        assert_dataset_exists(sas, "SASPYTEST-BAD")


def test_record_count_and_columns_cover_empty_and_missing_datasets(sas_session):
    """Validate zero-row datasets, column case handling, and failure paths."""
    sas = sas_session
    result = sas.submit("""
        data SASPYTEST_EMPTY;
            length CustomerID 8 FullName $20;
            stop;
        run;
        """)
    assert "ERROR:" not in result["LOG"]

    assert_record_count(sas, "SASPYTEST_EMPTY", 0)
    assert_columns_exist(sas, "saspytest_empty", ["customerid", "FULLNAME"])

    with pytest.raises(AssertionError, match="expected 1 observations, got 0"):
        assert_record_count(sas, "SASPYTEST_EMPTY", 1)

    with pytest.raises(AssertionError, match="was not found"):
        assert_record_count(sas, "SASPYTEST_MISSING", 0)

    with pytest.raises(AssertionError, match="missing columns"):
        assert_columns_exist(sas, "SASPYTEST_EMPTY", ["NOT_A_COLUMN"])


def test_dataset_comparison_covers_equal_unequal_and_cross_library_paths(sas_session):
    """Validate PROC COMPARE results for equal and unequal datasets."""
    sas = sas_session
    result = sas.submit("""
        data SASPYTEST_COMPARE(label="Student Data");
            set sashelp.class;
        run;

        data SASPYTEST_COMPARE_CHANGED;
            set SASPYTEST_COMPARE;
            age = age + 1;
        run;
        """)
    assert "ERROR:" not in result["LOG"]

    assert_datasets_equal(sas, "SASPYTEST_COMPARE", "CLASS", "WORK", "SASHELP")

    with pytest.raises(AssertionError, match=r"SYSINFO=\d+"):
        assert_datasets_equal(sas, "SASPYTEST_COMPARE", "SASPYTEST_COMPARE_CHANGED")

    with pytest.raises(AssertionError, match="was not found"):
        assert_datasets_equal(sas, "SASPYTEST_MISSING", "SASPYTEST_COMPARE")


def test_get_dataset_as_df_reads_empty_dataset(sas_session):
    """Validate DataFrame conversion for a valid zero-row dataset."""
    sas = sas_session
    sas.submit("""
        data SASPYTEST_DF_EMPTY;
            length value 8;
            stop;
        run;
        """)

    frame = get_dataset_as_df(sas, "SASPYTEST_DF_EMPTY")
    assert frame.empty
    assert list(frame.columns) == ["value"]

    with pytest.raises(Exception):  # saspy raises a connection-specific error for missing data.
        get_dataset_as_df(sas, "SASPYTEST_MISSING")


def test_cleanup_removes_prefixed_datasets_and_macro_variables(sas_session):
    """Validate the cleanup operation used by the autouse workspace fixture."""
    sas = sas_session
    sas.submit("""
        %let SASPYTEST_INTEGRATION_MACRO = present;
        data SASPYTEST_INTEGRATION_DATA;
            value = 1;
        run;
        """)
    assert_dataset_exists(sas, "SASPYTEST_INTEGRATION_DATA")
    assert sas.symget("SASPYTEST_INTEGRATION_MACRO") == "present"

    cleanup_test_artifacts(sas)

    assert_dataset_not_exists(sas, "SASPYTEST_INTEGRATION_DATA")
    assert sas.symget("SASPYTEST_INTEGRATION_MACRO") in (None, "")
