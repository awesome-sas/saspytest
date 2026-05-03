"""Validation for conventional SAS identifiers used by the public helpers."""

import re

_SAS_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_sas_identifier(value: str, label: str, max_length: int = 32) -> str:
    """Validate and return a conventional V7-compatible SAS identifier."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty SAS identifier")
    if len(value) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters")
    if _SAS_IDENTIFIER.fullmatch(value) is None:
        raise ValueError(
            f"{label} identifier must start with a letter or underscore and contain only "
            "letters, digits, and underscores"
        )
    return value
