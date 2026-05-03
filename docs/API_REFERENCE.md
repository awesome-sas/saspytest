# saspytest API Reference

Quick reference for all supported functions and pytest fixtures available in the
saspytest package.

## Import

```python
from saspytest import (
    get_sas_session,
    close_sas_session,
    reset_sas_session,
    create_new_sas_session,
    reset_test_state,
    cleanup_test_artifacts,
    upload_file,
    download_file,
    submit_sas_file,
    assert_macro_value,
    assert_macro_exists,
    assert_log_contains,
    assert_log_not_contains,
    assert_no_errors,
    assert_no_warnings,
    assert_errors,
    assert_warnings,
    assert_dataset_exists,
    assert_dataset_not_exists,
    assert_library_exists,
    assert_record_count,
    assert_columns_exist,
    assert_datasets_equal,
    get_dataset_as_df,
)
```

## Compatibility And Deprecation Policy

The names re-exported from `saspytest` and the documented pytest fixtures are the
supported public API and follow semantic versioning:

- Backward-compatible additions and behavior changes use a minor release.
- Bug fixes and documentation-only changes use a patch release.
- Breaking changes use a major release.
- Deprecated public behavior remains documented and continues to work for at
  least one minor release before removal in a later major release. A deprecation
  notice will identify the replacement and removal version.

Imports from private modules or names beginning with `_` are implementation
details and are not covered by this policy.

The installed distribution version is available as `saspytest.__version__`.
Compatibility details and known limitations are maintained in the
[Support Policy](SUPPORT.md).

## Common Input Conventions

Dataset, library, column, and macro-variable names must be conventional
ASCII SAS V7 identifiers: 1-32 characters, starting with a letter or `_`, and
containing only letters, digits, and `_`. Library references are limited to
eight characters. Pass macro-variable names without the `&` prefix. Name
literals, qualified names containing `.`, spaces, and other special characters
are rejected with `ValueError`; the helpers do not implement SAS name-literal
escaping.

SAS treats these identifiers case-insensitively. saspytest preserves the text
provided by the caller when constructing error messages and SAS code. Column
existence checks compare names case-insensitively. Unless a function says
otherwise, string matching is case-sensitive and does not strip whitespace.

## Session Management

Located in `saspytest.session`

When `saspytest` is installed, pytest auto-loads `saspytest.session` through the
package's `pytest11` entry point, so the fixtures below are available without
manual imports.

### Fixtures

#### `sas_session`
**Type:** pytest fixture (scope="function")  
**Purpose:** Provides the shared SAS session managed at session scope.

```python
def test_example(sas_session):
    result = sas_session.submit("data SASPYTEST_EXAMPLE; x=1; run;")
```

#### `clean_sas_workspace`
**Type:** pytest fixture (autouse=True)  
**Purpose:** Automatically cleans test artifacts before and after each test.

For tests that request `sas_session`, removes `SASPYTEST_*` datasets from the
WORK library and `SASPYTEST_*` global macro variables via `reset_test_state`.

#### `require_new_sas_session`
**Type:** pytest fixture (scope="function")  
**Purpose:** Forces creation of a brand-new SAS session for tests that need a clean engine state.

```python
def test_requires_fresh_session(require_new_sas_session):
    result = require_new_sas_session.submit("data SASPYTEST_FRESH; x=1; run;")
```

### Session Configuration Resolution

`sascfg_personal.py` is saspy's configuration file. It is different from
`saspytest_config.py`, which is the saspytest-specific filename used for local
automatic discovery.

When creating a session, `saspytest` resolves the saspy configuration in the following order:

1. **`SASPY_CONFIG` / `SASPY_CFGNAME` environment variables** — if set, passed directly to
   `saspy.SASsession(cfgfile=..., cfgname=...)`.
2. **`saspytest_config.py` file discovery** — if no environment variables are set, the working
   directory and all parent directories are searched for a file named `saspytest_config.py`. If found,
   its path is passed as `cfgfile`.
3. **saspy default resolution** — if neither of the above applies, `saspy.SASsession()` is called
   with no arguments and saspy uses its own config lookup.

### Functions

#### `get_sas_session()`
Returns the shared SAS session, creating it if needed.

```python
sas = get_sas_session()
```

#### `close_sas_session()`
Closes the shared SAS session.

```python
close_sas_session()
```

#### `reset_sas_session()`
Close the current shared session (if any) and create a new SAS session.

```python
sas = reset_sas_session()
```

#### `create_new_sas_session()`
Create an independent SAS session without replacing the shared session. The
caller owns the new session and must call `endsas()` when finished.

```python
isolated_sas = create_new_sas_session()
try:
    isolated_sas.submit("data SASPYTEST_ISOLATED; x = 1; run;")
finally:
    isolated_sas.endsas()
```

