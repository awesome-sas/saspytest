"""Unit tests for the maintainer test-suite runner."""

from types import SimpleNamespace
from unittest.mock import patch

from scripts.run_tests import run_suite  # pylint: disable=import-error


def test_run_suite_rejects_skipped_only_suite():
    result = SimpleNamespace(
        returncode=0,
        stdout="================ 38 skipped in 0.1s ================\n",
        stderr="",
    )

    with patch("scripts.run_tests.subprocess.run", return_value=result):
        assert run_suite("Integration tests", ("tests/integration/",)) is False


def test_run_suite_accepts_suite_with_passing_test():
    result = SimpleNamespace(
        returncode=0,
        stdout="================ 1 passed, 2 skipped in 0.1s ================\n",
        stderr="",
    )

    with patch("scripts.run_tests.subprocess.run", return_value=result):
        assert run_suite("Example tests", ("examples/",)) is True


def test_run_suite_allows_skipped_only_optional_suite():
    result = SimpleNamespace(
        returncode=0,
        stdout="================ 3 skipped in 0.1s ================\n",
        stderr="",
    )

    with patch("scripts.run_tests.subprocess.run", return_value=result):
        assert run_suite("Example tests", ("examples/",), require_passing=False) is True
