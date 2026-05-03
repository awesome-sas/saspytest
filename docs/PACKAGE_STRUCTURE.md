# saspytest Package Structure

## Repository Layout

The project uses a modern Python `src/` layout:

```
saspytest/
├── src/
│   └── saspytest/           # Main package source
│       ├── __init__.py      # Package initialization and exports
│       ├── _identifiers.py  # SAS identifier validation
│       ├── session.py       # Session management (fixtures, get/close session)
│       ├── files.py         # File handling (upload/download, submit .sas files)
│       ├── macros.py        # Macro variable assertions
│       ├── logs.py          # Log assertions (errors, warnings, patterns)
│       └── datasets.py      # Dataset/library assertions
├── tests/
│   ├── unit/                # Internal mock-based tests for saspytest
│   └── integration/         # Package tests requiring a live SAS connection
├── examples/                # Copyable starter projects
│   ├── README.md            # Layout guide and run instructions
│   ├── hello_world_simple_layout/   # Flat layout: *_test.py beside .sas files
│   ├── hello_world/         # Separated layout: macros/, programs/, tests/
│   └── roman_numerals/      # Full project with testdata and dataset comparisons
├── docs/                    # Documentation
│   ├── README.md            # PyPI description
│   ├── USAGE.md             # User guide
│   ├── API_REFERENCE.md     # Full API reference
│   ├── DEVELOPMENT.md       # Development setup guide
│   ├── DEVELOPMENT_GUIDELINES.md  # Testing conventions
│   ├── GETTING_STARTED.md    # First live-SAS user test
│   ├── RELEASE_TESTING.md    # External live-SAS release guide
│   ├── SUPPORT.md             # Stable compatibility and limitation policy
│   ├── PACKAGE_STRUCTURE.md # This file
│   └── SKILLS.md            # AI agent skill overview
├── agents/
│   └── skills/              # AI agent skill definitions
├── scripts/
│   ├── check_code.py        # Code quality runner (Black + Flake8 + Pylint)
│   └── run_tests.py         # Unit, integration, and example-suite runner
├── .github/workflows/       # CI, TestPyPI, and PyPI release workflows
├── AGENTS.md                # AI agent instructions
├── README.md                # GitHub landing page
├── CHANGELOG.md             # User-visible release history
├── CONTRIBUTING.md          # Contribution and development guidance
├── CODE_OF_CONDUCT.md       # Community standards
├── SECURITY.md              # Vulnerability reporting guidance
├── LICENSE                  # MIT License
├── pyproject.toml           # Package metadata and dependency declarations
└── pytest.ini               # pytest configuration for internal unit tests
```

## Installation

Install in development/editable mode:

```bash
pip install -e ".[dev]"
```

This means changes to the source code are immediately reflected without reinstalling.

## Usage in Tests

Import helpers directly from the `saspytest` package:

```python
from saspytest import (
    assert_no_errors,
    assert_dataset_exists,
)

def test_example(sas_session):
    result = sas_session.submit("data SASPYTEST_EXAMPLE; x=1; run;")
    assert_no_errors(result['LOG'])
    assert_dataset_exists(sas_session, "SASPYTEST_EXAMPLE")
```

> **Note:** `saspytest` registers `saspytest.session` as a pytest plugin via the `pytest11` entry point, so pytest loads the `sas_session`, `clean_sas_workspace`, and `require_new_sas_session` fixtures automatically once the package is installed. They are intentionally **not** exported via `from saspytest import ...`.

## Extracted Functions

### Session Management (`session.py`)
- `get_sas_session()` - Get or create shared SAS session
- `close_sas_session()` - Close the shared SAS session
- `reset_sas_session()` - Close and recreate the shared session
- `create_new_sas_session()` - Create an independent SAS session
- `reset_test_state(sas)` - Reset SAS test artifacts (datasets, macros)
- `cleanup_test_artifacts(sas)` - Alias for `reset_test_state()`
- `sas_session` - Pytest fixture (session-scoped manager + function-scoped access)
- `clean_sas_workspace` - Pytest fixture (autouse=True)
- `require_new_sas_session` - Pytest fixture (isolated session)

### File Handling (`files.py`)
- `upload_file(sas, local_path, remote_path, overwrite=True)`
- `download_file(sas, local_path, remote_path, overwrite=True)`
- `submit_sas_file(sas, local_path)`

### Macro Assertions (`macros.py`)
- `assert_macro_value(sas, macro_name, expected_value, msg=None)`
- `assert_macro_exists(sas, macro_name, msg=None)`

### Log Assertions (`logs.py`)
- `assert_log_contains(log, pattern, regex=False, msg=None)`
- `assert_log_not_contains(log, pattern, regex=False, msg=None)`
- `assert_no_errors(log, msg=None)`
- `assert_no_warnings(log, msg=None)`
- `assert_errors(log, expected_messages, msg=None)`
- `assert_warnings(log, expected_messages, msg=None)`

### Dataset Assertions (`datasets.py`)
- `assert_dataset_exists(sas, dataset, libref="WORK", msg=None)`
- `assert_dataset_not_exists(sas, dataset, libref="WORK", msg=None)`
- `assert_library_exists(sas, libref, msg=None)`
- `assert_record_count(sas, dataset, expected_count, libref="WORK", msg=None)`
- `assert_columns_exist(sas, dataset, columns, libref="WORK", msg=None)`
- `assert_datasets_equal(sas, dataset1, dataset2, libref1="WORK", libref2="WORK", msg=None)`
- `get_dataset_as_df(sas, dataset, libref="WORK")`

## Benefits

1. **Modularity**: Helper functions organized by category
2. **Reusability**: Can be imported and used in any test file
3. **Maintainability**: Single source of truth for test utilities
4. **Distribution**: Installed as a package and shared via PyPI
5. **Type Safety**: Better IDE support with organized imports

## Publishing

To publish a new release to PyPI:

1. Update `project.version` in `pyproject.toml` and `CHANGELOG.md`
2. Run `python -m build` and `python -m twine check dist/*`
3. Install the wheel in a clean environment and run
   `pytest -c pytest.ini -v`
4. Complete the external live-SAS release gate with
   `python scripts/run_tests.py`
5. Create and publish a GitHub release; the release workflow validates the tag,
   changelog, package build, and unit tests before publishing to PyPI.

The `pyproject.toml` file is the single source of truth for package metadata and
dependencies. Install it in editable mode for local development. CI and release
workflows are tracked under `.github/workflows/`.
