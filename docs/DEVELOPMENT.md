# Development Guide

## Project Layout

This repository uses the modern Python `src/` layout:

```
src/
  saspytest/        # Package source code
    __init__.py
    session.py
    logs.py
    macros.py
    datasets.py
    files.py
tests/
  unit/             # Internal mock-based tests for saspytest
  integration/      # Package tests requiring a live SAS connection
docs/               # Documentation
scripts/
  check_code.py     # Code quality runner (Black + Flake8 + Pylint)
  run_tests.py      # Internal, live-SAS, and example-suite runner
.github/workflows/  # CI, TestPyPI, and PyPI release workflows
README.md           # GitHub landing page
pyproject.toml      # Modern Python project configuration
pytest.ini          # pytest configuration
```

---

## Setting Up a Development Environment

### Local Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Running Tests

### Internal Unit Tests (no SAS required)

These tests use mocks to verify saspytest's Python implementation. They are
maintainer tests and are not the normal way to test a SAS program.

```bash
pytest -c pytest.ini
```

### Package Live-SAS Tests (requires SAS)

These tests verify saspytest against a live SAS connection via saspy. They are
not run in normal CI because no public SAS server is available.

```bash
# Run only package live-SAS tests
pytest tests/integration/ -v

# Run the full suite (requires a live SAS connection)
python scripts/run_tests.py
```

The root `pytest.ini` disables the `saspytest` plugin so the internal
mock-based suite can run without a live SAS session. The integration test
configuration explicitly loads the plugin.
Tests that request a live SAS session fail during fixture setup when no session
is available. Configure saspy before running the integration tests or examples.

---

## Configuring SAS Execution Environment for Package Live-SAS Tests

The package live-SAS tests require a working saspy configuration. Common approaches:

1. **Environment variables** (used by this codebase):
   ```bash
   export SASPY_CONFIG=/path/to/sascfg.py
   export SASPY_CFGNAME=oda
   ```

   These are read by `saspytest.session` and passed through to
   `saspy.SASsession(cfgfile=..., cfgname=...)`. Plain `saspy.SASsession()`
   does not read `SASPY_CONFIG` automatically.

2. **`saspytest_config.py` file discovery** — if no environment variables are set, `saspytest.session`
   searches the working directory and all parent directories for `saspytest_config.py` and passes it
   to saspy automatically (see [saspy docs](https://sassoftware.github.io/saspy/configuration.html#sascfg-personal-py-details) for the file format).

3. **Standard saspy auto-configuration** if you have a local SAS install.

> **Do not commit credentials or proprietary SAS JARs to the repository.**

---

## Code Style

The project uses `black` for formatting (100 character line length), `flake8`,
and `pylint` for linting.

Run all checks with the convenience script:

```bash
python scripts/check_code.py
```

Or individually:

```bash
black src/ tests/
flake8 src/ tests/
pylint src/ tests/ examples/
```

---

## Releasing to PyPI

The version in `pyproject.toml` is the single source of truth. The package
exposes that installed distribution version through `saspytest.__version__`.

1. Change `project.version` in `pyproject.toml` and update `CHANGELOG.md`
2. Install the development dependencies with `pip install -e ".[dev]"`
3. Run the internal tests and complete the code checks:

   ```bash
   pytest -c pytest.ini -v
   python scripts/check_code.py
   ```

4. Build and validate the distributions:

   ```bash
   python -m build
   python -m twine check dist/*
   ```

5. Install both the wheel and source distribution in separate fresh virtual environments
   and run the internal SAS-free unit suite with `pytest -c pytest.ini -v`
6. Complete the external live-SAS release gate described in
   [Release Testing](RELEASE_TESTING.md), using
   `python scripts/run_tests.py`
7. Create and publish the GitHub release. The release workflow validates the
   tag, changelog, package build, and unit tests before publishing to PyPI.

The TestPyPI workflow is available through GitHub Actions for a final package
installation check before the production release. Do not create a release tag
or upload an artifact until the validation steps have passed.

---

## Important: Proprietary SAS Components

- **SAS JARs** (`sastpj.rutil.jar`, `sas.rutil.jar`, etc.) are proprietary and **must never** be committed to this repository or included in distributions.
- Users are responsible for obtaining and configuring their own SAS deployment.
