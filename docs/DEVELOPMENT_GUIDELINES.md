# Development Guidelines for saspytest

These guidelines apply to contributors testing and maintaining saspytest itself.
Users writing tests for their SAS programs should start with the
[Getting Started guide](GETTING_STARTED.md).

## Test Structure and Organization

### Test Isolation and Idempotency
* Each test must be completely independent and produce the same result regardless of execution order
* Tests should not depend on side effects from other tests
* The `clean_sas_workspace` fixture automatically handles cleanup before and after tests that request `sas_session`
* Avoid creating dependencies between tests - each test should be self-contained

### Assertions Best Practices
* Each assertion should test a single, specific functionality
* Use descriptive assertion messages to aid debugging
* Prefer built-in saspytest assertions over custom SAS code checks
* Chain multiple simple assertions rather than creating one complex assertion

### Fixtures for Setup and Teardown
* Use the `sas_session` fixture for accessing the shared SAS session
* The `clean_sas_workspace` fixture is automatically applied to tests that request `sas_session`
* For custom setup/teardown, create additional fixtures as needed
* Use `@pytest.fixture` with appropriate scope (function, class, module, session)

The fixtures are provided by the `saspytest.session` pytest plugin and are auto-loaded when `saspytest` is installed.

## Naming Conventions

### Macro Variables
* **Prefix all test macro variables with `SASPYTEST_`** to avoid collisions
* Example: `SASPYTEST_COUNT`, `SASPYTEST_RESULT`, `SASPYTEST_STATUS`
* Macro variables with this prefix are automatically cleaned up by the fixture
* Do NOT manually delete SASPYTEST_* macro variables - the fixture handles this

### Macro Names
* **Prefix all test macros with `SASPYTEST_`** to avoid collisions
* Example: `%SASPYTEST_COUNT`, `%SASPYTEST_RESULT`, `%SASPYTEST_STATUS`


### Dataset Names
* **Prefix all test datasets with `SASPYTEST_`** to avoid name collisions
* Example: `SASPYTEST_INPUT`, `SASPYTEST_OUTPUT`, `SASPYTEST_CUSTOMERS`
* Always use the WORK library for temporary test datasets
* Datasets with this prefix are automatically cleaned up by the fixture
* Do NOT manually delete SASPYTEST_* datasets - the fixture handles this

### Test Function Names
* Follow pytest convention: prefix test functions with `test_`
* Use descriptive names that indicate what is being tested
* Example: `test_macro_variable_assignment`, `test_dataset_with_missing_values`

## Automatic Cleanup (Managed by Fixture)

### What Gets Cleaned Automatically
The `clean_sas_workspace` fixture automatically handles:
1. **SASPYTEST_* datasets** - Removed from WORK library before and after each test
2. **SASPYTEST_* macro variables** - Deleted from global scope before and after each test

**Note about SYSCC:** The System Completion Code (SYSCC) is a read/write automatic
SAS macro variable that reflects the condition code. It may remain elevated after
an earlier error even when later tests run clean code. Reset it explicitly when a
new scenario requires a clean condition code:

```sas
%let SYSCC = 0;
```

Workspace cleanup does not reset SYSCC or SYSERR. The conventional values used in
these guidelines are 0 for normal completion, 4 for warnings, and 8 or greater
for errors; the host-level return-code mapping is environment-specific. Tests
should verify SYSCC and SYSERR when testing error conditions rather than assuming
that artifact cleanup resets them.

### When Cleanup Occurs
* **Before each test** - `reset_test_state()` ensures a clean starting state
* **After each test** - `cleanup_test_artifacts()` removes test artifacts

### Manual Cleanup (When Needed)
* If you create datasets or macros WITHOUT the SASPYTEST_ prefix, you must clean them up manually
* Use `proc datasets` to delete datasets
* Use `%symdel` to delete macro variables
* Consider whether you really need non-prefixed names - using the prefix is recommended

## Error Handling

### System Error Codes
* **SYSCC** - System Completion Code (read/write automatic macro variable reflecting operation status)
* **SYSERR** - System Error Code (reflects last error condition)
* Tests that intentionally generate errors should verify SYSCC/SYSERR values
* Always check return codes after critical operations
* Conventional SYSCC values: 0 = normal completion, 4 = warning, 8+ = error

### Expected Errors and Warnings
* Use `assert_errors()` and `assert_warnings()` to verify expected error/warning conditions
* Add `@pytest.mark.filterwarnings("ignore::UserWarning")` to suppress saspy's Python warning when errors are expected
* Example:
  ```python
  @pytest.mark.filterwarnings("ignore::UserWarning")
  def test_error_condition(sas_session):
      result = sas_session.submit("data SASPYTEST_BAD; set nonexistent; run;")
      assert_errors(result['LOG'], ["does not exist"])
  ```

