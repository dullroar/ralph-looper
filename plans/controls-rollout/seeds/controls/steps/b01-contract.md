---
id: b01-contract
status: pending
depends_on: [b00-secret-guard]
touches:
  - pyproject.toml
  - src/deterministic_controls/__init__.py
  - src/deterministic_controls/__main__.py
  - src/deterministic_controls/cli.py
  - src/deterministic_controls/core/**
  - src/deterministic_controls/catalog/__init__.py
  - tests/test_contract.py
  - tests/test_cli.py
  - plans/bootstrap/steps/b01-contract.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Build the package skeleton, the CLI, the manifest, the result contract and the catalog loader

Read `plans/bootstrap/plan.md` first. It holds the decisions that this step builds.

## Change

- `pyproject.toml`: project `deterministic-controls`, version `0.0.0`, `requires-python = ">=3.11"`, no run-time dependencies, source layout `src/`, package data for `catalog/*.toml` and `adopt/templates/*`.
- `src/deterministic_controls/cli.py` and `__main__.py`: the commands `list`, `check`, `explain`, `version` and `adopt` (it imports `deterministic_controls.adopt` lazily and calls `main(argv)`. If that module does not exist yet, it exits `2` with "not implemented". Step `b08` adds the module). `check` takes `--root`, `--profile quick|ci|full`, `--format text|json` and `--report FILE`.
- `src/deterministic_controls/core/`: the `Finding` type, the `Context` object (root, parameters, helpers for read-only file access), the result builder, the manifest reader (`tomllib`), the catalog loader, the policy (severity to failure), and the exit codes `0`, `1`, `2`, `3`. Document the check API in the module docstring of `core/api.py`: a check module has a function `entry(context)` that returns a list of `Finding`.
- The catalog loader reads `catalog/*.toml` with the keys `id`, `summary`, `version`, `status`, `severity`, `parameters`, `module`, `entry` and the optional boolean `mandatory`. A mandatory check runs in every profile, including `quick`. An attempt to disable it in the manifest is a configuration error (exit `2`). It does not import a check module. `check` imports the module of an enabled check only. The folder is empty except `__init__.py`. Tests use their own catalog fixtures through a loader argument.
- Result JSON: the fields in `plans/bootstrap/plan.md`. The output is deterministic. Two runs give the same JSON except `duration_ms`. Sort checks and findings. The tool never writes into the checked repository.
- Every test file adds `<repo>/src` to `sys.path` at its top.

## Tests

`tests/test_contract.py` and `tests/test_cli.py` prove each case below. A bad case must fail for the expected reason, with the expected exit code.

- An unknown check ID in the manifest: exit `2`.
- A bad manifest (unknown key, wrong `schema_version`) and a missing manifest: exit `2`, with a clear message.
- An internal exception in a check: exit `3`, and the check has status `error`. A crash never gives `0`.
- A mandatory check (status `required`) that is missing or skipped: failure.
- A check with `mandatory = true` runs in the `quick` profile. A manifest that disables it: exit `2`.
- Two runs give identical JSON except timing.
- A good manifest with a passing fake check: exit `0`. A fake check that returns a finding: exit `1`.
- `list` and `explain` read the catalog and import no check module.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b00-secret-guard: the secret guard, the hooks, the CI job and fresh indexes.

## Done when

- The gate passes. The tests above exist and pass.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
