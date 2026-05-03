# saspytest — AI Agent Instructions

**saspytest** is a pytest support library for testing SAS programs via the [saspy](https://sassoftware.github.io/saspy/) Python interface. It provides assertions, fixtures, and session management for SAS-based CI/CD pipelines.

## Key Documentation

- Architecture & design decisions: [docs/PACKAGE_STRUCTURE.md](docs/PACKAGE_STRUCTURE.md)
- Development conventions: [docs/DEVELOPMENT_GUIDELINES.md](docs/DEVELOPMENT_GUIDELINES.md)
- API reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- Release testing (build, deploy, run on remote): [docs/RELEASE_TESTING.md](docs/RELEASE_TESTING.md)

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run internal unit tests (no SAS required)
pytest tests/unit/ -v

# Run integration tests (requires live SAS connection)
pytest tests/integration/ -v

# Check code style (black + flake8)
python scripts/check_code.py
```

## Project Layout

```
src/saspytest/      # Package source (src layout, PEP 420)
  session.py        # SAS session lifecycle, shared pool, pytest fixtures
  logs.py           # Log assertions (errors, warnings, patterns)
  datasets.py       # Dataset assertions (exists, row count, equality)
  macros.py         # Macro variable assertions
  files.py          # File upload/download, .sas file submission
  tests/unit/         # Internal mock-based tests — no SAS needed
  tests/integration/  # Package tests requiring a live SAS connection
docs/               # Documentation (link here, don't duplicate)
scripts/check_code.py  # Code quality runner (black + flake8)
```

## Code Style

- Formatter: **black**, line length **100**, targets py311–py313
- Linter: **flake8**
- Min Python: **3.11**
- Run `python scripts/check_code.py` before committing
- If you edit any Python file under `src/`, `tests/`, or `scripts/`, run `python scripts/check_code.py` before finishing the task

## Critical Conventions

### Naming — must follow these to get auto-cleanup from fixtures

| Item | Prefix | Example |
|------|--------|---------|
| Datasets (WORK library) | `SASPYTEST_` | `WORK.SASPYTEST_INPUT` |
| Macro variables | `SASPYTEST_` | `%let SASPYTEST_RESULT = ...` |
| SAS macros | `%SASPYTEST_` | `%macro SASPYTEST_HELPER;` |
| Assertion functions | `assert_` | `assert_no_errors()` |
| Private functions/fixtures | `_` prefix | `_create_session()` |

### Log Assertions — common pitfall

```python
# CORRECT: use result from submit()
result = sas.submit("...")
assert_no_errors(result['LOG'])

# WRONG: sas.saslog() contains cumulative session history, not just this call
assert_no_errors(sas.saslog())
```

### SAS Error/Warning Emission

Use `%STR()` to prevent SAS from treating ERROR/WARNING as keywords mid-submit:

```sas
%put %STR(ERR)OR: something went wrong;
%let syscc = %sysfunc(max(&syscc, 8));

%put %STR(WAR)NING: something is suspicious;
%let syscc = %sysfunc(max(&syscc, 4));
```

## Testing Patterns

- **Internal unit tests**: use the `mock_sas` fixture (MagicMock SAS session) — no SAS connection needed
- **Integration tests**: use the `sas_session` fixture (session-scoped, shared pool for speed)
- `clean_sas_workspace` fixture is auto-used — cleans `SASPYTEST_*` artifacts before/after each test
- Tests must be **independent** and **idempotent** (pass in any order)
- Use `@pytest.mark.integration` for tests requiring live SAS

### Live SAS Connection Failures

- Tests written by saspytest users that request a SAS session must fail during
  fixture setup when no SAS session is available.
- Example projects may catch SAS connection errors and convert them into
  `pytest.skip()` so they can be explored without a SAS installation.
- Do not add environment-variable switches or test-runner flags that turn a
  missing SAS session into a passing test run.

## Integration Testing Workflow

Building and testing against a real SAS server requires a manual deploy step — see [docs/RELEASE_TESTING.md](docs/RELEASE_TESTING.md) for the full build → transfer → install → run workflow.

### Devcontainer Live-SAS Tests

The devcontainer's `vscode` user reads saspy credentials from:

```text
/home/vscode/.authinfo
```

Provide this file once in the devcontainer with the saspy authinfo format. Do
not commit it or place credentials in tracked project files. From the repository
root, run the complete test suite with:

```bash
python scripts/run_tests.py
```

The runner executes the internal unit tests, package integration tests, and all
example suites. The package integration suite must execute passing tests for a
release gate; example projects may skip when no SAS connection is available.

## AI Skills

| Skill | Path | When to invoke |
|-------|------|----------------|
| `sas-tester` | [agents/skills/sas-tester/SKILL.md](agents/skills/sas-tester/SKILL.md) | Creating, maintaining, or running pytest-style integration tests for SAS code using `saspytest` |

See [docs/SKILLS.md](docs/SKILLS.md) for a human-readable overview of available skills.
