"""Pytest configuration for integration tests."""

import pytest

pytest_plugins = ("saspytest.session",)


@pytest.fixture(scope="session", autouse=True)
def _sas_session_manager():
    """Ensure integration tests fail during setup when SAS is unavailable."""
    from saspytest.session import (  # pylint: disable=import-outside-toplevel
        close_sas_session,
        get_sas_session,
    )

    session = get_sas_session()
    yield session
    close_sas_session()
