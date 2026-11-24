---
id: 08-record-pin
status: done
depends_on: [07-release-controls]
touches:
  - plans/controls-rollout/pins.tsv
  - plans/controls-rollout/steps/08-record-pin.md
lane: none
agent: script
run: bash plans/controls-rollout/pin.sh v0.1.0
gate: python3 scripts/check_records.py plans/controls-rollout/pins.tsv --min-rows 1 --match 'commit=[0-9a-f]{40}' && grep -qP '\tv0\.1\.0\t[0-9a-f]{40}$' plans/controls-rollout/pins.tsv && python3 scripts/check_context.py && git diff --check
claimed_by: script cli-default
claimed_at: "2026-11-24T01:38:48Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Record the v0.1.0 commit in pins.tsv

Script step. The driver runs `run` and then the gate. No model is used.

`pin.sh` resolves the tag on the remote and writes the commit to `pins.tsv`. It fails if the tag does not exist.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
