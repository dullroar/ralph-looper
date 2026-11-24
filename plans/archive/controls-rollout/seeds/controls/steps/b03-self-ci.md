---
id: b03-self-ci
status: pending
depends_on: [b02-plans-slice]
touches:
  - .github/workflows/controls.yml
  - controls.toml
  - tests/test_consumer.py
  - tests/fixtures/consumer/**
  - plans/bootstrap/steps/b03-self-ci.md
lane: none
gate: python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m deterministic_controls check --root . --profile ci --format json --report "${TMPDIR:-/tmp}/controls-b03.json" && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the CI workflow for this repository and a consumer fixture

Read `plans/bootstrap/plan.md` first. After this step, a bad plan fails in two places: the unit tests and the CI check of the repository itself.

The gate runs the package from the source tree with `PYTHONPATH=src`. The package is not installed in the repository. The workflow does the same: it sets `PYTHONPATH: src` in the `env` of the job.

## Change

- `controls.toml`: `schema_version = 1`, profile `ci`, enable `plans.schema` and `plans.graph`. No commands.
- `.github/workflows/controls.yml`: runs on `pull_request`, on `push` to `main` and on `workflow_dispatch`. No path filters. `permissions: contents: read`. Pin every action to a full 40-character commit SHA, with the tag in a trailing comment. Find the SHAs with `git ls-remote --tags` on the action repositories. It runs the unit tests, then `python3 -m deterministic_controls check --root . --profile ci --format json --report "$RUNNER_TEMP/controls.json"`, then uploads the report with `actions/upload-artifact`. It runs the check with `if: always()` for the upload only. The check itself must fail the job on any nonzero exit.
- Do not change `.github/workflows/context.yml`. Keep the template `context` job there until step `b09`.
- Follow the fixture rule in `plans/bootstrap/plan.md` (Markdown fixtures end in `.fixture`). `tests/fixtures/consumer/good/` and `tests/fixtures/consumer/bad/`: two small consumer repositories with a `controls.toml`, a `plans/` tree and `.git`-free files. The bad one has a plan without a `gate`.
- `tests/test_consumer.py`: install the package from this worktree into a temporary virtual environment (`python3 -m venv`, then `pip install --no-deps --no-build-isolation .` or the best offline option) and run the CLI on the good fixture (exit `0`) and the bad fixture (exit `1`, rule ID `plans.schema.missing-gate` or the ID that `b02` chose). Skip with a clear reason, and not a pass, if the environment cannot be built offline: the test then has status `skipped` with the message "no build tool". Also test the workflow text: no `uses:` line without a 40-character SHA, `permissions: contents: read` is present, there is no `paths:` filter.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b01-contract: CLI and core. b02-plans-slice: the plan checks and fixtures.

## Done when

- The gate passes. A bad plan fails in the unit tests and in the consumer test.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
