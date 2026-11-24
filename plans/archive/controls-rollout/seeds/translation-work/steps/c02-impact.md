---
id: c02-impact
status: pending
depends_on: [c01-synthetic-delta]
touches:
  - translation/rehearsal/impact.json
  - translation/rehearsal/fuzzy.jsonl
  - plans/v4-es-1/steps/c02-impact.md
lane: none
agent: script
run: python3 -I tools/rehearsal.py impact
gate: test -s translation/rehearsal/impact.json && test -s translation/rehearsal/fuzzy.jsonl && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: impact map and `msgmerge` on the rehearsal fixture

No model work. `tools/rehearsal.py impact` runs the impact map and `msgmerge` on the fixture of `c01-synthetic-delta`. It asserts that only the affected units are scheduled. It writes the schedule and the fuzzy entries that step `c03-delta-batch` sends to the Batch API.

## Do not change

- Files outside `touches`. The `gate`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
