"""Unit tests for the shared SAS identifier validation boundary."""

import pytest

from saspytest._identifiers import validate_sas_identifier


def test_accepts_valid_identifier_at_maximum_length():
    value = "A" * 32
    assert validate_sas_identifier(value, "name") == value


@pytest.mark.parametrize("value", [None, "", "1name", "name-with-dash", "A" * 33])
def test_rejects_invalid_identifier_values(value):
    with pytest.raises(ValueError):
        validate_sas_identifier(value, "name")
