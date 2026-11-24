---
id: b02-plans-slice
status: pending
depends_on: [b01-contract]
touches:
  - src/deterministic_controls/checks/plans.py
  - src/deterministic_controls/checks/__init__.py
  - src/deterministic_controls/catalog/plans.schema.toml
  - src/deterministic_controls/catalog/plans.graph.toml
  - tests/test_plans.py
  - tests/fixtures/plans/**
  - plans/bootstrap/steps/b02-plans-slice.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Port the plan checks: `plans.schema` and `plans.graph`

This is the first vertical slice. It proves the CLI, the result contract and a failing bad fixture end to end. Read `plans/bootstrap/plan.md` first.

The source is `scripts/check_plan.py` of this repository. Keep that script. The library check must give the same pass or fail result on the same input.

## Change

- `checks/plans.py`: two check entries. `plans.schema` checks one step file at a time: required front matter (`id`, `status`, `depends_on`, `touches`, `lane`, `gate`), `id` equal to the file name stem, a valid `status`, a `done` step with `evidence`, a non-empty `gate`, and `goal.md` and `plan.md` in each plan folder. `plans.graph` checks the whole plan: unknown dependencies, cycles, overlapping `touches` of steps that can run together, and a shared serial `lane`. Skip `plans/for-each-plan` and `plans/archive`. Use stable rule IDs, for example `plans.schema.missing-gate`.
- `catalog/plans.schema.toml` and `catalog/plans.graph.toml`: the catalog files (status `advisory`, severity `error`).
- Parse front matter without a third-party package. Match the behavior of `scripts/ctx_common.py`.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md` (Markdown fixtures end in `.fixture`). `tests/fixtures/plans/` has one valid plan and one bad plan for each rule: missing `gate`, `done` without evidence, unknown dependency, cycle, overlapping `touches` of runnable steps, shared serial lane, `id` not equal to the file name. `tests/test_plans.py` proves for each bad plan the rule ID, the path, the severity and the exit code `1`. The valid plan passes with exit `0`.

A compatibility test runs `scripts/check_plan.py` on every fixture root and on this repository, and compares the pass or fail result with the library. They must agree.

## Do not change

- Files outside `touches`. The `gate` command. `scripts/check_plan.py`.

## Already done by earlier steps

- b00-secret-guard: the guard and the CI job.
- b01-contract: the package, the CLI, the `Finding` type, the manifest, the catalog loader and exit codes.

## Done when

- The gate passes. Each bad fixture fails for its own rule. The valid fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
