# Changelog

User-visible changes to `saspytest` are recorded here and in GitHub Releases.

## Unreleased
- Add optional keyword-only `criterion` to `assert_datasets_equal` for absolute
  numeric tolerance while preserving default comparison behavior.
- Include PROC COMPARE mismatch diagnostics in dataset comparison failures,
  including failures with custom messages.

## 1.0.0 - 2026-09-07
- initial release