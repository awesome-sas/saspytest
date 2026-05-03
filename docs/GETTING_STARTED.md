# Getting Started

`saspytest` lets you write pytest tests that execute SAS code through a live
[saspy](https://sassoftware.github.io/saspy/) session.

The normal user workflow is:

1. Install `saspytest`.
2. Configure saspy for your SAS deployment.
3. Submit a SAS program or macro from a pytest test.
4. Assert against the SAS log, datasets, macro variables, or files.

## Install

```bash
pip install saspytest
```

You need Python 3.11 or later, a SAS deployment that saspy can access, Java for
IOM connections, and pandas 3.0 or later for the `get_dataset_as_df()` helper.
See the [Support Policy](SUPPORT.md) for the tested Python versions and SAS
configuration limitations.

## Configure SAS Execution environment

You can configure a project with either environment variables or an
auto-discovered `saspytest_config.py` file.

### Environment variables

Use environment variables in CI/CD or when the configuration file should live
outside the project:

```bash
export SASPY_CONFIG=/path/to/sascfg_personal.py
export SASPY_CFGNAME=oda
```

`sascfg_personal.py` is saspy's configuration file. `saspytest_config.py` is a
separate saspytest convention for locating that same saspy-compatible
configuration through the project directory.

### Project configuration file

For local development, place a file named `saspytest_config.py` in the
directory where pytest runs, or in one of its parent directories:

```text
my-sas-project/
├── saspytest_config.py
├── greetings.sas
└── greetings_test.py
```

The file uses the standard [saspy configuration format](https://sassoftware.github.io/saspy/configuration.html#sascfg-personal-py):

```python
SAS_config_names = ["oda"]

oda = {
    "iomhost": "sas.example.com",
    "iomport": 8591,
    "encoding": "utf-8",
}
```

Do not commit credentials or proprietary SAS JAR files. Add local configuration
files to `.gitignore`.

## Write Your First Test

Create `greetings.sas`:

```sas
%macro greetings(name);
    %put NOTE: Hello &name.;
%mend greetings;
```

Create `greetings_test.py` beside it:

```python
from pathlib import Path

from saspytest import assert_log_contains, assert_no_errors, submit_sas_file


SAS_FILE = Path(__file__).resolve().parent / "greetings.sas"


def test_greetings(sas_session):
    submit_sas_file(sas_session, SAS_FILE)
    result = sas_session.submit(r"%greetings(World);")

    assert_no_errors(result["LOG"])
    assert_log_contains(result["LOG"], "Hello World")
```

Run the test from the project directory:

```bash
pytest -v
```

The `sas_session` fixture is provided automatically by saspytest. It creates a
shared SAS session for the test run and closes it afterward.

## Check SAS Logs Correctly

Always assert against the log returned by the submission being tested:

```python
result = sas_session.submit("data work.SASPYTEST_OUTPUT; x = 1; run;")
assert_no_errors(result["LOG"])
```

Do not use `sas_session.saslog()` for this purpose. It contains cumulative
session history and can include messages from earlier tests.

## Test Datasets And Macro Variables

Prefix temporary datasets and macro variables with `SASPYTEST_`:

```python
from saspytest import (
    assert_dataset_exists,
    assert_no_errors,
    assert_record_count,
)


def test_output(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_OUTPUT;
            do id = 1 to 5;
                output;
            end;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas_session, "SASPYTEST_OUTPUT")
    assert_record_count(sas_session, "SASPYTEST_OUTPUT", 5)
```

The `clean_sas_workspace` fixture removes these test artifacts between tests.
Import the dataset assertions used by the example from `saspytest`.

## Selecting Live-SAS Tests

You do not need a marker for a project containing only live-SAS tests. If your
project also contains SAS-free Python tests, mark the live-SAS tests:

```python
import pytest

pytestmark = pytest.mark.integration
```

Register the marker in your project's `pytest.ini`:

```ini
[pytest]
markers =
    integration: marks tests that require a live SAS connection
```

Then select either group:

```bash
pytest -m integration -v
pytest -m "not integration" -v
```

## Next Steps

- Read the [User Guide](USAGE.md) for sessions, assertions, file utilities,
  and dataset comparisons.
- See the [API Reference](API_REFERENCE.md) for exact function behavior.
- Copy the [simple layout example](../examples/hello_world_simple_layout/README.md)
  for a small project.
- Use the [separated layout example](../examples/hello_world/README.md) for a
  larger project with `macros/`, `programs/`, and `tests/` directories.

## For Contributors

The repository also contains mock-based unit tests for saspytest itself. Those
tests verify internal Python behavior and are not required when writing tests
for your own SAS programs. Contributor instructions are in
[CONTRIBUTING.md](../CONTRIBUTING.md).
