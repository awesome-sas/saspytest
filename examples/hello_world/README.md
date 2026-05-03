# Hello World

This starter project shows the smallest useful `saspytest` setup for a SAS
macro and a SAS program.

## Layout

```text
examples/hello_world/
├── macros/
│   └── greetings.sas
├── programs/
│   └── greeter.sas
└── tests/
    ├── macros/
    │   └── test_greetings.py
    └── programs/
        └── test_greeter.py
```

## What It Demonstrates

- A reusable `%greetings` macro with basic input validation
- A simple SAS program that calls the macro
- Log-based assertions for warnings, notes, and greeting text
- Live-SAS tests that run against a configured SAS session

## Running The Example Tests

```bash
pytest examples/hello_world -v
```

If the local environment does not have a live SAS connection, the example
tests will be skipped during session setup.

## See Also

For a simpler flat layout where tests live beside the `.sas` files using
`*_test.py` naming, see [../hello_world_simple_layout/README.md](../hello_world_simple_layout/README.md).
