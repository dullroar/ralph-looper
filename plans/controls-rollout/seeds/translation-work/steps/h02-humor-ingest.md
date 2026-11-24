---
id: h02-humor-ingest
status: pending
depends_on: [h01-native-humor, j05-ingest, g02-lane-requests]
touches:
  - translation/humor-decisions.jsonl
  - review/humor-findings.jsonl
  - plans/v4-es-1/steps/fix-humor-*.md
  - plans/v4-es-1/steps/h02-humor-ingest.md
lane: none
agent: script
run: python3 tools/humor_ingest.py --ingest && python3 tools/fix_steps.py --humor review/humor-findings.jsonl --plan-dir plans/v4-es-1
gate: python3 tools/humor_ingest.py --check-review && test -s translation/humor-decisions.jsonl && python3 -I tools/humor_register.py --check && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: decide each humor item

No model work. `tools/humor_ingest.py --ingest` writes one row for each register item in `translation/humor-decisions.jsonl` (`kept`, `transcreated` or `flattened`, with the reason of the native reviewer). An item that two or more jurors scored under 4 of 5 goes to `review/humor-findings.jsonl`. `tools/fix_steps.py --humor` turns those rows into `fix-humor-*.md` steps (they depend on this step). Gate 7 needs every item decided.

## Do not change

- Files outside `touches`. The `gate`. `translation/humor-register.jsonl`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
