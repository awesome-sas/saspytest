# Examples

This directory contains copyable starter projects that show how to structure
SAS programs, macros, test data, and pytest-based checks with `saspytest`.

## Projects

| Project | Layout | Demonstrates |
|---|---|---|
| [Hello World — Simple Layout](hello_world_simple_layout/README.md) | Flat (`*_test.py` beside `.sas`) | Simplest setup; ideal for small projects |
| [Hello World](hello_world/README.md) | Separated (`tests/` tree, `test_*.py`) | Macro + program with log assertions |
| [Roman Numerals](roman_numerals/README.md) | Separated (`tests/` tree, `test_*.py`) | Full project with testdata and dataset comparisons |

## Project Layouts

### Simple layout — `*_test.py` beside `.sas`

Use this for small projects where the test naturally lives next to the SAS file:

```text
my-project/
├── pytest.ini          ← sets python_files = *_test.py
├── conftest.py
├── my_macro.sas
└── my_macro_test.py
```

Run with:
```bash
pytest my-project -v
```

### Separated layout — `tests/` tree

Use this for larger projects with many macros and programs:

```text
my-project/
├── pytest.ini          ← sets testpaths = tests
├── macros/
│   └── my_macro.sas
├── programs/
│   └── my_program.sas
└── tests/
    ├── conftest.py
    ├── macros/
    │   └── test_my_macro.py
    └── programs/
        └── test_my_program.py
```

Run with:
```bash
pytest my-project/tests -v
```

## Running The Example Tests

Each example project includes its own `pytest.ini`. The commands below assume
they are run from the repository root:

```bash
# Simple layout
pytest examples/hello_world_simple_layout -v

# Separated layout — pytest.ini points testpaths at tests/
pytest examples/hello_world -v
pytest examples/roman_numerals -v

# All examples at once
pytest examples -v
```

The examples are live-SAS tests. When no SAS connection is available, their
project fixtures skip cleanly instead of failing during session startup.
