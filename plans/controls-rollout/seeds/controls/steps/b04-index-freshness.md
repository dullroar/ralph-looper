---
id: b04-index-freshness
status: pending
depends_on: [b03-self-ci]
touches:
  - src/deterministic_controls/checks/index_freshness.py
  - src/deterministic_controls/catalog/context.index-freshness.toml
  - tests/test_index_freshness.py
  - tests/fixtures/index_freshness/**
  - plans/bootstrap/steps/b04-index-freshness.md
lane: none
agent: local
fallback: claude
gate: python3 -m unittest discover -s tests -p 'test_index_freshness.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Port `context.index-freshness`, without writes

Read `plans/bootstrap/plan.md` first. The source is `scripts/build_indexes.py --check` of this repository. Keep that script. The library check must never write a file.

## Change

- `checks/index_freshness.py`: a function `entry(context)`. Compute the expected text between the `BEGIN GENERATED INDEX` and `END GENERATED INDEX` markers of `memory/AGENTS.md`, `plans/AGENTS.md` and `scripts/AGENTS.md`, the same way `build_indexes.py` does. Compare it with the file. Do not write. Return one finding for each stale index, a finding for a missing marker, and a finding for a memory, plan or script that has no `gist` or `Run me when:` line. Use stable rule IDs: `context.index-freshness.stale`, `.missing-markers`, `.missing-gist`.
- `catalog/context.index-freshness.toml`: id `context.index-freshness`, status `advisory`, severity `error`, `module = "deterministic_controls.checks.index_freshness"`, `entry = "entry"`.
- Look at `checks/plans.py` and `catalog/plans.schema.toml` for the pattern. Use the `Finding` type of `core/`.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md` (Markdown fixtures end in `.fixture`). `tests/fixtures/index_freshness/` has a good repository (fresh indexes) and bad repositories: a stale `plans/AGENTS.md`, a stale `scripts/AGENTS.md`, a missing marker, a memory without a `gist`, a script without a `Run me when:` line. `tests/test_index_freshness.py` proves for each bad fixture the rule ID, the path and the exit code `1`, and proves that the good fixture passes. A test proves that the check does not change the modification time or the content of any fixture file. A compatibility test runs `scripts/build_indexes.py --check` on each fixture and compares the pass or fail result.

## Do not change

- Files outside `touches`. The `gate` command. `scripts/build_indexes.py`.

## Already done by earlier steps

- b01 to b03: the package, the CLI, the catalog loader, the plan checks and the CI job.

## Done when

- The gate passes. Each bad fixture fails for its own rule. The good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
