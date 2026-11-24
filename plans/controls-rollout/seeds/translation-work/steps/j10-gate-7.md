---
id: j10-gate-7
status: pending
depends_on: [j09-round-two, h02-humor-ingest]
touches:
  - plans/v4-es-1/steps/j10-gate-7.md
lane: none
agent: script
run: python3 tools/jury_gate.py --stage final
gate: python3 tools/jury_gate.py --stage final && python3 plans/v4-es-1/gatelib.py release --no-gates && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: Gate 7

No model work. Gate 7 means: no unresolved critical or major finding, canary reports filed, the humor register decided, the cold-reader test passed, all `needs-human` items decided and the Jury report committed. `jury_gate.py --stage final` checks each of these. The gate also runs `verify.py --release --no-gates` (exit `0` or `3` is a pass here; the full release is `r01-release-gates`).

## Do not change

- Files outside `touches`. The `gate`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
