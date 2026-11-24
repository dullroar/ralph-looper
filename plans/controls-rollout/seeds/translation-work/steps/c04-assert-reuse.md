---
id: c04-assert-reuse
status: pending
depends_on: [c03-delta-batch]
touches:
  - translation/rehearsal/reuse-report.md
  - plans/v4-es-1/steps/c04-assert-reuse.md
lane: none
agent: script
run: python3 -I tools/rehearsal.py import-assert
gate: test -s translation/rehearsal/reuse-report.md && grep -q '^model-calls-for-reused-units: 0$' translation/rehearsal/reuse-report.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: import the drafts, prove the reuse and the gates

No model work. `tools/rehearsal.py import-assert` imports `translation/rehearsal/drafts.jsonl` with `tools/translate.py --drafts` on the fixture (all checks run). It asserts that untouched Spanish was reused with no model call, and that every code, graph, book and link gate that the change reaches ran. It writes `translation/rehearsal/reuse-report.md`, which has the line `model-calls-for-reused-units: 0`.

## Do not change

- Files outside `touches`. The `gate`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
