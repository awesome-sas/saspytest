# Hello World — Simple Layout

This starter project shows the smallest possible `saspytest` setup using the
**simple layout** pattern: SAS source files and their tests live in the same
directory, with tests named `*_test.py`.

## Layout

```text
examples/hello_world_simple_layout/
├── pytest.ini
├── greetings.sas
├── greetings_test.py
├── greeter.sas
└── greeter_test.py
```

## What It Demonstrates

- The `*_test.py` side-by-side naming convention for small projects
- Tests referencing their SAS file with `Path(__file__).resolve().parent / "file.sas"`
- A `pytest.ini` that enables the `*_test.py` discovery pattern

## When To Use This Layout

Use this layout when:
- You have a small number of SAS files
- Each test file naturally lives next to the SAS file it covers
- You don't need a separate `tests/` tree

For larger projects with many macros and programs spread across subdirectories,
see [../hello_world/README.md](../hello_world/README.md) for the separated layout.

## Running The Example Tests

```bash
pytest examples/hello_world_simple_layout -v
```

If the local environment does not have a live SAS connection, the example
tests will be skipped during session setup.
