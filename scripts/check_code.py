#!/usr/bin/env python3
"""Check source code formatting and style with black and flake8."""

import subprocess
import sys


def run(cmd, description):
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        print(f"\n[FAIL] {description} failed!")
        return False
    print(f"\n[PASS] {description} passed!")
    return True


def main():
    all_passed = True
    python = sys.executable

    # Check formatting with black
    if not run([python, "-m", "black", "--check", "src", "tests"], "Black format check"):
        all_passed = False

    # Check style with flake8
    if not run([python, "-m", "flake8", "src", "tests"], "Flake8 style check"):
        all_passed = False

    # Check style with pylint
    if not run([python, "-m", "pylint", "src/", "tests/", "examples/"], "Pylint style check"):
        all_passed = False

    print(f"\n{'=' * 60}")
    if all_passed:
        print("All checks passed!")
        sys.exit(0)
    else:
        print("Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
