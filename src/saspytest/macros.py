"""
Macro variable assertions for SAS testing with saspy.

This module provides assertion functions for validating SAS macro variables.
"""

from typing import Optional
import saspy

from ._identifiers import validate_sas_identifier


def assert_macro_value(
    sas: saspy.SASsession, macro_name: str, expected_value: str, msg: Optional[str] = None
) -> None:
    """
    Assert that a SAS macro variable has the expected value.

    Args:
        sas: SAS session instance
        macro_name: Name of macro variable (without &)
        expected_value: Expected value
        msg: Optional custom error message

    Raises:
        AssertionError: If macro value doesn't match expected

    Example:
        >>> sas.symput("myvar", "test")
        >>> assert_macro_value(sas, "myvar", "test")
    """
    validate_sas_identifier(macro_name, "macro_name")
    actual_value = str(sas.symget(macro_name)).strip()
    expected_value = str(expected_value).strip()

    if msg is None:
        msg = f"Macro variable &{macro_name} expected '{expected_value}', got '{actual_value}'"

    assert actual_value == expected_value, msg


def assert_macro_exists(sas: saspy.SASsession, macro_name: str, msg: Optional[str] = None) -> None:
    """
    Assert that a SAS macro variable exists (is defined).

    Args:
        sas: SAS session instance
        macro_name: Name of macro variable (without &)
        msg: Optional custom error message

    Raises:
        AssertionError: If macro variable doesn't exist

    Example:
        >>> sas.symput("myvar", "value")
        >>> assert_macro_exists(sas, "myvar")
    """
    validate_sas_identifier(macro_name, "macro_name")
    value = sas.symget(macro_name)

    if msg is None:
        msg = f"Macro variable &{macro_name} should exist but was not found"

    assert value is not None and value != "", msg
