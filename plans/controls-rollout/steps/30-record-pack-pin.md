---
id: 30-record-pack-pin
status: pending
depends_on: [29-release-translation-pack]
touches:
  - plans/controls-rollout/pins.tsv
  - plans/controls-rollout/steps/30-record-pack-pin.md
lane: none
agent: script
run: bash plans/controls-rollout/pin.sh v0.2.0
gate: grep -qP '\tv0\.2\.0\t[0-9a-f]{40}$' plans/controls-rollout/pins.tsv && python3 scripts/check_records.py plans/controls-rollout/pins.tsv --min-rows 2 --match 'commit=[0-9a-f]{40}' && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Record the v0.2.0 commit in pins.tsv

Script step. The driver runs `run` and then the gate. No model is used.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
