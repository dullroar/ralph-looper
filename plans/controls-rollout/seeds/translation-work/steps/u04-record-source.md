---
id: u04-record-source
status: pending
depends_on: [u03-upstream-pr]
touches:
  - translation/source.json
  - translation/reports/impact-v4-es.1.json
  - plans/v4-es-1/steps/u04-record-source.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py record-source plans/v4-es-1/records/u03-upstream-pr.md
gate: python3 plans/v4-es-1/gatelib.py source-check plans/v4-es-1/records/u03-upstream-pr.md && python3 plans/v4-es-1/gatelib.py verify && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: pin the accepted English commit and write the impact report

No model work. The `run` command writes the accepted commit of `u03-upstream-pr` to `translation/source.json` (and keeps the old one as `previous_english_commit`). It then runs `tools/impact.py --old <pinned commit> --new <accepted commit> --release v4-es.1 --write` on two scratch clones of the English repository. The report is `translation/reports/impact-v4-es.1.json`. It does not touch `loop/CONFIG.yaml`: `u05-adopt-upstream` plans that change (task A6).

## Do not change

- Files outside `touches`. The `gate`. The English clone (read only).

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
