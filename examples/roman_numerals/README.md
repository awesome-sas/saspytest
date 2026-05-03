# Roman Numerals

This starter project shows how to test a small SAS macro and a SAS program with
`saspytest`.

## Layout

```text
 examples/roman_numerals/
├── macros/
│   └── number_to_roman.sas
├── programs/
│   └── convert_numbers.sas
├── testdata/
│   ├── saspytest_roman_expected.sas7bdat
│   └── saspytest_roman_input.sas7bdat
└── tests/
    ├── conftest.py
    ├── macros/
    │   └── test_number_to_roman.py
    └── programs/
        └── test_convert_numbers.py
```

## What It Demonstrates

- A reusable `%number_to_roman` macro with input validation
- A SAS program that reads demo input data and produces an output dataset
- Separate macro and program tests, mirroring `examples/hello_world/`
- Program validation against an expected SAS dataset stored in `testdata/`

## Validation Rules

The macro accepts integer values from `1` to `999`.

Invalid input writes a SAS error to the log with `%STR(ERR)OR:` and raises
`SYSCC` to at least `8`.

## Running The Example Tests

Run these tests explicitly because the repository's default `pytest` discovery is
limited to `tests/unit`.

If no live SAS connection is available, the suite skips cleanly during session
setup.

```bash
pytest examples/roman_numerals/tests/ -v
```

## Path Assumption

`programs/convert_numbers.sas` uses hardcoded relative paths to the macro and
input dataset files:

- `examples/roman_numerals/macros/number_to_roman.sas`
- `examples/roman_numerals/testdata/saspytest_roman_input.sas7bdat`

That keeps the demo easy to copy, but it also means the SAS session must be able
to read those paths from the repository root.
