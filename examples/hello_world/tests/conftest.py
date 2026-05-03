"""Shared fixtures for the Hello World example."""

# pylint: disable=duplicate-code

import pytest

from saspytest.session import (
    cleanup_test_artifacts,
    close_sas_session,
    get_sas_session,
    reset_test_state,
)


@pytest.fixture(scope="session", autouse=True)
def _sas_session_manager():
    """Skip the example suite when no live SAS connection is available."""
    try:
        session = get_sas_session()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        close_sas_session()
        pytest.skip(f"Example tests require a live SAS connection: {exc}")

    yield session
    close_sas_session()


@pytest.fixture()
def sas_session(_sas_session_manager):
    """Return the shared SAS session for one example test."""
    return get_sas_session()


@pytest.fixture(autouse=True)
def clean_sas_workspace(_sas_session_manager):
    """Reset prefixed SAS artifacts before and after each example test."""
    sas = get_sas_session()
    reset_test_state(sas)
    yield
    cleanup_test_artifacts(sas)
