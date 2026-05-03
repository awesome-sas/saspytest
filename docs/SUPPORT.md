# Support Policy

## Version 1.0

The supported public API is the set of functions re-exported from
`saspytest`, the documented pytest fixtures, and `saspytest.__version__`.
Imports from private modules or names beginning with `_` are implementation
details.

## Python

The package metadata requires Python 3.11 or later. Version 1.0 is tested in CI
on Python 3.11, 3.12, and 3.13. Newer Python versions may work, but they are
best-effort until they are added to the CI matrix.

## SAS And saspy

- `saspy>=5.0.0` is required.
- `pandas>=3.0.0` is required because `get_dataset_as_df()` is part of the stable
  public API and returns a pandas DataFrame. This is a saspytest requirement;
  pandas is not required by saspy's base installation.
- The target SAS deployment must be reachable through a saspy-supported
  configuration. saspytest does not provide or pin a SAS server version.
- IOM connections require Java and the proprietary SAS client components
  required by saspy. These components are not bundled by saspytest.
- The live-SAS release gate must record the tested SAS deployment, saspy
  version, Python version, and connection mode.

## Known Limitations

- SAS-dependent tests require a live SAS service, network access, and valid
  credentials.
- The repository's default unit tests use mocks and do not validate SAS server
  behavior. The live-SAS suite is an external release gate.
- Dataset, library, column, and macro names are restricted to conventional ASCII
  SAS V7 identifiers. SAS name literals are not supported.
- The shared session is process-global and is reused by tests that request the
  `sas_session` fixture.
- Automatic cleanup covers only `SASPYTEST_*` datasets in `WORK` and global
  `SASPYTEST_*` macro variables.

## Upgrading To 1.0

Version 1.0 is the first stable API contract. Code should import supported
helpers from `saspytest` and use the documented fixtures. Pre-1.0 imports from
private modules or undocumented names have no compatibility guarantee.
