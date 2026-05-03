# AI Agent Skills

This page documents the AI agent skills available in this repository. Skills contain domain-specific instructions that an AI coding assistant can load on demand when performing a task.

Skills live under `agents/skills/<name>/SKILL.md`.

---

## sas-tester

**File:** [agents/skills/sas-tester/SKILL.md](../agents/skills/sas-tester/SKILL.md)

**When to invoke:** creating, maintaining, or running pytest-style integration tests for SAS code using `saspytest`.

### What the skill covers

- Package import conventions
- **Session configuration** — how `saspytest` discovers a saspy config:
  1. `SASPY_CONFIG` / `SASPY_CFGNAME` environment variables (CI/CD)
   2. `saspytest_config.py` auto-discovery (walks CWD and parent directories)
  3. Default saspy resolution
- Project layout recommendations (simple side-by-side vs. separate `tests/` tree) and `pytest.ini` configuration
- `conftest.py` pattern for advanced session lifecycle control (optional; most projects don't need it)
- Naming conventions (`SASPYTEST_` prefix for auto-cleanup)
- Log assertion rules (`result["LOG"]`, not `sas.saslog()`)
- Fixture reference (`sas_session`, `clean_sas_workspace`, `require_new_sas_session`)
- Full assertion API (log, dataset, macro, library, file utilities)
- Test patterns (simple side-by-side, macro, program, dataset comparison, parametrized, DataFrame)
- How to run tests
- Common pitfalls

### Quick reference: session configuration

| Priority | Source | Notes |
|---|---|---|
| 1 | `SASPY_CONFIG` / `SASPY_CFGNAME` env vars | Recommended for CI/CD |
| 2 | `saspytest_config.py` in CWD or any parent | Drop-in; no env vars needed |
| 3 | Default saspy resolution | saspy's own config lookup |

Place a `saspytest_config.py` in the directory where you invoke pytest or one of
its ancestors and `saspytest` picks it up automatically — no environment
variable configuration needed.
