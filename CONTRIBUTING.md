# Contributing

## Development Setup

The project requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Tests And Checks

Run the internal SAS-free unit suite and code checks before opening a pull request:

```bash
pytest -c pytest.ini -v
python scripts/check_code.py
python -m build
python -m twine check dist/*
```

Package live-SAS tests require a configured SAS service. They are not part of
normal CI; follow [the release testing guide](docs/RELEASE_TESTING.md) when
changes affect saspy behavior or SAS syntax.

## Pull Requests

- Keep changes focused and explain user-visible behavior changes.
- Add or update internal unit tests for SAS-free package behavior.
- Use the `SASPYTEST_` prefix for datasets and macro variables created by tests.
- Do not commit credentials, `saspy` configuration files, or proprietary SAS
  JARs.
- Update documentation and `CHANGELOG.md` when changing public behavior.

Pull requests should pass the required CI checks before review.
