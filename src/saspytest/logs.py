"""
Log assertions for SAS testing with saspy.

This module provides assertion functions for validating SAS log contents.

IMPORTANT - Log Handling:
--------------------------
The saspy library maintains a cumulative log in the session object (_log attribute).
This log is NOT flushed between calls to saslog() - it continuously accumulates all
log messages from the entire session.

For proper log assertions:
1. Use submit() return value: result = sas.submit("..."); log = result['LOG']
2. The result['LOG'] contains ONLY the log for that specific submit() call
3. DO NOT use sas.saslog() for assertions - it returns the entire session history

Example (CORRECT):
    result = sas.submit("data test; x=1; run;")
    assert_no_errors(result['LOG'])  # Checks only this submit's log

Example (INCORRECT - will check entire session history):
    sas.submit("data test; x=1; run;")
    assert_no_errors(sas.saslog())  # BAD: Includes all previous submits!
"""

import re
from typing import Optional, List

_ERROR_MARKER = r"\bERROR(?:\s+\d+(?:-\d+)?)?\s*:"
_WARNING_MARKER = r"\bWARNING(?:\s+\d+(?:-\d+)?)?\s*:"


def assert_log_contains(
    log: str, pattern: str, regex: bool = False, msg: Optional[str] = None
) -> None:
    """
    Assert that the SAS log contains a specific pattern.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        pattern: String or regex pattern to search for
        regex: Whether pattern is a regular expression
        msg: Optional custom error message

    Raises:
        AssertionError: If pattern not found in log

    Example:
        >>> result = sas.submit("data test; x=1; run;")
        >>> assert_log_contains(result['LOG'], "DATA statement used")
    """
    if regex:
        found = re.search(pattern, log) is not None
    else:
        found = pattern in log

    if msg is None:
        msg = f"Pattern '{pattern}' not found in SAS log"

    assert found, msg


def assert_log_not_contains(
    log: str, pattern: str, regex: bool = False, msg: Optional[str] = None
) -> None:
    """
    Assert that the SAS log does NOT contain a specific pattern.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        pattern: String or regex pattern to search for
        regex: Whether pattern is a regular expression
        msg: Optional custom error message

    Raises:
        AssertionError: If pattern found in log

    Example:
        >>> result = sas.submit("data test; x=1; run;")
        >>> assert_log_not_contains(result['LOG'], "ERROR")
    """
    if regex:
        found = re.search(pattern, log) is not None
    else:
        found = pattern in log

    if msg is None:
        msg = f"Pattern '{pattern}' should not be in SAS log but was found"

    assert not found, msg


def assert_no_errors(log: str, msg: Optional[str] = None) -> None:
    """
    Assert that the SAS log contains no ERROR messages.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        msg: Optional custom error message

    Raises:
        AssertionError: If errors found in log

    Example:
        >>> result = sas.submit("data test; x=1; run;")
        >>> assert_no_errors(result['LOG'])
    """
    errors = re.findall(_ERROR_MARKER, log, re.IGNORECASE)

    if msg is None:
        msg = f"SAS log contains {len(errors)} ERROR(s)"

    assert len(errors) == 0, msg


def assert_no_warnings(log: str, msg: Optional[str] = None) -> None:
    """
    Assert that the SAS log contains no WARNING messages.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        msg: Optional custom error message

    Raises:
        AssertionError: If warnings found in log

    Example:
        >>> result = sas.submit("data test; x=1; run;")
        >>> assert_no_warnings(result['LOG'])
    """
    found_warnings = re.findall(_WARNING_MARKER, log, re.IGNORECASE)

    if msg is None:
        msg = f"SAS log contains {len(found_warnings)} WARNING(s)"

    assert len(found_warnings) == 0, msg


def assert_errors(log: str, expected_messages: List[str], msg: Optional[str] = None) -> None:
    """
    Assert that the SAS log contains expected ERROR messages.

    Use this when testing error conditions to verify specific errors occur.

    Note: This function cannot suppress the UserWarning from saspy.submit()
    itself, as that warning is emitted during submit execution. To suppress it,
    use pytest.mark.filterwarnings or warnings.filterwarnings in the test.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        expected_messages: List of expected error message substrings
        msg: Optional custom error message

    Raises:
        AssertionError: If expected errors not found

    Example:
        >>> import warnings
        >>> with warnings.catch_warnings():
        ...     warnings.filterwarnings("ignore", category=UserWarning)
        ...     result = sas.submit("data test; set nonexistent; run;")
        >>> assert_errors(result['LOG'], ["File WORK.NONEXISTENT.DATA does not exist"])
    """
    error_pattern = rf"{_ERROR_MARKER}[^\n]*"
    found_errors = re.findall(error_pattern, log, re.IGNORECASE)

    if len(found_errors) == 0:
        if msg is None:
            msg = f"Expected {len(expected_messages)} error(s) but found none"
        assert False, msg

    # Check that each expected message appears in at least one error
    missing_messages = []
    for expected in expected_messages:
        found = any(expected.lower() in error.lower() for error in found_errors)
        if not found:
            missing_messages.append(expected)

    if missing_messages:
        if msg is None:
            msg = (
                f"Expected error messages not found: {missing_messages}\n"
                f"Found errors: {found_errors}"
            )
        assert False, msg

    # Print errors for visibility in pytest output
    print(f"\nExpected errors found ({len(found_errors)} total):")
    for error in found_errors:
        print(f"  - {error.strip()}")


def assert_warnings(log: str, expected_messages: List[str], msg: Optional[str] = None) -> None:
    """
    Assert that the SAS log contains expected WARNING messages.

    Use this when testing warning conditions to verify specific warnings occur.

    Args:
        log: SAS log text (typically from submit() result['LOG'])
        expected_messages: List of expected warning message substrings
        msg: Optional custom error message

    Raises:
        AssertionError: If expected warnings not found

    Example:
        >>> result = sas.submit("...code that generates warning...")
        >>> assert_warnings(result['LOG'], ["Missing values detected"])
    """
    warning_pattern = rf"{_WARNING_MARKER}[^\n]*"
    found_warnings = re.findall(warning_pattern, log, re.IGNORECASE)

    if len(found_warnings) == 0:
        if msg is None:
            msg = f"Expected {len(expected_messages)} warning(s) but found none"
        assert False, msg

    # Check that each expected message appears in at least one warning
    missing_messages = []
    for expected in expected_messages:
        found = any(expected.lower() in warning.lower() for warning in found_warnings)
        if not found:
            missing_messages.append(expected)

    if missing_messages:
        if msg is None:
            msg = (
                f"Expected warning messages not found: {missing_messages}\n"
                f"Found warnings: {found_warnings}"
            )
        assert False, msg

    # Print warnings for visibility in pytest output
    print(f"\nExpected warnings found ({len(found_warnings)} total):")
    for warning in found_warnings:
        print(f"  - {warning.strip()}")
