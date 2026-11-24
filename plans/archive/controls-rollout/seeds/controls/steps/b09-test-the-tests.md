---
id: b09-test-the-tests
status: pending
depends_on: [b04-index-freshness, b05-markdown-links, b06-secrets, b07-forbidden-artifacts, b08-adoption-tools]
touches:
  - tests/test_mutation.py
  - tests/test_metamorphic.py
  - tests/test_fail_closed.py
  - tests/test_performance.py
  - tests/fixtures/mutation/**
  - docs/fault-matrix.md
  - controls.toml
  - scripts/check_context.py
  - scripts/AGENTS.md
  - .github/workflows/context.yml
  - plans/bootstrap/steps/b09-test-the-tests.md
lane: none
gate: python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m deterministic_controls check --root . --profile full --format json --report "${TMPDIR:-/tmp}/controls-b09.json" && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Test the tests: mutation, metamorphic, fail-closed, performance and the fault matrix

Read `plans/bootstrap/plan.md` first. A check that never fails proves nothing. This step proves that each check fails when it must, and that the whole tool fails closed.

## Change

- `tests/test_mutation.py` with `tests/fixtures/mutation/**`: start from a good repository (built at run time, or Markdown fixtures with the `.fixture` suffix). Apply one mutation at a time: remove a `gate`, rename a dependency, change a heading target, weaken a token pattern (use a copy of the secret check with a weakened pattern), and drop an index line. Each mutation must turn a pass into the expected failure, with the expected rule ID.
- `tests/test_metamorphic.py`: file order and repeated runs do not change the findings. Rename the root directory: the findings stay the same except for the path root.
- `tests/test_fail_closed.py`: an exception in a check, a timeout and an unreadable file give status `error` and a nonzero exit. A skipped mandatory check fails. A crash never gives `0`.
- `tests/test_performance.py`: build 100, 1,000 and 10,000 synthetic Markdown files in a temporary directory. Run the checks. Assert only a loose bound (10,000 files in under 120 seconds). Print the times.
- `docs/fault-matrix.md`: a table of faults (for each check: a missing file, an unreadable file, a malformed input, an internal error, a timeout), the expected result and the test that proves it. Add the measured times for 100, 1,000 and 10,000 files. Write in Simplified Technical English. Keep the links valid.
- `controls.toml`: enable all checks (`plans.schema`, `plans.graph`, `context.index-freshness`, `markdown.local-links`, `security.secrets`, `security.personal-data`, `repo.forbidden-artifacts`) in the profiles `ci` and `full`. Keep `quick` small and keep `security.secrets` in it.
- `scripts/check_context.py`: replace it with the shim that `adopt apply` writes (see `src/deterministic_controls/adopt/`). The shim keeps the old output lines and exit codes. In this repository it runs `python3 -m deterministic_controls check --root . --profile ci` with `PYTHONPATH=src`, because the package source is here. It does not use a cached environment in this repository. Keep a `Run me when:` line in its first 25 lines. Run `python3 scripts/build_indexes.py` to refresh `scripts/AGENTS.md`.
- `.github/workflows/context.yml`: the `check` job keeps its name and its steps. Make sure that every `uses:` action is pinned to a full 40-character SHA.
- The old template scripts (`check_plan.py`, `check_links.py`, `build_indexes.py`, `scan_secrets.py`, `ctx_common.py`) stay. The compatibility tests use them.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b00 to b03: the guard, the package, the CLI, the plan checks and the CI job.
- b04 to b07: the index, link, secret, personal-data and forbidden-artifact checks.
- b08-adoption-tools: the adoption tools and the shim writer.

## Done when

- The gate passes. This repository runs its own checks through the shim.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
