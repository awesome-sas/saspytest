"""
Session management for SAS testing with saspy.

This module provides session setup and teardown utilities,
along with pytest fixtures for managing shared SAS sessions.
"""

import os
import pathlib
from typing import Optional, Tuple

import pytest
import saspy

# Module-level mutable container for the shared SAS session.
# Using a dict avoids "global" statements while still providing module-level state.
_session_container: dict[str, Optional[saspy.SASsession]] = {"session": None}


def get_sas_session() -> saspy.SASsession:
    """
    Get or create a shared SAS session.

    Returns:
        saspy.SASsession: Active SAS session instance

    Raises:
        RuntimeError: If session cannot be established
    """
    if _session_container["session"] is None:
        _session_container["session"] = _create_session()

    return _session_container["session"]


def close_sas_session() -> None:
    """Close the shared SAS session if it exists."""
    session = _session_container.get("session")
    try:
        if session is not None:
            session.endsas()
    finally:
        # Keep the container usable even when saspy reports a teardown error.
        _session_container["session"] = None


def reset_sas_session() -> saspy.SASsession:
    """
    Reset the shared SAS session by closing and recreating it.

    WARNING: This affects the global shared session used by all tests.
    Only use this when you specifically need to test session reset behavior.
    Consider using require_new_sas_session fixture instead for isolated sessions.
    """
    close_sas_session()
    return get_sas_session()


def create_new_sas_session() -> saspy.SASsession:
    """
    Create a new independent SAS session without affecting the shared session.

    This creates a completely separate session that won't interfere with
    the global _sas_session used by other tests.

    Returns:
        saspy.SASsession: New independent SAS session instance
    """
    return _create_session()


def _create_session() -> saspy.SASsession:
    cfgfile, cfgname = _resolve_config_source()
    if cfgfile or cfgname:
        kwargs = {}
        if cfgfile:
            kwargs["cfgfile"] = cfgfile
        if cfgname:
            kwargs["cfgname"] = cfgname
        return saspy.SASsession(**kwargs)
    return saspy.SASsession()


def _find_saspytest_config() -> Optional[str]:
    """Search the working directory and its parents for saspytest_config.py."""
    current = pathlib.Path.cwd()
    while True:
        candidate = current / "saspytest_config.py"
        if candidate.is_file():
            return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _resolve_config_source() -> Tuple[Optional[str], Optional[str]]:
    env_cfgfile = os.environ.get("SASPY_CONFIG")
    env_cfgname = os.environ.get("SASPY_CFGNAME")
    if env_cfgfile or env_cfgname:
        return env_cfgfile, env_cfgname

    discovered = _find_saspytest_config()
    if discovered:
        return discovered, None

    return None, None


def reset_test_state(sas: saspy.SASsession) -> None:
    """
    Reset SAS session state for test isolation.

    This function ensures each test starts with a clean slate by:
    - Deleting all SASPYTEST_* datasets from WORK library
    - Deleting all SASPYTEST_* macro variables

    Note: SYSCC (system completion code) is a read/write SAS automatic macro
    variable. This cleanup does not reset it; use ``%let SYSCC = 0;`` explicitly
    when a scenario requires a clean condition code.

    Args:
        sas: SAS session instance

    Example:
        >>> reset_test_state(sas)
        >>> # Now session is clean for test execution
    """
    sas.submit("""
        /* Prefix lists avoid creating global helper names during cleanup. */
        proc datasets library=work nolist nowarn;
            delete SASPYTEST_:
            ;
        quit;

        /* Generate %SYMDEL calls without introducing a global macro variable. */
        data _null_;
            set sashelp.vmacro;
            where scope='GLOBAL' and upcase(name) like 'SASPYTEST_%';
            call execute(catx(' ', '%nrstr(%symdel)', name, '/ nowarn;'));
        run;
    """)


def cleanup_test_artifacts(sas: saspy.SASsession) -> None:
    """
    Clean up test artifacts after test execution.

    This is an alias for reset_test_state() to provide semantic clarity
    when used in fixture teardown. Performs the same cleanup operations.

    Args:
        sas: SAS session instance

    Example:
        >>> cleanup_test_artifacts(sas)
    """
    reset_test_state(sas)


@pytest.fixture(scope="session")
def _sas_session_manager():
    """Ensure the shared SAS session is alive when a test requests it."""
    session = get_sas_session()
    print("\n=== SAS session established ===")
    yield session
    print("\n=== Closing SAS session ===")
    close_sas_session()


@pytest.fixture()
def sas_session(_sas_session_manager):
    """Function-scoped fixture that returns the shared SAS session."""
    return get_sas_session()


@pytest.fixture()
def require_new_sas_session():
    """
    Fixture that provides a brand-new isolated SAS session.

    This creates an independent session that does not affect the shared
    session used by other tests. The session is automatically closed
    after the test completes.
    """
    session = create_new_sas_session()
    try:
        reset_test_state(session)
        yield session
    finally:
        # Cleanup also runs when initial session setup fails.
        try:
            session.endsas()
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # Ignore errors during cleanup


@pytest.fixture(autouse=True)
def clean_sas_workspace(request):
    """
    Clean up SAS workspace before and after each test.

    This fixture automatically runs before and after each test to ensure
    test isolation and idempotency by:
    - Removing all SASPYTEST_* datasets
    - Removing all SASPYTEST_* macro variables

    Workspace artifacts do not leak between tests. SYSCC and SYSERR are session
    state and are not reset by this fixture.

    Note: Workspace cleanup does not reset SYSCC or SYSERR. Reset SYSCC explicitly
    with ``%let SYSCC = 0;`` when a test scenario requires it.
    """
    if "sas_session" not in request.fixturenames:
        yield
        return

    sas = request.getfixturevalue("sas_session")

    # Setup: Clean state before test
    reset_test_state(sas)

    yield

    # Teardown: Clean state after test
    cleanup_test_artifacts(sas)
