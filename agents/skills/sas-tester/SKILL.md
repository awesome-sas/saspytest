---
name: sas-tester
description: Create, maintain, and run pytest-style integration tests for SAS code
---

# SAS Tester Skill — saspytest

Use this skill to create, maintain, and run pytest-style integration tests for SAS code using the `saspytest` library.

---

## 1. Package Overview

`saspytest` provides pytest fixtures and assertion helpers for testing SAS programs through the [saspy](https://sassoftware.github.io/saspy/) Python interface.

**Import convention:**
```python
from saspytest import (
    assert_no_errors,
    assert_no_warnings,
    assert_log_contains,
    assert_log_not_contains,
    assert_errors,
    assert_warnings,
    assert_dataset_exists,
    assert_dataset_not_exists,
    assert_record_count,
    assert_columns_exist,
    assert_datasets_equal,
    assert_library_exists,
    assert_macro_value,
    assert_macro_exists,
    get_dataset_as_df,
    submit_sas_file,
    upload_file,
    download_file,
)
```

---

## 2. Session Configuration

`saspytest` resolves the saspy connection in this order — stop as soon as one source provides config:

| Priority | Source | How it works |
|---|---|---|
| 1 | `SASPY_CONFIG` / `SASPY_CFGNAME` env vars | Passed as `cfgfile=` / `cfgname=` to `saspy.SASsession()`. Recommended for CI/CD. |
| 2 | `saspytest_config.py` auto-discovery | `saspytest` walks the working directory and every parent directory looking for a file named `saspytest_config.py`. The first one found is passed as `cfgfile=`. No env vars needed. |
| 3 | Default saspy resolution | Falls back to saspy's own config lookup (`sascfg_personal.py` in the saspy package directory, etc.). |

### Quick-start: `saspytest_config.py` drop-in

Place a `saspytest_config.py` in the directory where you invoke pytest (or in an
ancestor of that directory):

```
my-sas-project/
├── saspytest_config.py ← auto-discovered; no env vars needed
├── macros/
│   └── my_macro.sas
└── tests/
    └── test_my_macro.py
```

`saspytest_config.py` uses the same format as saspy's standard `sascfg_personal.py`:

```python
# saspytest_config.py
SAS_config_names = ["myserver"]
myserver = {
    "iomhost": "sas.example.com",
    "iomport": 8591,
    "encoding": "utf-8",
}
```

See the [saspy configuration docs](https://sassoftware.github.io/saspy/configuration.html) for all options.

### CI/CD via environment variables

```bash
export SASPY_CONFIG="/opt/sas/sascfg_personal.py"
export SASPY_CFGNAME="iomlinux"
pytest tests/ -v
```

### Verify the connection

```bash
python -c "from saspytest import get_sas_session; print(get_sas_session())"
```

> **Note:** `SASPY_CONFIG` / `SASPY_CFGNAME` are read by `saspytest.session`, not by plain `saspy.SASsession()`.

---

## 3. Project Layout

For simple projects, a SAS source file and its test should live in the same directory.
Recommended naming is `*_test.py` alongside the `.sas` file, for example:

```text
example.sas
example_test.py
```

This is the default pattern to use for single macros, single programs, or otherwise small SAS projects.
Use it when the test file can sit beside the `.sas` file in the same directory.

Do not use `*.test.py`. If you prefer a prefix style, `test_*.py` is also valid, but `*_test.py` is the recommended default for small projects.

For larger projects, keep SAS code grouped under source directories such as `macros/` and `programs/`, and place tests in a separate `tests/` tree as shown below.

```
<repo-root>/
├── <source-dir>/    # Reusable SAS macros (*.sas), often `macros/`
│   └── example_macro.sas
├── <program-dir>/   # Runnable SAS programs (*.sas), often `programs/`
│   └── example_program.sas
├── tests/
│   ├── <source-dir>/
│   │   └── example_macro_test.py
│   └── <program-dir>/
│       └── example_program_test.py
├── testdata/        # Binary SAS datasets (*.sas7bdat) needed by tests
```

### conftest.py (optional)

Most projects can use the shared `saspytest` fixtures directly when `saspy` is configured correctly. Add a `conftest.py` only when you need custom session lifecycle control or extra project-specific fixtures.

If you do need one, copy this pattern:

```python
"""Shared pytest fixtures for SAS tests."""

import pytest

from saspytest.session import (
    close_sas_session,
    cleanup_test_artifacts,
    create_new_sas_session,
    get_sas_session,
    reset_test_state,
)


@pytest.fixture(scope="session", autouse=True)
def _sas_session_manager():
    try:
        session = get_sas_session()
    except Exception as exc:
        pytest.skip(f"Tests require a live SAS connection: {exc}")
    yield session
    close_sas_session()


@pytest.fixture()
def sas_session(_sas_session_manager):
    return get_sas_session()


@pytest.fixture()
def require_new_sas_session():
    session = create_new_sas_session()
    reset_test_state(session)
    yield session
    try:
        session.endsas()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_sas_workspace():
    sas = get_sas_session()
    reset_test_state(sas)
    yield
    cleanup_test_artifacts(get_sas_session())
```

---

## 4. Key Rules

### 4.1 Naming Convention — ALWAYS use `SASPYTEST_` prefix
- **Datasets:** `SASPYTEST_INPUT`, `SASPYTEST_OUTPUT`, `SASPYTEST_RESULT`
- **Macro variables:** `SASPYTEST_STATUS`, `SASPYTEST_COUNT`
- For tests that request `sas_session`, the `clean_sas_workspace` fixture removes `SASPYTEST_*` datasets from WORK and global macro variables before and after each test

### 4.2 Log Assertions — always use `result["LOG"]`, never `sas.saslog()`
```python
result = sas_session.submit("data SASPYTEST_EX; x=1; run;")
assert_no_errors(result["LOG"])       # CORRECT — only this submission
# assert_no_errors(sas_session.saslog())  # WRONG — cumulative session history
```

### 4.3 Load macros explicitly before use
Tests do **not** autocall-load project macros. Always use `submit_sas_file` first:
```python
from pathlib import Path
MACRO_PATH = Path(__file__).resolve().parent / "example_macro.sas"

def test_something(sas_session):
    submit_sas_file(sas_session, MACRO_PATH)
    result = sas_session.submit(r"%example_macro(hello world);")
    assert_no_errors(result["LOG"])
```

### 4.4 Expected errors — suppress saspy warnings
```python
import pytest

@pytest.mark.filterwarnings("ignore::UserWarning")
def test_expected_error(sas_session):
    result = sas_session.submit("data SASPYTEST_BAD; set nonexistent; run;")
    assert_errors(result["LOG"], ["does not exist"])
```

### 4.5 Custom SAS errors/warnings in macros
```sas
/* Error */
%put %STR(ERR)OR: Dataset not found;
%let syscc = %sysfunc(max(&syscc, 8));

/* Warning */
%put %STR(WAR)NING: Missing values detected;
%let syscc = %sysfunc(max(&syscc, 4));
```

### 4.6 SYSCC behavior
SYSCC is a read/write automatic SAS macro variable. A nonzero value may persist
across submissions in the same session, so use `%let SYSCC = 0;` when a new
scenario requires an explicit reset. Use `%sysfunc(max(&syscc, N))` to raise it
without accidentally lowering a higher existing value. Workspace cleanup removes
test artifacts but does not reset SYSCC or SYSERR.

---

## 5. Fixture Reference

| Fixture | Scope | Purpose |
|---|---|---|
| `sas_session` | function | Shared SAS session (session-scoped manager, function-scoped access) |
| `clean_sas_workspace` | function (autouse) | Auto-clean `SASPYTEST_*` datasets & macros before/after each test |
| `require_new_sas_session` | function | Creates an independent fresh SAS session |

---

## 6. Assertion Reference

### Log Assertions (`saspytest.logs`)

| Function | Description |
|---|---|
| `assert_no_errors(log)` | Assert no ERROR messages in log |
| `assert_no_warnings(log)` | Assert no WARNING messages in log |
| `assert_log_contains(log, pattern, regex=False)` | Assert log contains text or regex |
| `assert_log_not_contains(log, pattern, regex=False)` | Assert log does NOT contain text/regex |
| `assert_errors(log, expected_messages)` | Assert specific ERROR messages exist |
| `assert_warnings(log, expected_messages)` | Assert specific WARNING messages exist |

### Dataset Assertions (`saspytest.datasets`)

| Function | Description |
|---|---|
| `assert_dataset_exists(sas, dataset, libref="WORK", msg=None)` | Assert dataset exists |
| `assert_dataset_not_exists(sas, dataset, libref="WORK", msg=None)` | Assert dataset does not exist |
| `assert_record_count(sas, dataset, expected_count, libref="WORK", msg=None)` | Assert number of observations |
| `assert_columns_exist(sas, dataset, columns, libref="WORK", msg=None)` | Assert specific columns exist |
| `assert_datasets_equal(sas, dataset1, dataset2, libref1="WORK", libref2="WORK", msg=None)` | Assert datasets are identical (PROC COMPARE) |
| `get_dataset_as_df(sas, dataset, libref="WORK")` | Return dataset as pandas DataFrame |

### Macro Assertions (`saspytest.macros`)

| Function | Description |
|---|---|
| `assert_macro_exists(sas, macro_name, msg=None)` | Assert macro variable is defined |
| `assert_macro_value(sas, macro_name, expected_value, msg=None)` | Assert macro variable has expected value |

### Library Assertions (`saspytest.datasets`)

| Function | Description |
|---|---|
| `assert_library_exists(sas, libref, msg=None)` | Assert a SAS library is assigned |

### File Utilities (`saspytest.files`)

| Function | Description |
|---|---|
| `submit_sas_file(sas, local_path)` | Read and submit a `.sas` file; returns `{"LOG": ..., "LST": ...}` |
| `upload_file(sas, local_path, remote_path, overwrite=True)` | Upload file to SAS server |
| `download_file(sas, local_path, remote_path, overwrite=True)` | Download file from SAS server |

---

## 7. Test Patterns

### 7.1 Default simple-project pattern: source and test side by side
```python
"""Tests for example.sas."""

from pathlib import Path

import pytest

from saspytest import assert_no_errors, submit_sas_file

pytestmark = pytest.mark.integration

SAS_PATH = Path(__file__).resolve().parent / "example.sas"


def test_example_returns_empty_for_unsorted_table(sas_session):
    submit_sas_file(sas_session, SAS_PATH)
    result = sas_session.submit(r"%let SASPYTEST_RESULT = %example_macro(SASPYTEST_UNSORTED);")
    assert_no_errors(result["LOG"])
```

Use this pattern when the `.sas` file and `*_test.py` file are in the same directory.

### 7.2 Larger-project macro test
```python
"""Tests for example_macro.sas."""
from pathlib import Path
import pytest
from saspytest import assert_log_contains, assert_no_errors, submit_sas_file

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MACRO_PATH = PROJECT_ROOT / "macros" / "example_macro.sas"

# This example assumes a repo-wide tests tree under `<repo-root>/tests/`.

def test_macro_works(sas_session):
    submit_sas_file(sas_session, MACRO_PATH)
    result = sas_session.submit(r"%example_macro(hello);")
    assert_no_errors(result["LOG"])
    assert_log_contains(result["LOG"], "hello")
```

### 7.3 Larger-project program test
```python
from pathlib import Path
import pytest
from saspytest import assert_no_errors, assert_dataset_exists, submit_sas_file

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MACRO_PATH = PROJECT_ROOT / "macros" / "example_macro.sas"
PROGRAM_PATH = PROJECT_ROOT / "programs" / "example_program.sas"

# This example assumes a repo-wide tests tree under `<repo-root>/tests/`.

def test_program_creates_output(sas_session):
    submit_sas_file(sas_session, MACRO_PATH)
    result = submit_sas_file(sas_session, PROGRAM_PATH)
    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas_session, "SASPYTEST_OUTPUT")
```

### 7.4 Larger-project dataset comparison test (with testdata)
```python
def test_against_expected(sas_session, expected_dataset):
    result = submit_sas_file(sas_session, PROGRAM_PATH)
    assert_no_errors(result["LOG"])
    assert_datasets_equal(
        sas_session,
        "SASPYTEST_OUTPUT",
        expected_dataset,
        libref1="WORK",
        libref2="VERIFY",
    )
```

This example assumes a project fixture has loaded `expected_dataset` into the
`VERIFY` library.

### 7.5 Larger-project parametrized test
```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 2), (5, 10), (10, 20)
])
def test_doubling(sas_session, input_val, expected):
    sas_session.submit("""
        %let SASPYTEST_RESULT = %eval(&input_val * 2);
    """.replace("&input_val", str(input_val)))
    assert_macro_value(sas_session, "SASPYTEST_RESULT", str(expected))
```

### 7.6 Larger-project value checks with `get_dataset_as_df`
```python
from saspytest import get_dataset_as_df

def test_values(sas_session):
    sas_session.submit("""
        data SASPYTEST_DATA;
            id = 1; name = "Alice"; score = 95; output;
        run;
    """)
    df = get_dataset_as_df(sas_session, "SASPYTEST_DATA")
    assert len(df) == 1
    assert df["score"].iloc[0] == 95
```

---

## 8. Running Tests

```bash
# Run all tests
python -m pytest <repo-root>/tests -q

# Single test file
python -m pytest <repo-root>/tests/macros/example_macro_test.py -q

# Single test
python -m pytest <repo-root>/tests/programs/example_program_test.py::test_example_program_logs_input -q
```

Tests marked `integration` require a live SAS connection. The default
`saspytest` fixtures report a setup error when no connection is available. A
project-specific `conftest.py` may provide a skip-on-missing-SAS policy for
copyable examples, but the package integration suite and release validation
must fail when the SAS gate is unavailable.

When the source and test live side by side, run the specific `*_test.py` file from that directory. When using the larger-project layout, run tests from `<repo-root>/tests/`.

---

## 9. Common Pitfalls

| Mistake | Fix |
|---|---|
| Not loading macro before test | Add `submit_sas_file(sas_session, MACRO_PATH)` before calling the macro |
| Using `sas.saslog()` instead of `result["LOG"]` | Always capture `result = sas.submit(...)` and use `result["LOG"]` |
| Not using `SASPYTEST_` prefix | Artifacts won't be auto-cleaned and may collide with other tests |
| Not using `@pytest.mark.filterwarnings` on error tests | saspy emits UserWarning on SAS errors; suppress it |
| Creating inter-test dependencies | Each test must pass independently and in any order |
| Building long tests | Keep tests focused on one scenario; use separate test functions |
