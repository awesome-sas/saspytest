#!/usr/bin/env python3
"""Run the unit, integration, and example test suites."""

from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_suite(name, pytest_args, require_passing=True):
    """Run one pytest suite and return whether it passed."""
    print(f"\n{'=' * 60}")
    print(f"Running: {name}")
    print(f"{'=' * 60}", flush=True)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", *pytest_args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        return False

    if not require_passing:
        return True

    # A skipped-only suite has exit code 0, but it did not validate anything.
    summary_has_passed = re.search(
        r"^=+\s+.*\b[1-9]\d*\s+passed\b.*=+$", result.stdout, re.MULTILINE
    )
    if summary_has_passed is None:
        print(f"{name} did not execute any passing tests.", file=sys.stderr)
        return False

    return True


def main():
    """Run all test suites and return a failing status if any suite fails."""
    suites = (
        ("Internal unit tests", ("-c", "pytest.ini", "-v")),
        ("Integration tests", ("tests/integration/", "-v")),
        (
            "Hello World example tests",
            ("-c", "examples/hello_world/pytest.ini", "examples/hello_world", "-v"),
            False,
        ),
        (
            "Roman Numerals example tests",
            ("-c", "examples/roman_numerals/pytest.ini", "examples/roman_numerals", "-v"),
            False,
        ),
        (
            "Hello World simple layout example tests",
            (
                "-c",
                "examples/hello_world_simple_layout/pytest.ini",
                "examples/hello_world_simple_layout",
                "-v",
            ),
            False,
        ),
    )
    all_passed = True

    for suite in suites:
        name, pytest_args, *options = suite
        require_passing = options[0] if options else True
        if not run_suite(name, pytest_args, require_passing=require_passing):
            all_passed = False

    print(f"\n{'=' * 60}")
    print("All test suites passed!" if all_passed else "Some test suites failed!")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
