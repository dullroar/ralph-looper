---
id: 09-runner-adopts-controls
status: pending
depends_on: [08-record-pin]
touches:
  - scripts/check_context.py
  - scripts/controls-requirements.txt
  - scripts/AGENTS.md
  - controls.toml
  - .github/workflows/context.yml
  - AGENTS.md
  - docs/controls-adoption.md
  - plans/controls-rollout/steps/09-runner-adopts-controls.md
lane: none
gate: python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && bash tests/run.sh && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Wire ralph-looper to the pinned library

This repository is the runner. It must dogfood the controls. Source phase 6.

## Do

1. Install the pin from `pins.tsv` in a temporary virtual environment and run `python3 -m deterministic_controls adopt plan --root .`. Review the diff. Run `adopt apply`.
2. Keep `scripts/check_records.py` and `scripts/build_indexes.py`. They are not replaced by the library.
3. In `.github/workflows/context.yml`, keep the `context` job name. Add a second job `runner-tests` that runs `bash tests/run.sh`, `python3 tests/test_fanout.py`, `python3 tests/test_report.py` and `python3 tests/test_check_records.py`. Both jobs: `permissions: contents: read`, actions pinned to full SHAs, no path filters, no secrets.
4. Add the controls rules to `AGENTS.md`: CI runs the controls in all cases; do not change the controls, the pin, `controls.toml` or the workflows to make an unrelated task pass.
5. Write `docs/controls-adoption.md` with the receipt from `adopt receipt` and the rollback command.
6. Probe: in a temporary copy, remove the `gate` from a step of `plans/runner-routing` and confirm that `python3 scripts/check_context.py` fails with the `plans.schema` rule ID. Record it below.

The shim uses the library's cache environment for the pinned commit. Later gates in this plan call the same shim, so the cache must build on this host. Record the first-run and cached-run times below.

## Results

(fill in)

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