#### `reset_test_state(sas)`
Remove saspytest test artifacts for test isolation.

Removes all SASPYTEST_* datasets from the WORK library and deletes all SASPYTEST_* global macro variables.
Called automatically by the `clean_sas_workspace` fixture before and after each test.

**Note:** This cleanup does not reset `SYSCC` or `SYSERR`. `SYSCC` is a read/write
automatic SAS macro variable and can be reset explicitly when needed:

```sas
%let SYSCC = 0;
```

`SYSERR` reports the last SAS step's error condition. Both variables reflect SAS
session state and are outside the scope of saspytest workspace cleanup.

```python
# Manual reset if needed mid-test
reset_test_state(sas)
```

#### `cleanup_test_artifacts(sas)`
Clean up test artifacts after test execution.

Alias for `reset_test_state()` for semantic clarity in teardown contexts.
Called automatically by the fixture after each test.

```python
cleanup_test_artifacts(sas)
```

---

## File Handling

Located in `saspytest.files`

#### `upload_file(sas, local_path, remote_path, overwrite=True)`
Upload a file to the SAS server.

**Returns:** `bool` - True if successful

The underlying `sas.upload()` result is interpreted as follows: `None` means
success, a dictionary returns the truthiness of its case-sensitive `Success`
value, and any other result or a missing/false `Success` value means failure.
Exceptions from saspy are propagated. The `overwrite` value is passed through
unchanged.

```python
success = upload_file(sas, "/tmp/data.csv", "/tmp/remote.csv")
```

#### `download_file(sas, local_path, remote_path, overwrite=True)`
Download a file from the SAS server.

**Returns:** `bool` - True if successful

`download_file()` applies the same result rules as `upload_file()`: `None` is
success, a dictionary is successful only when its `Success` value is truthy,
and all other results are failure. Exceptions from saspy are propagated.

```python
success = download_file(sas, "/tmp/local.csv", "/tmp/remote.csv")
```

#### `submit_sas_file(sas, local_path)`
Read a local file as UTF-8 and submit its contents to the SAS session. The path
must identify an existing regular file; the function does not enforce a `.sas`
extension. Empty files are accepted.

**Returns:** `Dict[str, str]` - saspy `submit()` result with `LOG` and `LST` keys

**Raises:** `FileNotFoundError` if the path is missing or is not a regular file;
`UnicodeDecodeError` for non-UTF-8 content. Exceptions from `Path.read_text()`
and `sas.submit()` otherwise propagate unchanged.

The return value is the exact object returned by `sas.submit()`, without
normalization or copying.

```python
def test_submit_program_file(sas_session, tmp_path):
    program = tmp_path / "etl.sas"
    program.write_text("data work.SASPYTEST_ETL; x = 1; run;", encoding="utf-8")

    result = submit_sas_file(sas_session, program)
    assert_no_errors(result["LOG"])
```

---

## Macro Assertions

Located in `saspytest.macros`

#### `assert_macro_value(sas, macro_name, expected_value, msg=None)`
Assert that a macro variable has the expected value.

Both the value returned by `sas.symget()` and `expected_value` are converted to
strings and stripped at both ends before comparison. An undefined value is
therefore compared as the string `"None"`.

```python
assert_macro_value(sas, "myvar", "expected")
```

#### `assert_macro_exists(sas, macro_name, msg=None)`
Assert that a macro variable is defined.

The assertion passes when `sas.symget()` returns any non-`None`, non-empty
value. Whitespace-only values count as existing; the value is not stripped for
this check.

```python
assert_macro_exists(sas, "myvar")
```

---

## Log Assertions

Located in `saspytest.logs`

#### `assert_log_contains(log, pattern, regex=False, msg=None)`
Assert that the log contains a pattern.

With `regex=False`, this is a case-sensitive literal substring search. With
`regex=True`, it calls `re.search()` with Python's default flags, so invalid
regular expressions raise `re.error` and matching is case-sensitive unless the
pattern supplies its own flags.

```python
result = sas.submit("data SASPYTEST_EXAMPLE; x=1; run;")
assert_log_contains(result['LOG'], "DATA statement")
```

#### `assert_log_not_contains(log, pattern, regex=False, msg=None)`
Assert that the log does NOT contain a pattern.

It uses the same literal-versus-regex and case-sensitivity rules as
`assert_log_contains()`.

```python
assert_log_not_contains(result['LOG'], "ERROR")
```

#### `assert_no_errors(log, msg=None)`
Assert that the log contains no ERROR messages.

The check is case-insensitive and recognizes `ERROR:` and numbered SAS markers
such as `ERROR 180-322:`. It does not require the message to start a line.

```python
result = sas.submit("data SASPYTEST_EXAMPLE; x=1; run;")
assert_no_errors(result['LOG'])
```

#### `assert_no_warnings(log, msg=None)`
Assert that the log contains no WARNING messages.

