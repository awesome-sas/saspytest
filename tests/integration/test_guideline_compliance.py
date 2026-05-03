"""
Test suite demonstrating compliance with DEVELOPMENT_GUIDELINES.md.

This module shows proper usage of:
- SASPYTEST_ prefix for datasets and macro variables
- Automatic cleanup via fixtures
- Proper error handling
- Test isolation and idempotency
"""

import pytest

from saspytest import (
    reset_test_state,
    assert_macro_value,
    assert_no_errors,
    assert_dataset_exists,
    assert_record_count,
    get_dataset_as_df,
    assert_errors,
    assert_warnings,
)

pytestmark = pytest.mark.integration


def test_proper_dataset_naming(sas_session):
    """
    Demonstrates proper dataset naming with SASPYTEST_ prefix.

    This test shows:
    - Using SASPYTEST_ prefix for datasets
    - Automatic cleanup by fixture (no manual cleanup needed)
    """
    sas = sas_session

    # Create dataset with proper prefix
    result = sas.submit("""
        data SASPYTEST_CUSTOMERS;
            input id name $ balance;
            datalines;
        1 Alice 1500
        2 Bob 2300
        3 Charlie 800
        ;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_CUSTOMERS")
    assert_record_count(sas, "SASPYTEST_CUSTOMERS", 3)

    # No manual cleanup needed - fixture handles it!


def test_proper_macro_naming(sas_session):
    """
    Demonstrates proper macro variable naming with SASPYTEST_ prefix.

    This test shows:
    - Using SASPYTEST_ prefix for macro variables
    - Automatic cleanup by fixture
    """
    sas = sas_session

    # Create macro variable with proper prefix
    result = sas.submit("""
        %let SASPYTEST_STATUS = SUCCESS;
        %let SASPYTEST_COUNT = 42;

        %put NOTE: Status is &SASPYTEST_STATUS;
        %put NOTE: Count is &SASPYTEST_COUNT;
    """)

    assert_no_errors(result["LOG"])
    assert_macro_value(sas, "SASPYTEST_STATUS", "SUCCESS")
    assert_macro_value(sas, "SASPYTEST_COUNT", "42")

    # No manual cleanup needed - fixture handles it!


def test_idempotency_demonstration(sas_session):
    """
    Demonstrates test idempotency - can run multiple times with same result.

    This test will produce the same result regardless of:
    - Execution order
    - Previous test states
    - Number of times run
    """
    sas = sas_session

    # This test always starts clean due to fixture
    result = sas.submit("""
        data SASPYTEST_TEMP;
            x = 100;
            output;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_record_count(sas, "SASPYTEST_TEMP", 1)

    df = get_dataset_as_df(sas, "SASPYTEST_TEMP")
    assert df["x"].iloc[0] == 100


def test_multiple_prefixed_artifacts(sas_session):
    """
    Demonstrates creating multiple artifacts with proper prefixes.

    Shows that the fixture cleans up all SASPYTEST_* items.
    """
    sas = sas_session

    # Create multiple datasets and macro variables
    result = sas.submit("""
        data SASPYTEST_INPUT;
            input val;
            datalines;
        1
        2
        3
        ;
        run;

        data SASPYTEST_OUTPUT;
            set SASPYTEST_INPUT;
            val_squared = val ** 2;
        run;

        %let SASPYTEST_INPUT_COUNT = 3;
        %let SASPYTEST_OUTPUT_COUNT = 3;
    """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_INPUT")
    assert_dataset_exists(sas, "SASPYTEST_OUTPUT")
    assert_macro_value(sas, "SASPYTEST_INPUT_COUNT", "3")
    assert_macro_value(sas, "SASPYTEST_OUTPUT_COUNT", "3")

    # Verify computed values
    df = get_dataset_as_df(sas, "SASPYTEST_OUTPUT")
    assert df["val_squared"].tolist() == [1, 4, 9]

    # All artifacts automatically cleaned up after test


def test_manual_state_reset_mid_test(sas_session):
    """
    Demonstrates manual state reset during a test when needed.

    Sometimes you need to reset state mid-test to test multiple scenarios.
    """
    sas = sas_session

    # Scenario 1: Create some data
    result1 = sas.submit("""
        data SASPYTEST_SCENARIO1;
            x = 1;
        run;

        %let SASPYTEST_VAR1 = VALUE1;
    """)

    assert_no_errors(result1["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_SCENARIO1")
    assert_macro_value(sas, "SASPYTEST_VAR1", "VALUE1")

    # Manual reset for clean scenario 2
    reset_test_state(sas)

    # Scenario 2: Fresh state
    result2 = sas.submit("""
        data SASPYTEST_SCENARIO2;
            y = 2;
        run;

        %let SASPYTEST_VAR2 = VALUE2;
    """)

    assert_no_errors(result2["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_SCENARIO2")
    assert_macro_value(sas, "SASPYTEST_VAR2", "VALUE2")

    # Automatic cleanup at end


def test_syscc_behavior_understanding(sas_session):
    """
    Demonstrates understanding of SYSCC behavior.

    SYSCC is a read/write automatic macro variable. Once elevated, it may persist
    across submissions in the same session, even after successful operations
    complete, until a later condition changes it or the test resets it explicitly.
    """
    sas = sas_session

    # Run clean operations
    result = sas.submit("""
        data SASPYTEST_CLEAN;
            x = 1;
        run;

        %put NOTE: SYSCC after clean data step = &syscc;
    """)

    # Verify this specific submission had no errors
    assert_no_errors(result["LOG"])

    # Note: SYSCC may still be elevated from previous test errors
    # This demonstrates that SYSCC persists across submissions in the same session
    syscc_value = int(sas.symget("syscc"))

    # Document the behavior: SYSCC can remain elevated even after clean operations
    print(f"\nSYSCC after clean operation: {syscc_value}")
    print("  (May be elevated from previous errors in the session)")

    # What we CAN verify: This submission itself didn't add errors
    assert "data SASPYTEST_CLEAN" in result["LOG"]


def test_syscc_persists_until_explicit_reset(sas_session):
    """Verify SYSCC survives clean submissions and can be explicitly reset."""
    sas = sas_session

    sas.submit("%let SYSCC = 0;")
    sas.submit("%let SYSCC = 8;")

    result = sas.submit("%put NOTE: clean submission after explicit SYSCC elevation; ")
    assert_no_errors(result["LOG"])
    assert int(sas.symget("SYSCC") or "0") == 8

    reset_result = sas.submit("%let SYSCC = 0;")
    assert_no_errors(reset_result["LOG"])
    assert int(sas.symget("SYSCC") or "0") == 0


def test_error_handling_with_proper_syscc(sas_session):
    """
    Demonstrates proper error handling that sets SYSCC correctly.

    Shows how to generate custom errors following SAS guidelines.
    """
    sas = sas_session

    # Intentionally generate an error with proper SYSCC setting
    result = sas.submit("""
        %macro SASPYTEST_CHECK_INPUT(value);
            %if &value < 0 %then %do;
                %put %STR(ERR)OR: Value must be non-negative, got &value;
                %let syscc = %sysfunc(max(&syscc,8));
            %end;
        %mend SASPYTEST_CHECK_INPUT;

        %SASPYTEST_CHECK_INPUT(-5);
    """)

    # Verify expected error was generated
    assert_errors(result["LOG"], ["Value must be non-negative"])

    # Verify SYSCC was raised to 8 (error level)
    syscc_value = int(sas.symget("syscc"))
    assert syscc_value >= 8, f"SYSCC should be >= 8 after error, got {syscc_value}"


def test_warning_handling_with_proper_syscc(sas_session):
    """
    Demonstrates proper warning handling that sets SYSCC correctly.

    Shows how to generate custom warnings following SAS guidelines.
    """
    sas = sas_session

    # Generate a warning with proper SYSCC setting
    result = sas.submit("""
        %macro SASPYTEST_CHECK_RANGE(value);
            %if &value > 100 %then %do;
                %put %STR(WAR)NING: Value &value exceeds recommended maximum of 100;
                %let syscc = %sysfunc(max(&syscc,4));
            %end;
        %mend SASPYTEST_CHECK_RANGE;

        %SASPYTEST_CHECK_RANGE(150);
    """)

    # Verify expected warning was generated
    assert_warnings(result["LOG"], ["Value 150 exceeds recommended maximum"])

    # Verify SYSCC was raised to 4 (warning level)
    syscc_value = int(sas.symget("syscc"))
    assert syscc_value >= 4, f"SYSCC should be >= 4 after warning, got {syscc_value}"


@pytest.mark.parametrize("input_val,expected_output", [(1, 2), (5, 10), (10, 20), (100, 200)])
def test_parametrized_with_proper_naming(sas_session, input_val, expected_output):
    """
    Demonstrates parametrized tests with proper naming conventions.

    Each parametrized run is isolated and cleaned up automatically.
    """
    sas = sas_session

    result = sas.submit(f"""
        data SASPYTEST_PARAM;
            input_value = {input_val};
            output_value = input_value * 2;
        run;
    """)

    assert_no_errors(result["LOG"])

    df = get_dataset_as_df(sas, "SASPYTEST_PARAM")
    assert df["output_value"].iloc[0] == expected_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
