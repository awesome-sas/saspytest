# Release Testing With Live SAS

This maintainer guide explains how to build the `saspytest` package locally,
transfer it to a server with a live SAS connection, and run the package's
live-SAS verification suite there. It is separate from the user guide for
writing tests for your own SAS programs.

## Overview

`saspytest` is pure Python and does not contain compiled extensions. This means a wheel built on one machine will run on any other machine with a compatible Python version. The target server must have a working **saspy configuration** that can connect to SAS; Java is also required for IOM connections. See the [Support Policy](SUPPORT.md) for the 1.0 compatibility contract.

> **Note:** The package live-SAS tests require a live SAS session. CI cannot run
> them without a sanctioned SAS target, so the release process performs this
> gate externally before PyPI publication.

---

## Step 1: Build the Package Locally

From the repository root, build a wheel and source distribution:

```bash
python -m build --outdir dist/
```

The `build` and `twine` commands are included in the `dev` extra. Install them
with `pip install -e ".[dev]"` before building.

This produces:

```
dist/
├── saspytest-<version>-py3-none-any.whl   # <-- binary wheel (preferred for install)
└── saspytest-<version>.tar.gz             # <-- source distribution
```

> **Note for dev-container users:** If you get `OSError: [Errno 18] Invalid cross-device link` or a `PermissionError` during the build, it means `/tmp` and your workspace are on different filesystems. Build to `/tmp` instead and copy the results afterward:
>
> ```bash
> python -m build --outdir /tmp/saspytest-dist
> cp /tmp/saspytest-dist/* dist/
> ```

### Verify the build

```bash
# Check the distribution metadata
python -m twine check dist/*

# Quick sanity check after installing the wheel
python -c "import saspytest; print(saspytest.__version__)"
```

---

## Step 2: Transfer to the Target Server

Copy the built artifacts and the test files to the server that has SAS access.

### Option A: `scp` / `rsync`

```bash
# Copy wheel only
scp dist/saspytest-<version>-py3-none-any.whl user@target-server:/tmp/

# Copy the test suite too (required to run tests). Create the destination first
# so the resulting layout is unambiguous.
ssh user@target-server "mkdir -p /tmp/saspytest-tests/tests"
scp pytest.ini user@target-server:/tmp/saspytest-tests/
scp -r tests/integration user@target-server:/tmp/saspytest-tests/tests/
```

### Option B: Shared storage / artifact repository

Upload the wheel to your organization's artifact store (Nexus, Artifactory, etc.) and download it on the target server.

---

## Step 3: Prepare the Target Server

### Prerequisites

| Requirement | Notes |
|---|---|
| Python | 3.11 or later |
| SAS connection | `saspy` must be configured to reach your SAS deployment |
| Java | Required if using IOM connections |

### Configure saspy

Choose **one** of the following methods:

#### Method 1: Environment variables

These environment variables are consumed by `saspytest` when it creates a
session through `saspytest.session.get_sas_session()`. They are not standard
`saspy` environment variables.

```bash
export SASPY_CONFIG=/path/to/sascfg.py
export SASPY_CFGNAME=oda   # or whatever your config name is
```

#### Method 2: `saspytest_config.py` (automatic discovery)

Place a `saspytest_config.py` in the directory where you run tests (or any parent directory).
`saspytest` searches the working directory and all parent directories for this file and, if found,
passes it to saspy automatically — no environment variables needed.

See the [saspy configuration docs](https://sassoftware.github.io/saspy/configuration.html) for the file format.

#### Method 3: Local SAS install

If SAS is installed locally, saspy often auto-detects the configuration.

### Verify the connection

If you are using `SASPY_CONFIG` and `SASPY_CFGNAME`, verify the connection
through `saspytest`, because plain `saspy.SASsession()` does not read those
environment variables:

```bash
python -c "from saspytest import get_sas_session; print(get_sas_session())"
```

If this opens a session without errors, you are ready.

If you want to validate `saspy` directly instead, pass the config explicitly:

```bash
python -c "import os, saspy; sas = saspy.SASsession(cfgfile=os.environ['SASPY_CONFIG'], cfgname=os.environ.get('SASPY_CFGNAME')); print(sas)"
```

---

## Step 4: Install the Package on the Target Server

### Install the wheel

```bash
pip install /tmp/saspytest-<version>-py3-none-any.whl
```

For the source-distribution check, install the `.tar.gz` artifact in a separate
clean environment as well. The wheel and source distribution must both install
successfully and expose the same `saspytest.__version__`.

```bash
python -m venv /tmp/saspytest-sdist-env
/tmp/saspytest-sdist-env/bin/python -m pip install /tmp/saspytest-<version>.tar.gz
```

### Install with dev dependencies (needed for tests)

```bash
pip install "/tmp/saspytest-<version>-py3-none-any.whl[dev]"
```

### Verify the installation

```bash
python -c "import saspytest; print('saspytest', saspytest.__version__)"
```

---

## Step 5: Run the Package Live-SAS Tests

### Option A: Run tests from a copied integration directory

If you copied the integration folder in Step 2:

```bash
cd /tmp/saspytest-tests
pytest tests/integration/ -v
```

### Option B: Clone the repository on the target server

The source distribution does **not** include `tests/`, so if you do not transfer
`tests/` directly you should clone the repository instead:

```bash
git clone https://github.com/awesome-sas/saspytest.git
cd saspytest
pip install -e ".[dev]"
pytest tests/integration/ -v
```

### Run the full test suite (unit + integration + examples)

```bash
python scripts/run_tests.py
```

The live-SAS suites fail during fixture setup when the SAS connection is
unavailable. Do not treat a run that omits or deselects those suites as a
release gate.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'saspytest'` | Package not installed | Re-run `pip install` on the wheel |
| `get_sas_session()` or `saspy.SASsession(...)` hangs or fails | SAS connection not configured | Check `SASPY_CONFIG` and `SASPY_CFGNAME` for `saspytest`, or check your direct `saspy` configuration such as `sascfg_personal.py` |
| Integration tests fail during fixture setup | No live SAS session available | Verify `get_sas_session()` works before running tests, or call `saspy.SASsession(cfgfile=..., cfgname=...)` directly |
| `FileNotFoundError` for `.sas` files in tests | Relative paths broken by working directory | Run pytest from the repo root (e.g., `cd saspytest && pytest tests/`) |

---

## Security Reminders

- **Never commit SAS credentials or proprietary JAR files** to this repository.
- Transfer wheels and test files over secure channels (`scp`, VPN, encrypted shares).
- If using environment variables for SAS configuration, ensure they are not logged in shell history (`export HISTCONTROL=ignoreboth`).