The check is case-insensitive and recognizes `WARNING:` and numbered SAS markers
such as `WARNING 123:`. It does not require the message to start a line.

```python
assert_no_warnings(result['LOG'])
```

#### `assert_errors(log, expected_messages, msg=None)`
Assert that the log contains expected ERROR messages.

Use when testing error conditions to verify specific errors occur.
Prints found errors to pytest output for visibility.

Error messages are extracted one line at a time using a case-insensitive
`ERROR:` or numbered SAS marker. Each expected message must be a case-insensitive
substring of at least one extracted error. An empty expected-message list
passes if at least one error exists and fails if none exists. A supplied `msg`
replaces the generated message on every assertion failure; successful calls
still print the discovered errors.

**Note:** Add `@pytest.mark.filterwarnings("ignore::UserWarning")` to test to suppress SASpy's warning during submit().

```python
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_error_case(sas_session):
    result = sas_session.submit("proc print data=nonexistent; run;")
    assert_errors(result['LOG'], ["nonexistent"])
```

#### `assert_warnings(log, expected_messages, msg=None)`
Assert that the log contains expected WARNING messages.

Use when testing warning conditions to verify specific warnings occur.
Prints found warnings to pytest output for visibility.

Warnings follow the same rules as `assert_errors()`, using the `WARNING:` or
numbered SAS marker and warning messages. A supplied `msg` replaces the generated failure
message, while successful calls print the discovered warnings.

```python
def test_warning_case(sas_session):
    result = sas_session.submit("...code generating warning...")
    assert_warnings(result['LOG'], ["expected warning text"])
```

---

## Dataset Assertions

Located in `saspytest.datasets`

Dataset assertions perform an explicit existence check before reading dataset
metadata. A missing dataset, missing library metadata, or missing result from a
failed SAS metadata operation raises `AssertionError` rather than treating the
result as an empty dataset or producing an incidental conversion error. The
helpers use per-call `SASPYTEST_`-prefixed macro variables and WORK datasets;
the `clean_sas_workspace` fixture removes these artifacts between tests.

#### `assert_dataset_exists(sas, dataset, libref="WORK", msg=None)`
Assert that a dataset exists.

```python
assert_dataset_exists(sas, "mydata")
assert_dataset_exists(sas, "mydata", libref="MYLIB")
```

#### `assert_dataset_not_exists(sas, dataset, libref="WORK", msg=None)`
Assert that a dataset does NOT exist.

```python
assert_dataset_not_exists(sas, "temp")
```

#### `assert_library_exists(sas, libref, msg=None)`
Assert that a library is assigned.

```python
assert_library_exists(sas, "WORK")
```

#### `assert_record_count(sas, dataset, expected_count, libref="WORK", msg=None)`
Assert the number of observations in a dataset.

```python
assert_record_count(sas, "mydata", 100)
```

#### `assert_columns_exist(sas, dataset, columns, libref="WORK", msg=None)`
Assert that specific columns exist in a dataset.

```python
assert_columns_exist(sas, "mydata", ["id", "name", "age"])
```

#### `assert_datasets_equal(sas, dataset1, dataset2, libref1="WORK", libref2="WORK", msg=None)`
Assert that two datasets are equal using PROC COMPARE.

The assertion passes only when the submitted `PROC COMPARE` sets `SYSINFO` to
exactly `0`. Any non-zero value fails the assertion, including differences in
dataset metadata or labels, variable presence or attributes, observation data,
or comparison/BY-group structure reported by SAS. The helper does not ignore
any PROC COMPARE difference categories.

```python
assert_datasets_equal(sas, "SASPYTEST_ORIGINAL", "SASPYTEST_COPY")
```

#### `get_dataset_as_df(sas, dataset, libref="WORK")`
Get a SAS dataset as a pandas DataFrame.

**Returns:** `pandas.DataFrame`

```python
df = get_dataset_as_df(sas, "mydata")
assert len(df) == 100
assert df["age"].mean() > 18
```

---

## Best Practices

### Always Use Isolated Logs

```python
# ✓ CORRECT - Isolated log
result = sas.submit("data SASPYTEST_LOG_OK; x=1; run;")
assert_no_errors(result['LOG'])

# ✗ WRONG - Cumulative session log
sas.submit("data SASPYTEST_LOG_OK; x=1; run;")
assert_no_errors(sas.saslog())  # Includes all previous submissions!
```

### Custom SAS Errors and Warnings

```sas
/* Errors */
%PUT %STR(ERR)OR: Dataset not found;
%let syscc = %sysfunc(max(&syscc,8));

/* Warnings */
%PUT %STR(WAR)NING: Missing values detected;
%let syscc = %sysfunc(max(&syscc,4));

/* Notes */
%PUT NOTE: Processing started;
```
