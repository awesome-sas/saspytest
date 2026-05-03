# saspytest

**pytest support library for SAS testing with saspy.**

saspytest provides utility functions and pytest-style assertions for testing SAS programs through the [saspy](https://sassoftware.github.io/saspy/index.html) Python interface. It is inspired by SASUnit assertion macros.

---

## Features

- **Session management** – Shared or isolated SAS sessions with automatic setup and teardown
- **Log assertions** – Validate SAS logs for errors, warnings, or custom patterns
- **Dataset assertions** – Check dataset existence, record counts, columns, and equality
- **Macro assertions** – Verify SAS macro variable values and existence
- **File utilities** – Upload/download files and submit local `.sas` scripts

---

## Installation

```bash
pip install saspytest
```

With [uv](https://docs.astral.sh/uv/), use `uv add saspytest` in a uv-managed
project, or `uv pip install saspytest` in an existing environment.

### Prerequisites

- Python 3.11+
- A working [saspy](https://sassoftware.github.io/saspy/configuration.html) configuration that can connect to your SAS deployment
- Java (required by saspy only for IOM connections)
- pandas 3.0+ (required by saspytest's `get_dataset_as_df()` helper)

> **Note:** saspytest does **not** bundle proprietary SAS JARs. You must provide your own SAS deployment and configure saspy accordingly. `sascfg_personal.py` is saspy's configuration file; `saspytest_config.py` is saspytest's separate auto-discovered project configuration convention. See [Getting Started](https://github.com/awesome-sas/saspytest/blob/main/docs/GETTING_STARTED.md).

---

## Getting Started

The normal saspytest workflow is to write pytest tests that execute SAS code
against a live SAS session. See the [Getting Started guide](https://github.com/awesome-sas/saspytest/blob/main/docs/GETTING_STARTED.md).

Run a user test project with:

```bash
pytest -v
```

The repository's mock-based unit tests are internal contributor tests. They do
not require SAS and are documented in
[Contributing](https://github.com/awesome-sas/saspytest/blob/main/CONTRIBUTING.md).

---

## Quickstart

When `saspytest` is installed, pytest auto-loads the package's fixture plugin, so
the `sas_session` fixture is available in your tests without importing it. The
example requires a live SAS connection. If a project also contains SAS-free
Python tests, use the optional [live-SAS test marker](https://github.com/awesome-sas/saspytest/blob/main/docs/USAGE.md#live-sas-test-selection).

```python
from saspytest import (
    assert_no_errors,
    assert_dataset_exists,
    assert_record_count,
)


def test_sas_program(sas_session):
    result = sas_session.submit("""
        data work.SASPYTEST_EXAMPLE;
            do i = 1 to 5;
                output;
            end;
        run;
    """)

    assert_no_errors(result["LOG"])
    assert_dataset_exists(sas_session, "SASPYTEST_EXAMPLE")
    assert_record_count(sas_session, "SASPYTEST_EXAMPLE", 5)
```

---

## Documentation

- **[Getting Started](https://github.com/awesome-sas/saspytest/blob/main/docs/GETTING_STARTED.md)** – Configure SAS execution environment and write your first live-SAS test
- **[User Guide](https://github.com/awesome-sas/saspytest/blob/main/docs/USAGE.md)** – How to use saspytest: session management, assertions, file utilities, and examples
- [API Reference](https://github.com/awesome-sas/saspytest/blob/main/docs/API_REFERENCE.md) – Complete function and fixture reference
- [Support Policy](https://github.com/awesome-sas/saspytest/blob/main/docs/SUPPORT.md) – Supported Python, saspy, and SAS configurations
- [Development Setup](https://github.com/awesome-sas/saspytest/blob/main/docs/DEVELOPMENT.md) – Getting started as a contributor
- [Development Guidelines](https://github.com/awesome-sas/saspytest/blob/main/docs/DEVELOPMENT_GUIDELINES.md) – Code style and conventions
- [AI Skills](https://github.com/awesome-sas/saspytest/tree/main/agents/skills/) – Agent skills available in this repository (e.g. `sas-tester`)

---

## License

MIT License. See [LICENSE](https://github.com/awesome-sas/saspytest/blob/main/LICENSE) for details.
