# saspytest — User Guide

A pytest support library for testing SAS programs through the [saspy](https://sassoftware.github.io/saspy/index.html) Python interface.

This guide is for saspytest users writing tests for their SAS programs. Those
tests normally execute against a live SAS session. The repository's mock-based
unit tests are internal contributor tests for saspytest itself and are covered
in [Contributing](../CONTRIBUTING.md).

---

## Table of Contents

- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Session Management](#session-management)
  - [The `sas_session` Fixture](#the-sas_session-fixture)
  - [Automatic Cleanup](#automatic-cleanup)
  - [Isolated Sessions](#isolated-sessions)
  - [Session Configuration](#session-configuration)
  - [Manual Session Management](#manual-session-management)
- [Live-SAS Test Selection](#live-sas-test-selection)
- [Project Layout](#project-layout)
  - [Simple layout — `*_test.py` beside `.sas`](#simple-layout--_testpy-beside-sas)
  - [Separated layout — `tests/` tree](#separated-layout--tests-tree)
- [Log Assertions](#log-assertions)
  - [Checking for Errors and Warnings](#checking-for-errors-and-warnings)
  - [Searching for Patterns](#searching-for-patterns)
  - [Expecting Errors and Warnings](#expecting-errors-and-warnings)
  - [Common Pitfall: Cumulative Logs](#common-pitfall-cumulative-logs)
- [Dataset Assertions](#dataset-assertions)
  - [Existence Checks](#existence-checks)
  - [Row Counts](#row-counts)
  - [Column Checks](#column-checks)
  - [Comparing Datasets](#comparing-datasets)
  - [Converting to pandas](#converting-to-pandas)
- [Macro Variable Assertions](#macro-variable-assertions)
- [File Utilities](#file-utilities)
  - [Uploading and Downloading Files](#uploading-and-downloading-files)
  - [Submitting .sas Files](#submitting-sas-files)
- [Library Assertions](#library-assertions)
- [Full Example: Testing a SAS Program](#full-example-testing-a-sas-program)
- [Writing Custom SAS Errors and Warnings](#writing-custom-sas-errors-and-warnings)
- [Tips and Best Practices](#tips-and-best-practices)

---

## Installation

```bash
pip install saspytest
```

For saspytest contributors (editable install with development dependencies):

```bash
pip install -e ".[dev]"
```

## Prerequisites

- **Python 3.11+**
- A working [saspy](https://sassoftware.github.io/saspy/configuration.html) configuration that can connect to your SAS deployment
- **Java** (required by saspy for IOM connections)
- **pandas 3.0+** (required by `get_dataset_as_df()`)

> saspytest does **not** bundle proprietary SAS JARs. You must provide your own SAS deployment and configure saspy accordingly. `sascfg_personal.py` belongs to saspy; `saspytest_config.py` is saspytest's separate auto-discovered project configuration convention.

---

## Session Management

saspytest manages SAS sessions through pytest fixtures so you don't have to worry about creating, sharing, or closing sessions yourself.

When `saspytest` is installed, pytest auto-loads the `saspytest.session` plugin, so the fixture names below are available without importing them into your test modules.

### The `sas_session` Fixture

The primary way to get a SAS session in your tests is the `sas_session` fixture. It provides a shared `saspy.SASsession` that is created lazily on the first request and reused across the test run:

```python
from saspytest import assert_no_errors

def test_basic_data_step(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_EXAMPLE;
            x = 42;
            output;
        run;
    """)
    assert_no_errors(result["LOG"])
```

**Key points:**
- The session is created once when the first test requests it (session scope)
- Every test function that declares `sas_session` as a parameter receives the same session
- The session is automatically closed when the test run finishes

### Automatic Cleanup

For tests that request `sas_session`, the `clean_sas_workspace` fixture runs
automatically before and after the test. It removes these `SASPYTEST_` artifacts
from the SAS session:

- All `SASPYTEST_*` datasets in the WORK library
- All `SASPYTEST_*` global macro variables

You do not need to request this fixture; it is auto-used. It does not remove
SAS macros or artifacts in libraries other than WORK.

> **Naming convention:** Prefix your test datasets and macro variables with `SASPYTEST_` to get automatic cleanup. For example, `WORK.SASPYTEST_INPUT` or `%let SASPYTEST_RESULT = ...;`.

### SAS Identifier Rules

Dataset names, library references, column names, and macro-variable names used
by saspytest helpers must use conventional ASCII SAS V7 syntax. Names must be
non-empty, start with a letter or underscore, contain only letters, digits, and
underscores, and be no longer than 32 characters. Library references have an
eight-character limit. Pass macro-variable names without `&`.

Name literals, spaces, dots, and other special characters are not escaped and
are rejected with `ValueError`. SAS compares accepted names case-insensitively.

### Isolated Sessions

Sometimes a test needs a completely fresh SAS session (e.g. to test session-level behavior). Use the `require_new_sas_session` fixture:

```python
def test_fresh_session(require_new_sas_session):
    sas = require_new_sas_session
    result = sas.submit("data SASPYTEST_FRESH; x = 1; run;")
    assert_no_errors(result["LOG"])
```

This creates an independent session that:
- Does **not** affect the shared session used by other tests
- Is automatically cleaned up and closed after the test finishes

### Session Configuration

saspytest resolves the saspy configuration in the following order:

1. **Environment variables** (recommended for CI/CD):
   - `SASPY_CONFIG` — path to a saspy configuration file used by `saspytest`
   - `SASPY_CFGNAME` — config name within that file used by `saspytest`
2. **`saspytest_config.py` file discovery** — if no environment variables are set, `saspytest` searches
   the working directory and all parent directories for a file named `saspytest_config.py`. If found,
   its path is passed to saspy automatically.
3. **Default saspy resolution** — if neither environment variables nor `saspytest_config.py` are found,
   saspy falls back to its standard config lookup.

`SASPY_CONFIG` and `SASPY_CFGNAME` are read by `saspytest.session` and passed to
`saspy.SASsession(cfgfile=..., cfgname=...)`. They are not read automatically by
plain `saspy.SASsession()`.

Example CI setup:

```bash
export SASPY_CONFIG="/opt/sas/sascfg_personal.py"
export SASPY_CFGNAME="iomlinux"
pytest tests/ -v
```

### Manual Session Management

For advanced use cases outside of pytest fixtures, you can manage sessions programmatically:

```python
from saspytest import (
    close_sas_session,
    create_new_sas_session,
    get_sas_session,
    reset_sas_session,
)

# Get (or create) the shared session
sas = get_sas_session()

# Close the shared session
close_sas_session()

# Close and recreate the shared session
sas = reset_sas_session()

# Create and close an independent session when shared state must be avoided
isolated = create_new_sas_session()
try:
    isolated.submit("data SASPYTEST_ISOLATED; x = 1; run;")
finally:
    isolated.endsas()
```

> **Note:** In most cases, prefer the `sas_session` fixture. Manual session management is mainly useful for custom tooling or non-pytest contexts.

---

## Live-SAS Test Selection

Tests that use `sas_session` or another live SAS connection execute SAS code
against an external service. They need a working saspy configuration, network
access, and valid credentials. In pytest terminology these are commonly called
integration tests. The unit tests in the saspytest repository use mocks instead
and are not part of the normal user workflow.

If a project also contains SAS-free Python tests, use pytest's `integration`
marker to label tests that require live SAS:

```python
import pytest
from saspytest import assert_no_errors

pytestmark = pytest.mark.integration


def test_sas_program(sas_session):
    result = sas_session.submit("data SASPYTEST_EXAMPLE; x = 1; run;")
    assert_no_errors(result["LOG"])
```

The marker is metadata used for test selection. It does not create a SAS
session, configure saspy, or skip a test automatically. A marked test still
runs when selected normally; the marker lets you choose whether to include it.

Register the custom marker in the project's `pytest.ini` to avoid
`PytestUnknownMarkWarning`:

```ini
[pytest]
markers =
    integration: marks tests that require a live SAS connection
```

Run only live-SAS tests:

```bash
pytest -m integration -v
```

Run tests that do not require live SAS:

```bash
pytest -m "not integration" -v
```

The second command excludes marked tests. For this repository, use
`pytest -c pytest.ini` for the mock-based internal unit suite. That
configuration also disables the saspytest plugin so those tests cannot
accidentally start a SAS session.

---

## Project Layout

saspytest works with any project layout. Choose based on project size.

### Simple layout — `*_test.py` beside `.sas`

For small projects, place the test file next to the SAS file and name it `*_test.py`:

```text
my-project/
├── pytest.ini          ← optional: restricts discovery to *_test.py
├── my_macro.sas
└── my_macro_test.py
```

Pytest discovers both `test_*.py` and `*_test.py` by default. Add a
`pytest.ini` setting only when you want to restrict or customize discovery:

```ini
[pytest]
python_files = *_test.py
markers =
    integration: marks tests that require a live SAS connection
filterwarnings =
    ignore::UserWarning:saspy.sasioiom
    ignore::UserWarning:saspy.sasiostdio
    ignore::UserWarning:saspy.sasiohttp
    ignore::UserWarning:saspy.sasiocom
```

Reference the SAS file with `Path(__file__).resolve().parent`:

```python
from pathlib import Path
import pytest
from saspytest import assert_no_errors, submit_sas_file

pytestmark = pytest.mark.integration

SAS_PATH = Path(__file__).resolve().parent / "my_macro.sas"

def test_my_macro(sas_session):
    submit_sas_file(sas_session, SAS_PATH)
    result = sas_session.submit(r"%my_macro(hello);")
    assert_no_errors(result["LOG"])
```

Run the project normally:

```bash
pytest my-project -v
```

Use `-m integration` only when the project also contains SAS-free Python tests.

See [`examples/hello_world_simple_layout/`](../examples/hello_world_simple_layout/README.md) for a working example.

### Separated layout — `tests/` tree

For larger projects with many macros and programs, group SAS files into source directories and tests into a separate `tests/` tree:

```text
my-project/
├── pytest.ini          ← sets testpaths = tests
├── macros/
│   └── my_macro.sas
├── programs/
│   └── my_program.sas
└── tests/
    ├── macros/
    │   └── test_my_macro.py
    └── programs/
        └── test_my_program.py
```

`pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    integration: marks tests that require a live SAS connection
filterwarnings =
    ignore::UserWarning:saspy.sasioiom
    ignore::UserWarning:saspy.sasiostdio
    ignore::UserWarning:saspy.sasiohttp
    ignore::UserWarning:saspy.sasiocom
```

Reference SAS files by navigating up from the test file:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MACRO_PATH = PROJECT_ROOT / "macros" / "my_macro.sas"
```

Run the project normally:

```bash
pytest my-project -v
```

See [`examples/hello_world/`](../examples/hello_world/README.md) and [`examples/roman_numerals/`](../examples/roman_numerals/README.md) for working examples.

---

## Log Assertions

SAS communicates outcomes through its log. saspytest provides assertion functions to validate log contents.

### Checking for Errors and Warnings

The most common assertion — verify that a SAS step completed without errors:

```python
from saspytest import assert_no_errors, assert_no_warnings

def test_clean_execution(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_CLEAN;
            x = 1;
            output;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_no_warnings(result["LOG"])
```

### Searching for Patterns

Check for specific text or regex patterns in the log:

```python
from saspytest import assert_log_contains, assert_log_not_contains

def test_log_messages(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_DEMO;
            x = 1;
            output;
        run;
    """)

    # Plain text search
    assert_log_contains(result["LOG"], "NOTE:")

    # Regex search
    assert_log_contains(result["LOG"], r"NOTE:.*observations", regex=True)

    # Ensure something is absent
    assert_log_not_contains(result["LOG"], "uninitialized")
```

### Expecting Errors and Warnings

When testing error-handling logic, you may **want** errors or warnings to appear:

```python
import pytest
from saspytest import assert_errors, assert_warnings

@pytest.mark.filterwarnings("ignore::UserWarning")
def test_expected_error(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_BAD;
            set work.nonexistent_dataset;
        run;
    """)
    assert_errors(result["LOG"], ["does not exist"])


def test_expected_warning(sas_session):
    result = sas_session.submit("""
        %put %STR(WAR)NING: Division by zero example;
        %let syscc = %sysfunc(max(&syscc, 4));
    """)
    assert_warnings(result["LOG"], ["Division by zero example"])
```

> **Tip:** When testing code that produces SAS errors, saspy emits a Python `UserWarning`. Add `@pytest.mark.filterwarnings("ignore::UserWarning")` to suppress it in test output.

### Common Pitfall: Cumulative Logs

```python
# CORRECT — use the log from submit()
result = sas_session.submit("data SASPYTEST_LOG_OK; x=1; run;")
assert_no_errors(result["LOG"])  # Only this submission's log

# WRONG — sas.saslog() returns the entire session history
sas_session.submit("data SASPYTEST_LOG_OK; x=1; run;")
assert_no_errors(sas_session.saslog())  # Includes ALL previous submissions!
```

Always use `result["LOG"]` from the `submit()` return value.

---

## Dataset Assertions

Validate SAS datasets created during your tests.

### Existence Checks

```python
from saspytest import assert_dataset_exists, assert_dataset_not_exists

def test_dataset_creation(sas_session):
    sas_session.submit("""
        data work.SASPYTEST_OUTPUT;
            do i = 1 to 10; output; end;
        run;
    """)

    assert_dataset_exists(sas_session, "SASPYTEST_OUTPUT")
    assert_dataset_not_exists(sas_session, "this_does_not_exist")
```

To check a dataset in a specific library:

```python
assert_dataset_exists(sas_session, "mydata", libref="SASHELP")
```

### Row Counts

```python
from saspytest import assert_record_count

def test_row_count(sas_session):
    sas_session.submit("""
        data work.SASPYTEST_COUNTS;
            do i = 1 to 100; output; end;
        run;
    """)

    assert_record_count(sas_session, "SASPYTEST_COUNTS", 100)
```

### Column Checks

```python
from saspytest import assert_columns_exist

def test_columns(sas_session):
    sas_session.submit("""
        data work.SASPYTEST_COLS;
            name = "Alice";
            age = 30;
            score = 95.5;
            output;
        run;
    """)

    assert_columns_exist(sas_session, "SASPYTEST_COLS", ["name", "age", "score"])
```

### Comparing Datasets

Verify that two datasets are identical using PROC COMPARE:

```python
from saspytest import assert_datasets_equal

def test_dataset_equality(sas_session):
    sas_session.submit("""
        data work.SASPYTEST_ORIGINAL;
            x = 1; y = 2; output;
        run;

        data work.SASPYTEST_COPY;
            set work.SASPYTEST_ORIGINAL;
        run;
    """)

    assert_datasets_equal(sas_session, "SASPYTEST_ORIGINAL", "SASPYTEST_COPY")
```

To compare datasets across different libraries:

```python
assert_datasets_equal(
    sas_session,
    "dataset_a", "dataset_b",
    libref1="WORK", libref2="MYLIB",
)
```

### Converting to pandas

Pull a SAS dataset into a pandas DataFrame for further analysis:

```python
from saspytest import get_dataset_as_df

def test_data_values(sas_session):
    sas_session.submit("""
        data work.SASPYTEST_PANDAS;
            do i = 1 to 5;
                value = i * 10;
                output;
            end;
        run;
    """)

    df = get_dataset_as_df(sas_session, "SASPYTEST_PANDAS")
    assert len(df) == 5
    assert df["value"].sum() == 150
```

---

## Macro Variable Assertions

Verify SAS macro variable values set during program execution:

```python
from saspytest import assert_macro_exists, assert_macro_value

def test_macro_variables(sas_session):
    sas_session.submit("""
        %let SASPYTEST_GREETING = Hello;
        %let SASPYTEST_COUNT = 42;
    """)

    assert_macro_exists(sas_session, "SASPYTEST_GREETING")
    assert_macro_value(sas_session, "SASPYTEST_GREETING", "Hello")
    assert_macro_value(sas_session, "SASPYTEST_COUNT", "42")
```

> **Note:** Macro variable names are passed **without** the `&` prefix.

---

## File Utilities

### Uploading and Downloading Files

Transfer files between the local filesystem and the SAS server:

```python
from saspytest import upload_file, download_file

def test_file_transfer(sas_session):
    # Upload a local file to the SAS server
    success = upload_file(sas_session, "/tmp/input.csv", "/tmp/sas_input.csv")
    assert success

    # Download a file from the SAS server
    success = download_file(sas_session, "/tmp/output.csv", "/tmp/sas_output.csv")
    assert success
```

### Submitting .sas Files

Run a `.sas` program file through an existing session:

```python
from saspytest import submit_sas_file, assert_no_errors

def test_sas_program(sas_session, tmp_path):
    program = tmp_path / "etl_pipeline.sas"
    program.write_text(
        "data work.SASPYTEST_FILE_RUN; x = 1; output; run;",
        encoding="utf-8",
    )

    result = submit_sas_file(sas_session, program)

    assert_no_errors(result["LOG"])
```

The function reads the file locally and submits its contents to SAS. It returns the same `{"LOG": ..., "LST": ...}` dict as `sas.submit()`.

Raises `FileNotFoundError` if the file does not exist.

---

## Library Assertions

Verify that a SAS library is assigned and accessible:

```python
from saspytest import assert_library_exists

def test_library(sas_session):
    assert_library_exists(sas_session, "WORK")
    assert_library_exists(sas_session, "SASHELP")
```

---

## Full Example: Testing a SAS Program

Here is a complete test file demonstrating typical usage patterns:

```python
"""tests/test_etl.py — Test an ETL pipeline in SAS."""
from saspytest import (
    assert_no_errors,
    assert_no_warnings,
    assert_dataset_exists,
    assert_record_count,
    assert_columns_exist,
    assert_macro_value,
    submit_sas_file,
    get_dataset_as_df,
)


def test_etl_creates_output(sas_session, tmp_path):
    """Verify the ETL step creates the expected output dataset."""
    # Arrange: create input data
    result = sas_session.submit("""
        data work.SASPYTEST_INPUT;
            do id = 1 to 100;
                name = cats("Person_", id);
                score = round(ranuni(42) * 100);
                output;
            end;
        run;
    """)
    assert_no_errors(result["LOG"])

    program = tmp_path / "transform.sas"
    program.write_text(
        """
data work.SASPYTEST_OUTPUT;
    set work.SASPYTEST_INPUT;
    length grade $1;
    if score >= 90 then grade = "A";
    else if score >= 80 then grade = "B";
    else if score >= 70 then grade = "C";
    else if score >= 60 then grade = "D";
    else grade = "F";
run;

%let SASPYTEST_ETL_STATUS = COMPLETE;
        """.strip(),
        encoding="utf-8",
    )

    # Act: run the ETL program
    result = submit_sas_file(sas_session, program)
    assert_no_errors(result["LOG"])
    assert_no_warnings(result["LOG"])

    # Assert: check outputs
    assert_dataset_exists(sas_session, "SASPYTEST_OUTPUT")
    assert_record_count(sas_session, "SASPYTEST_OUTPUT", 100)
    assert_columns_exist(sas_session, "SASPYTEST_OUTPUT", ["id", "name", "score", "grade"])


def test_etl_grade_distribution(sas_session, tmp_path):
    """Verify grade calculations are correct."""
    result = sas_session.submit("""
        data work.SASPYTEST_INPUT;
            id = 1; name = "Alice"; score = 95; output;
            id = 2; name = "Bob";   score = 72; output;
            id = 3; name = "Carol"; score = 40; output;
        run;
    """)
    assert_no_errors(result["LOG"])

    program = tmp_path / "transform.sas"
    program.write_text(
        """
data work.SASPYTEST_OUTPUT;
    set work.SASPYTEST_INPUT;
    length grade $1;
    if score >= 90 then grade = "A";
    else if score >= 80 then grade = "B";
    else if score >= 70 then grade = "C";
    else if score >= 60 then grade = "D";
    else grade = "F";
run;

%let SASPYTEST_ETL_STATUS = COMPLETE;
        """.strip(),
        encoding="utf-8",
    )

    result = submit_sas_file(sas_session, program)
    assert_no_errors(result["LOG"])

    df = get_dataset_as_df(sas_session, "SASPYTEST_OUTPUT")
    grades = dict(zip(df["name"].str.strip(), df["grade"].str.strip()))

    assert grades["Alice"] == "A"
    assert grades["Bob"] == "C"
    assert grades["Carol"] == "F"


def test_etl_sets_status_macro(sas_session, tmp_path):
    """Verify the ETL program sets a status macro variable."""
    sas_session.submit("""
        data work.SASPYTEST_INPUT;
            id = 1; name = "Test"; score = 80; output;
        run;
    """)

    program = tmp_path / "transform.sas"
    program.write_text(
        """
data work.SASPYTEST_OUTPUT;
    set work.SASPYTEST_INPUT;
    length grade $1;
    if score >= 90 then grade = "A";
    else if score >= 80 then grade = "B";
    else if score >= 70 then grade = "C";
    else if score >= 60 then grade = "D";
    else grade = "F";
run;

%let SASPYTEST_ETL_STATUS = COMPLETE;
        """.strip(),
        encoding="utf-8",
    )

    submit_sas_file(sas_session, program)

    assert_macro_value(sas_session, "SASPYTEST_ETL_STATUS", "COMPLETE")
```

For copyable starter projects with realistic folder layouts, see:

- [`examples/hello_world_simple_layout/`](../examples/hello_world_simple_layout/README.md) for the simplest setup: `*_test.py` beside `.sas`, no `tests/` tree
- [`examples/hello_world/`](../examples/hello_world/README.md) for a macro/program test setup with a separated `tests/` tree
- [`examples/roman_numerals/`](../examples/roman_numerals/README.md) for a fuller project with local test data and dataset comparisons

The Roman Numerals example includes:

- `macros/number_to_roman.sas`
- `programs/convert_numbers.sas`
- `testdata/saspytest_roman_input.sas7bdat`
- `testdata/saspytest_roman_expected.sas7bdat`
- `tests/macros/test_number_to_roman.py`
- `tests/programs/test_convert_numbers.py`

---

## Writing Custom SAS Errors and Warnings

When writing SAS code that generates custom errors or warnings, use `%STR()` to
prevent SAS from treating `ERROR` and `WARNING` as keywords during parsing.
Splitting the words as `ERR` + `OR` and `WAR` + `NING` lets the text appear in
the submitted log while avoiding premature macro parsing.

```sas
/* Custom error */
%put %STR(ERR)OR: Dataset &indata not found;
%let syscc = %sysfunc(max(&syscc, 8));

/* Custom warning */
%put %STR(WAR)NING: Missing values found in &var;
%let syscc = %sysfunc(max(&syscc, 4));

/* Notes work directly */
%put NOTE: Processing started;
```

Use `%sysfunc(max(&syscc, N))` to raise the system completion code without accidentally lowering it if a previous step already set a higher error level.

`SYSCC` is a read/write automatic SAS macro variable:

- `SYSCC = 0` represents a normal internal SAS completion.
- `SYSCC = 4` is the conventional warning condition code.
- `SYSCC >= 8` is the conventional error condition range used by these examples.

See the [SAS SYSCC reference](https://support.sas.com/documentation/cdl/en/mcrolref/62978/HTML/default/p11nt7mv7k9hl4n1x9zwkralgq1b.htm) for the SAS-defined variable and host return-code behavior.

SAS translates the internal condition code into an operating-system return code,
so the exact host-level mapping is environment-specific. A nonzero `SYSCC` value
may persist across submissions in the same SAS session, even after a later clean
submission. Reset it explicitly when a new scenario requires a clean condition
code:

```sas
%let SYSCC = 0;
```

The `reset_test_state()` and `cleanup_test_artifacts()` helpers remove
`SASPYTEST_*` datasets and macro variables but deliberately do not reset `SYSCC`
or `SYSERR`. Tests that intentionally produce errors or warnings should assert
the submitted log and, when relevant, the resulting `SYSCC` value. `SYSERR`
reports the last SAS step's error condition and is likewise not reset by
saspytest's workspace cleanup.

---

## Tips and Best Practices

1. **Always use `result["LOG"]`** from `submit()` for assertions — never `sas.saslog()`, which contains the entire session history.

2. **Prefix test artifacts with `SASPYTEST_`** so the automatic cleanup fixture removes them between tests.

3. **Tests should be independent and idempotent.** They must pass in any order and produce the same result when run repeatedly.

4. **Use `@pytest.mark.filterwarnings("ignore::UserWarning")`** on tests that intentionally produce SAS errors, to suppress saspy's Python warning.

5. **Provide custom error messages** via the `msg` parameter when the default assertion message might not give enough context:

    ```python
    assert_record_count(sas, "SASPYTEST_OUTPUT", 100, msg="ETL should produce exactly 100 rows")
    ```

6. **Use `require_new_sas_session`** only when you truly need a fresh session. The shared session is faster because it avoids the overhead of creating a new SAS connection per test.

7. **For file-based tests**, use `submit_sas_file()` to run `.sas` programs. It reads the file locally and submits the code, returning the log and listing for assertion.
