"""
Test suite for SAS integration using the saspytest package.

This module demonstrates how to use the saspytest package for testing
SAS programs with pytest. All helper functions and assertions have been
extracted to the saspytest package.

For documentation on SAS error and warning handling, see the saspytest package
documentation and ``docs/DEVELOPMENT_GUIDELINES.md``.
"""

import os
import tempfile
import pytest

# Import all helpers from the saspytest package
from saspytest import (
    # Session management
    get_sas_session,
    # Note: pytest fixtures (sas_session, clean_sas_workspace,
    # require_new_sas_session) are provided via conftest.py so they should
    # NOT be imported here. Import only functions intended for direct use.
    reset_sas_session,
    # File handling
    upload_file,
    download_file,
    # Macro assertions
    assert_macro_value,
    assert_macro_exists,
    # Log assertions
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    assert_no_warnings,
    assert_errors,
    assert_warnings,
    # Dataset assertions
    assert_dataset_exists,
    assert_library_exists,
    assert_record_count,
    assert_columns_exist,
    assert_datasets_equal,
    get_dataset_as_df,
)

pytestmark = pytest.mark.integration

# ==============================================================================
# Example Test Cases
# ==============================================================================


def test_macro_variables(sas_session):
    """Example: Testing macro variable operations."""
    sas = sas_session

    # Set macro variable from Python
    sas.symput("SASPYTEST_TESTVAR", "Hello World")

    # Assert macro has expected value
    assert_macro_value(sas, "SASPYTEST_TESTVAR", "Hello World")

    # Assert macro exists
    assert_macro_exists(sas, "SASPYTEST_TESTVAR")

    # Use macro in SAS code
    sas.submit("""
        %put NOTE: Test variable = &SASPYTEST_TESTVAR;
        %let SASPYTEST_COMPUTED = %upcase(&SASPYTEST_TESTVAR);
    """)

    # Verify computed macro
    assert_macro_value(sas, "SASPYTEST_COMPUTED", "HELLO WORLD")


def test_dataset_creation_and_validation(sas_session):
    """Example: Testing dataset creation and properties."""
    sas = sas_session

    # Create a test dataset
    result = sas.submit("""
        data SASPYTEST_MYTEST;
            do id = 1 to 10;
                name = cats('Person', id);
                age = 20 + mod(id, 5) * 10;
                output;
            end;
        run;
    """)

    # Verify no errors occurred
    assert_no_errors(result["LOG"])

    # Assert dataset exists
    assert_dataset_exists(sas, "SASPYTEST_MYTEST")

    # Assert correct number of records
    assert_record_count(sas, "SASPYTEST_MYTEST", 10)

    # Assert required columns exist
    assert_columns_exist(sas, "SASPYTEST_MYTEST", ["id", "name", "age"])

    # Get data as DataFrame for detailed checks
    df = get_dataset_as_df(sas, "SASPYTEST_MYTEST")
    assert df["id"].min() == 1
    assert df["id"].max() == 10


def test_dataset_comparison(sas_session):
    """Example: Comparing two datasets for equality."""
    sas = sas_session

    # Create two identical datasets
    result = sas.submit("""
        data SASPYTEST_ORIGINAL;
            input x y z;
            datalines;
        1 2 3
        4 5 6
        7 8 9
        ;
        run;

        data SASPYTEST_COPY;
            set SASPYTEST_ORIGINAL;
        run;
    """)

    assert_no_errors(result["LOG"])

    # Assert datasets are equal
    assert_datasets_equal(sas, "SASPYTEST_ORIGINAL", "SASPYTEST_COPY")

    # Modify the copy
    sas.submit("""
        data SASPYTEST_COPY;
            set SASPYTEST_COPY;
            z = z * 2;
        run;
    """)

    # Now they should be different (this will raise AssertionError)
    try:
        assert_datasets_equal(sas, "SASPYTEST_ORIGINAL", "SASPYTEST_COPY")
        assert False, "Should have raised AssertionError"
    except AssertionError as e:
        # Expected - datasets are different
        assert "not equal" in str(e)


