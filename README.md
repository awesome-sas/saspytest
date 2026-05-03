# saspytest

[![CI](https://github.com/awesome-sas/saspytest/actions/workflows/ci.yml/badge.svg)](https://github.com/awesome-sas/saspytest/actions/workflows/ci.yml)

## saspy + pytest = saspytest

**Testing of SAS programs made easy**

saspytest provides utility functions and pytest-style assertions for testing SAS programs through the [saspy](https://sassoftware.github.io/saspy/) Python interface. It is inspired by SASUnit assertion macros.

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
- A working [saspy](https://sassoftware.github.io/saspy/) configuration that can connect to your SAS deployment
- Java (required by saspy for IOM connections)
- pandas 3.0+ (required by saspytest's `get_dataset_as_df()` helper)

> **Note:** saspytest does **not** bundle proprietary SAS JARs for IOM connections. You must provide your own SAS deployment and configure saspy accordingly. `sascfg_personal.py` is saspy's configuration file; `saspytest_config.py` is saspytest's separate auto-discovered project configuration convention. See the [Getting Started guide](docs/GETTING_STARTED.md).

---

## Quickstart

The normal saspytest test is a pytest test that executes SAS code against a live
SAS session. Follow the [Getting Started guide](docs/GETTING_STARTED.md) to
configure saspy and write your first test.

After installation, pytest auto-loads saspytest's plugin, which provides the
`sas_session` fixture:

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

Run it with:

```bash
pytest -v
```

If your project also contains SAS-free Python tests, use pytest's optional
`integration` marker to select the live-SAS tests. The marker is explained in
the [User Guide](docs/USAGE.md#live-sas-test-selection).

---

## Maintainer Testing

The repository's mock-based unit tests test saspytest's internal Python
implementation and do not require SAS. They are intended for contributors, not
for normal saspytest users:

```bash
pytest -c pytest.ini -v
```

Run the live-SAS package tests and examples with the repository test runner:

```bash
python scripts/run_tests.py
```

See [Contributing](CONTRIBUTING.md) and [Release Testing](docs/RELEASE_TESTING.md)
for maintainer workflows.

---

## Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** – Configure SAS access and write your first live-SAS test
- **[User Guide](docs/USAGE.md)** – Complete usage guide for sessions, assertions, file utilities, and examples
- [API Reference](docs/API_REFERENCE.md) – Complete function and fixture reference
- [Package Structure](docs/PACKAGE_STRUCTURE.md) – Architecture and design decisions
- [Development Setup](docs/DEVELOPMENT.md) – Getting started as a contributor
- [Support Policy](docs/SUPPORT.md) – Supported Python, saspy, and SAS configurations
- [Release Testing](docs/RELEASE_TESTING.md) – External live-SAS validation for maintainers
- [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md) – Code style and conventions
- [Examples](examples/README.md) – Copyable starter projects for testing SAS macros and programs
- [Hello World — Simple Layout](examples/hello_world_simple_layout/README.md) – Smallest setup: `*_test.py` files beside `.sas` files, no `tests/` tree
- [Hello World](examples/hello_world/README.md) – Separated layout with `macros/`, `programs/`, and `tests/` directories
- [Roman Numerals](examples/roman_numerals/README.md) – Starter SAS project with a macro, program, test data, and live-SAS tests

## GenAI sas-tester Skill
The git repository provides a [sas-tester](agents/skills/sas-tester/SKILL.md) skill.
This skill knows everything about the saspytest framework and can assist in writing and running saspytest tests.

---

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