### Custom Error Messages in SAS
Follow the custom error and warning guidance in [the user guide](USAGE.md#writing-custom-sas-errors-and-warnings):
* **NOTES**: `%put NOTE: message;`
* **WARNINGS**: `%put %STR(WAR)NING: message;` + `%let syscc = %sysfunc(max(&syscc,4));`
* **ERRORS**: `%put %STR(ERR)OR: message;` + `%let syscc = %sysfunc(max(&syscc,8));`

## Test Design Patterns

### Minimal Test Setup
* Let the fixture handle standard cleanup - don't repeat it in each test
* Focus test code on the specific scenario being tested
* Keep tests simple and readable

### Example Test Structure
```python
def test_something(sas_session):
    """Test description."""
    sas = sas_session

    # No manual cleanup needed - fixture handles it!

    # Create test data with proper prefix
    result = sas.submit("""
        data SASPYTEST_INPUT;
            input x y z;
            datalines;
        1 2 3
        4 5 6
        ;
        run;
    """)
    
    # Verify results
    assert_no_errors(result['LOG'])
    assert_dataset_exists(sas, "SASPYTEST_INPUT")
    assert_record_count(sas, "SASPYTEST_INPUT", 2)

    # No manual cleanup needed - fixture handles it!
```

### Testing Multiple Scenarios
* Create separate test functions for different scenarios
* Use pytest parametrization for testing variations of the same logic
* Example:
  ```python
  @pytest.mark.parametrize("input_val,expected", [
      (1, 2),
      (5, 10),
      (10, 20)
  ])
  def test_doubling(sas_session, input_val, expected):
      # Test implementation
  ```

## Log Handling

### Using submit() Return Values
* Always capture the return value from `sas.submit()`: `result = sas.submit("...")`
* Use `result['LOG']` for assertions - it contains ONLY that submission's log
* **Never use `sas.saslog()`** for assertions - it contains cumulative session history

### Log Assertions
* Use `assert_no_errors(result['LOG'])` to verify no errors occurred
* Use `assert_no_warnings(result['LOG'])` to verify no warnings occurred
* Use `assert_log_contains()` for checking specific messages
* See [the API Reference](API_REFERENCE.md) for detailed assertion documentation

## Performance Considerations

### Session Reuse
* All tests share a single SAS session (session scope)
* This significantly improves test execution speed
* The fixture ensures proper isolation between tests

### Dataset Efficiency
* Use small datasets in tests - just enough data to validate logic
* Prefer WORK library over permanent libraries
* Clean up is automatic for SASPYTEST_* datasets

### Minimize SAS Submissions
* Combine related SAS code into single submit() calls when possible
* Each submit() incurs communication overhead
* Balance readability with performance

## Documentation

### Test Docstrings
* Test functions should have a docstring explaining what they test, especially when the scenario is not obvious from the test name
* Format: `"""Test description of what is being validated."""`
* Be specific about the scenario being tested

### Comments in Test Code
* Comment complex logic or non-obvious assertions
* Explain WHY something is tested, not just WHAT is tested
* Use comments to mark test sections (setup, execution, verification)

## Common Pitfalls to Avoid

1. **Not using SASPYTEST_ prefix** - Leads to naming collisions and failed cleanup
2. **Using sas.saslog() for assertions** - Contains cumulative history, not current submission
3. **Creating test dependencies** - Each test must be independent
4. **Forgetting to check error codes** - Always verify no errors in critical operations
5. **Over-complicated tests** - Keep tests simple and focused on one thing
6. **Hardcoding paths** - Use relative paths or fixtures for file operations
7. **Not documenting test purpose** - Always include clear docstrings

## Advanced Topics

### Custom Fixtures
Create additional fixtures for specialized setup:
```python
@pytest.fixture
def sample_customer_data(sas_session):
    """Provide sample customer dataset for tests."""
    sas_session.submit("""
        data SASPYTEST_CUSTOMERS;
            input id name $ balance;
            datalines;
        1 Alice 1000
        2 Bob 2000
        ;
        run;
    """)
    yield
    # Automatic cleanup by clean_sas_workspace
```

### Manual State Reset
If you need to reset state mid-test:
```python
from saspytest import reset_test_state

def test_multiple_scenarios(sas_session):
    # Scenario 1
    # ... test code ...

    # Reset for scenario 2
    reset_test_state(sas_session)

    # Scenario 2
    # ... test code ...
```

### Debugging Failed Tests
* Run pytest with `-v` for verbose output
* Use `-s` to see print statements and SAS log output
* Use `%put` statements in SAS code to debug macro values
* Check SYSCC and SYSERR values when errors occur