def test_log_content_validation(sas_session):
    """Example: Validating SAS log contents with proper NOTE messages."""
    sas = sas_session

    # Run code that generates specific log messages
    result = sas.submit("""
        %put NOTE: Custom message - Test passed;

        data SASPYTEST_VALIDATION;
            set sashelp.class;
        run;
    """)

    # Check for expected log content
    assert_log_contains(result["LOG"], "Custom message - Test passed")
    assert_log_contains(result["LOG"], "NOTE:", regex=False)

    # Verify no errors or warnings
    assert_no_errors(result["LOG"])
    assert_no_warnings(result["LOG"])


def test_library_operations(sas_session):
    """Example: Testing library existence."""
    sas = sas_session

    # WORK library always exists
    assert_library_exists(sas, "WORK")

    # SASHELP library typically exists
    assert_library_exists(sas, "SASHELP")


def test_file_upload_download(sas_session):
    """Example: Testing file upload and download operations."""
    sas = sas_session

    # Create a temporary local file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        local_file = f.name
        f.write("Test content for upload\n")
        f.write("Line 2\n")

    try:
        # Upload to SAS server
        remote_file = "/tmp/SASPYTEST_UPLOAD.txt"
        success = upload_file(sas, local_file, remote_file)
        assert success, "Upload failed"

        # Verify file exists on server by reading it
        result = sas.submit(f"""
            data _null_;
                infile "{remote_file}";
                input;
                put _infile_;
            run;
        """)

        assert_no_errors(result["LOG"])
        assert_log_contains(result["LOG"], "Test content for upload")

        # Download the file back
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            download_file_path = f.name

        success = download_file(sas, download_file_path, remote_file)
        assert success, "Download failed"

        # Verify downloaded content
        with open(download_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Test content for upload" in content

        # Cleanup
        os.remove(download_file_path)

    finally:
        # Cleanup local file
        if os.path.exists(local_file):
            os.remove(local_file)


def test_complex_data_processing(sas_session):
    """Example: Complex multi-step data processing with validation."""
    sas = sas_session

    # Step 1: Create initial dataset
    result = sas.submit("""
        data SASPYTEST_CUSTOMERS;
            input customer_id name $ balance;
            datalines;
        101 Alice 1500
        102 Bob 2300
        103 Charlie 800
        104 Diana 3200
        105 Edward 1100
        ;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_CUSTOMERS")
    assert_record_count(sas, "SASPYTEST_CUSTOMERS", 5)

    # Step 2: Process data
    result = sas.submit("""
        data SASPYTEST_HIGH_BALANCE SASPYTEST_LOW_BALANCE;
            set SASPYTEST_CUSTOMERS;
            if balance >= 1500 then output SASPYTEST_HIGH_BALANCE;
            else output SASPYTEST_LOW_BALANCE;
        run;
    """)

    assert_no_errors(result["LOG"])

    # Step 3: Validate results
    assert_dataset_exists(sas, "SASPYTEST_HIGH_BALANCE")
    assert_dataset_exists(sas, "SASPYTEST_LOW_BALANCE")

    # Check record counts
    assert_record_count(sas, "SASPYTEST_HIGH_BALANCE", 3)  # Alice, Bob, Diana
    assert_record_count(sas, "SASPYTEST_LOW_BALANCE", 2)  # Charlie, Edward

    # Step 4: Verify data using pandas
    df_high = get_dataset_as_df(sas, "SASPYTEST_HIGH_BALANCE")
    df_low = get_dataset_as_df(sas, "SASPYTEST_LOW_BALANCE")

    assert all(df_high["balance"] >= 1500)
    assert all(df_low["balance"] < 1500)
    assert len(df_high) + len(df_low) == 5  # Total records preserved


def test_error_handling(sas_session):
    """Example: Testing error detection in SAS code."""
    sas = sas_session

    # Intentionally cause an error
    result = sas.submit("""
        data SASPYTEST_TEST;
            set nonexistent_dataset;
        run;
    """)

    # This should detect the error
    try:
        assert_no_errors(result["LOG"])
        assert False, "Should have detected ERROR in log"
    except AssertionError as e:
        # Expected - error was detected
        assert "ERROR" in str(e)


def test_expected_error_detection(sas_session):
    """Test: Verify we can detect when errors ARE expected and present."""
    sas = sas_session

    # Create code that will generate an ERROR
    result = sas.submit("""
        data _null_;
            /* This will cause an error - invalid syntax */
            x = 1 / 0;  /* Division by zero in some contexts */
        run;

        /* Try to use nonexistent dataset - guaranteed error */
        proc print data=this_dataset_does_not_exist_12345;
        run;
    """)

    # Use new assert_errors to verify expected errors
    assert_errors(result["LOG"], ["this_dataset_does_not_exist_12345"])


def test_expected_warning_detection(sas_session):
    """Test: Verify we can detect when warnings ARE expected and present."""
    sas = sas_session

    # Create code that will generate a WARNING
    result = sas.submit("""
        %put %STR(WAR)NING: This is a test warning message;
    """)

    # Use new assert_warnings to verify expected warning
    assert_warnings(result["LOG"], ["test warning message"])


def test_log_isolation_regression(sas_session):
    """
    REGRESSION TEST: Verify that submit() returns isolated logs.

    This test verifies the fix for the log handling issue where assertions
    were incorrectly using saslog() which returns cumulative session history
    instead of using submit()['LOG'] which returns isolated logs.

    The test ensures that:
    1. Each submit() returns only its own log in result['LOG']
    2. Errors in one submission don't contaminate assertions on later submissions
    3. The isolated log approach prevents false positives
    """
    sas = sas_session

    # Submit 1: Clean code
    result1 = sas.submit("""
        data SASPYTEST_CLEAN1;
            x = 1;
        run;
    """)

    # Verify submit 1 has no errors
    assert_no_errors(result1["LOG"])
    assert_log_contains(result1["LOG"], "SASPYTEST_CLEAN1")
    # Should NOT contain code from other submits
    assert_log_not_contains(result1["LOG"], "SASPYTEST_INTENTIONAL_ERROR")
    assert_log_not_contains(result1["LOG"], "SASPYTEST_CLEAN2")

    # Submit 2: Code with ERROR
    result2 = sas.submit("""
        data SASPYTEST_INTENTIONAL_ERROR;
            set this_does_not_exist;
        run;
    """)

    # Verify submit 2 HAS errors
    assert_log_contains(result2["LOG"], "ERROR")
    assert_log_contains(result2["LOG"], "SASPYTEST_INTENTIONAL_ERROR")
    # Should NOT contain code from other submits
    assert_log_not_contains(result2["LOG"], "SASPYTEST_CLEAN1")
    assert_log_not_contains(result2["LOG"], "SASPYTEST_CLEAN2")

    # Submit 3: Clean code again
    result3 = sas.submit("""
        data SASPYTEST_CLEAN2;
            y = 2;
        run;
    """)

    # CRITICAL TEST: Verify submit 3's isolated log has NO errors
    # (even though submit 2 had errors in the session history)
    assert_no_errors(result3["LOG"])  # This is the regression test!
    assert_log_contains(result3["LOG"], "SASPYTEST_CLEAN2")
    # Should NOT contain errors or code from previous submits
    assert_log_not_contains(result3["LOG"], "ERROR")
    assert_log_not_contains(result3["LOG"], "SASPYTEST_INTENTIONAL_ERROR")
    assert_log_not_contains(result3["LOG"], "SASPYTEST_CLEAN1")

    # Verify that saslog() WOULD show all history (demonstrating the problem)
    full_log = sas.saslog()
    # Full log should contain ALL submissions
    assert "SASPYTEST_CLEAN1" in full_log
    assert "SASPYTEST_INTENTIONAL_ERROR" in full_log
    assert "SASPYTEST_CLEAN2" in full_log

    # This demonstrates why using saslog() for assertions is wrong:
    # If we checked saslog() after submit 3, we'd incorrectly detect
    # the error from submit 2
    assert "ERROR" in full_log  # Error from submit 2 is in full history

    print("\n✓ REGRESSION TEST PASSED:")
    print("  - Isolated logs contain only their own submission")
    print("  - Errors don't leak between isolated logs")
    print(f"  - Submit 1 log length: {len(result1['LOG'])}")
    print(f"  - Submit 2 log length: {len(result2['LOG'])}")
    print(f"  - Submit 3 log length: {len(result3['LOG'])}")
    print(f"  - Full session log length: {len(full_log)}")


def test_warning_vs_error_distinction(sas_session):
    """Test: Verify we can distinguish between warnings and errors."""
    sas = sas_session

    # Code with only WARNING (no ERROR)
    result_warn = sas.submit("""
        %put %STR(WAR)NING: Test warning for distinction test;
    """)

    # Should have warning but no error
    assert_log_contains(result_warn["LOG"], "WARNING")
    assert_log_not_contains(result_warn["LOG"], "ERROR")
    assert_no_errors(result_warn["LOG"])  # Should pass - no errors

    try:
        assert_no_warnings(result_warn["LOG"])
        assert False, "Should have detected warning"
    except AssertionError:
        pass  # Expected

    # Code with ERROR (may also have warnings)
    result_error = sas.submit("""
        proc print data=nonexistent;
        run;
    """)

    # Should have error
    assert_log_contains(result_error["LOG"], "ERROR")

    try:
        assert_no_errors(result_error["LOG"])
        assert False, "Should have detected error"
    except AssertionError:
        pass  # Expected


def test_proper_error_logging_with_syscc(sas_session):
    """
    Test: Demonstrate proper error logging following SAS guidelines.

    According to docs/DEVELOPMENT_GUIDELINES.md:
    - Use %PUT %STR(ERR)OR: for custom errors
    - Set SYSCC to 8 when issuing an error
    """
    sas = sas_session

    # Example: Proper error handling in a validation macro
    result = sas.submit("""
        %macro SASPYTEST_VALIDATE_DATA(dataset=);
            /* Check if dataset parameter provided */
            %if &dataset= %then %do;
                %put %STR(ERR)OR: DATASET parameter is required;
                %let syscc = %sysfunc(max(&syscc,8));
                %return;
            %end;

            /* Check if dataset exists */
            %if not %sysfunc(exist(&dataset)) %then %do;
                %put %STR(ERR)OR: Dataset &dataset does not exist;
                %let syscc = %sysfunc(max(&syscc,8));
                %return;
            %end;

            %put NOTE: Dataset &dataset validated successfully;
        %mend SASPYTEST_VALIDATE_DATA;

        /* Test with missing parameter - should log error and set SYSCC */
        %SASPYTEST_VALIDATE_DATA(dataset=);
    """)

    # Verify error message appears in log
    assert_log_contains(result["LOG"], "ERROR: DATASET parameter is required")

    # Verify SYSCC was set to 8
    syscc_value = int(sas.symget("syscc") or "0")
    assert syscc_value >= 8, f"SYSCC should be >= 8 for errors, got {syscc_value}"


def test_proper_warning_logging_with_syscc(sas_session):
    """
    Test: Demonstrate proper warning logging following SAS guidelines.

    According to docs/DEVELOPMENT_GUIDELINES.md:
    - Use %PUT %STR(WAR)NING: for custom warnings
    - Set SYSCC to 4 when issuing a warning (if less than 4)
    """
    sas = sas_session

    # Reset SYSCC first
    sas.submit("%let syscc = 0;")

    # Example: Proper warning handling in a data quality check
    result = sas.submit("""
        %macro SASPYTEST_CHECK_DATA_QUALITY(dataset=);
            /* Check for missing values */
            proc sql noprint;
                select count(*) into :SASPYTEST_MISSING_COUNT
                from &dataset
                where name is missing;
            quit;

            %if &SASPYTEST_MISSING_COUNT > 0 %then %do;
                %put %STR(WAR)NING: Found &SASPYTEST_MISSING_COUNT observations with missing names;
                %let syscc = %sysfunc(max(&syscc,4));
            %end;
            %else %do;
                %put NOTE: No missing values found;
            %end;
        %mend SASPYTEST_CHECK_DATA_QUALITY;

        /* Create test data with missing values */
        data SASPYTEST_TEST_MISSING;
            input name $ age;
            datalines;
        John 25
        . 30
        Jane 35
        ;
        run;

        /* Test warning - should log warning and set SYSCC to 4 */
        %SASPYTEST_CHECK_DATA_QUALITY(dataset=SASPYTEST_TEST_MISSING);
    """)

    # Verify warning message appears in log
    assert_log_contains(result["LOG"], "WARNING: Found")
    assert_log_contains(result["LOG"], "missing names")

    # Verify SYSCC was set to at least 4
    syscc_value = int(sas.symget("syscc") or "0")
    assert syscc_value >= 4, f"SYSCC should be >= 4 for warnings, got {syscc_value}"


def test_error_does_not_downgrade_syscc(sas_session):
    """
    Test: Verify that error handling properly uses max() to avoid downgrading SYSCC.

    According to docs/DEVELOPMENT_GUIDELINES.md:
    - Use %sysfunc(max(&syscc,8)) to ensure SYSCC is raised to 8 but not lowered
    """
    sas = sas_session

    # Set SYSCC to 12 (higher than typical error code)
    sas.submit("%let syscc = 12;")

    result = sas.submit("""
        /* This error handling should NOT reduce SYSCC from 12 to 8 */
        %put %STR(ERR)OR: Test error with existing high SYSCC;
        %let syscc = %sysfunc(max(&syscc,8));

        %put NOTE: SYSCC after error handling = &syscc;
    """)

    # Verify SYSCC stayed at 12 (not downgraded to 8)
    syscc_value = int(sas.symget("syscc") or "0")
    assert syscc_value == 12, f"SYSCC should remain 12, got {syscc_value}"

    assert_log_contains(result["LOG"], "ERROR: Test error")


def test_warning_does_not_downgrade_syscc(sas_session):
    """
    Test: Verify that warning handling properly uses max() to avoid downgrading SYSCC.

    According to docs/DEVELOPMENT_GUIDELINES.md:
    - Use %sysfunc(max(&syscc,4)) to ensure SYSCC is raised to 4 but not lowered
    """
    sas = sas_session

    # Set SYSCC to 8 (error level, higher than warning)
    sas.submit("%let syscc = 8;")

    result = sas.submit("""
        /* This warning handling should NOT reduce SYSCC from 8 to 4 */
        %put %STR(WAR)NING: Test warning with existing error SYSCC;
        %let syscc = %sysfunc(max(&syscc,4));

        %put NOTE: SYSCC after warning handling = &syscc;
    """)

    # Verify SYSCC stayed at 8 (not downgraded to 4)
    syscc_value = int(sas.symget("syscc") or "0")
    assert syscc_value == 8, f"SYSCC should remain 8, got {syscc_value}"

    assert_log_contains(result["LOG"], "WARNING: Test warning")


def test_require_new_session_fixture(require_new_sas_session):
    """Fixture should provide a brand-new SAS session without shared state."""
    sas = require_new_sas_session

    result = sas.submit("""
        data SASPYTEST_FRESH_SESSION_CHECK;
            x = 42;
        run;
        """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas, "SASPYTEST_FRESH_SESSION_CHECK")


def test_reset_sas_session_direct_usage():
    """
    reset_sas_session() should close and reopen the shared session.

    WARNING: This test directly manipulates the shared session. It's isolated
    at the end by forcing pytest to run tests serially (see pytest.ini).
    The session is reset at the end to restore normal state for other tests.
    """
    sas_initial = get_sas_session()

    # Capture identifying macro variables from the initial session
    host_initial = sas_initial.symget("SYSHOSTNAME") or ""
    pid_initial = sas_initial.symget("SYSPROCESSID") or ""

    try:
        # Reset the shared session and capture the same macros
        sas_new = reset_sas_session()

        host_new = sas_new.symget("SYSHOSTNAME") or ""
        pid_new = sas_new.symget("SYSPROCESSID") or ""

        # Ensure the combination of hostname and process id changed (unique session)
        assert (host_initial, pid_initial) != (
            host_new,
            pid_new,
        ), (
            "reset_sas_session() should create a new session "
            "(SYSHOSTNAME+SYSPROCESSID tuple must differ)"
        )

        # Verify we can run code in the new session
        result = sas_new.submit("""
            data SASPYTEST_DIRECT_RESET_CHECK;
                y = 7;
            run;
            """)

        assert_no_errors(result["LOG"])
        assert_dataset_exists(sas_new, "SASPYTEST_DIRECT_RESET_CHECK")

    finally:
        # Ensure we have a valid session for subsequent tests
        # (in case the test failed mid-execution)
        try:
            get_sas_session()
        except Exception:  # pylint: disable=broad-exception-caught
            reset_sas_session()


if __name__ == "__main__":
    # Run tests with pytest:
    #     pytest test_sas_integration.py -v
    #
    # Run specific test:
    #     pytest test_sas_integration.py::test_macro_variables -v
    #
    # Show output:
    #     pytest test_sas_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])
