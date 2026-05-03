"""Shared pytest fixtures for the Roman numerals example."""

# pylint: disable=duplicate-code

from pathlib import Path, PurePosixPath

import pytest

from saspytest import assert_no_errors, upload_file
from saspytest.session import (  # noqa: F401
    close_sas_session,
    cleanup_test_artifacts,
    create_new_sas_session,
    get_sas_session,
    reset_test_state,
)

DEMO_ROOT = Path(__file__).resolve().parent.parent
MACRO_FILE = DEMO_ROOT / "macros" / "number_to_roman.sas"
INPUT_DATA_FILE = DEMO_ROOT / "testdata" / "saspytest_roman_input.sas7bdat"
EXPECTED_DATA_FILE = DEMO_ROOT / "testdata" / "saspytest_roman_expected.sas7bdat"


@pytest.fixture(scope="session", autouse=True)
def _sas_session_manager():
    """Ensure the shared SAS session exists, or skip the examples."""
    try:
        session = get_sas_session()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        pytest.skip(f"Example tests require a live SAS connection: {exc}")

    yield session
    close_sas_session()


@pytest.fixture()
def sas_session(_sas_session_manager):
    """Function-scoped fixture that returns the shared SAS session."""
    return get_sas_session()


@pytest.fixture()
def require_new_sas_session():
    """Create a new SAS session for a single example test."""
    session = create_new_sas_session()
    reset_test_state(session)
    yield session
    try:
        session.endsas()
    except Exception:  # pylint: disable=broad-exception-caught
        pass


@pytest.fixture(autouse=True)
def clean_sas_workspace():
    """Reset the shared SAS workspace before and after each example test."""
    sas = get_sas_session()

    reset_test_state(sas)

    yield

    cleanup_test_artifacts(get_sas_session())


@pytest.fixture
def roman_remote_root(request):
    """Create a writable remote demo tree so hardcoded relative paths resolve."""
    session = request.getfixturevalue("sas_session")

    result = session.submit("""
        data _null_;
            length workpath $512;
            workpath = pathname('WORK');
            rc = dlgcdir(workpath);
        run;

        filename cwd '.';
        %let SASPYTEST_REMOTE_CWD = %sysfunc(pathname(cwd));
        filename cwd clear;

        data _null_;
            length base child $512;

            base = symget('SASPYTEST_REMOTE_CWD');

            child = cats(base, '/examples');
            if fileexist(child) = 0 then rc = dcreate('examples', base);

            base = child;
            child = cats(base, '/roman_numerals');
            if fileexist(child) = 0 then rc = dcreate('roman_numerals', base);

            base = child;
            child = cats(base, '/macros');
            if fileexist(child) = 0 then rc = dcreate('macros', base);

            child = cats(base, '/testdata');
            if fileexist(child) = 0 then rc = dcreate('testdata', base);
        run;
        """)

    assert_no_errors(result["LOG"])

    return PurePosixPath(session.symget("SASPYTEST_REMOTE_CWD")) / "examples" / "roman_numerals"


@pytest.fixture
def _roman_assets(request):
    """Upload demo assets to the remote SAS environment."""
    session = request.getfixturevalue("sas_session")
    remote_root = request.getfixturevalue("roman_remote_root")

    remote_macro = remote_root / "macros" / "number_to_roman.sas"
    remote_input = remote_root / "testdata" / "saspytest_roman_input.sas7bdat"
    remote_expected = remote_root / "testdata" / "saspytest_roman_expected.sas7bdat"

    assert upload_file(session, str(MACRO_FILE), str(remote_macro))
    assert upload_file(session, str(INPUT_DATA_FILE), str(remote_input))
    assert upload_file(session, str(EXPECTED_DATA_FILE), str(remote_expected))

    return {
        "root": remote_root,
        "macro": remote_macro,
        "input": remote_input,
        "expected": remote_expected,
    }
