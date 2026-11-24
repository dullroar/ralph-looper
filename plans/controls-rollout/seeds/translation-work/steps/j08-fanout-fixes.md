---
id: j08-fanout-fixes
status: pending
depends_on: [j07-human-decisions, g01-lane-tools]
touches:
  - plans/v4-es-1/steps/fix-po-*.md
  - plans/v4-es-1/steps/fix-code-*.md
  - plans/v4-es-1/steps/j08-fanout-fixes.md
lane: none
agent: script
run: python3 tools/fix_steps.py --findings 'review/findings-*.jsonl' --plan-dir plans/v4-es-1
gate: python3 tools/fix_steps.py --check --findings 'review/findings-*.jsonl' --plan-dir plans/v4-es-1 && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: write one fix step for each PO file or code family

No model work. `tools/fix_steps.py` (built in `g01-lane-tools`) reads the decided findings and writes `plans/v4-es-1/steps/fix-po-*.md` and `fix-code-*.md`. Each fix step touches one PO file and its generated Markdown, or one code family. A fix step with a mechanical change has `tier: light`. A fix step that changes meaning has a standard agent. The gate of each fix step runs `verify.py --fast --files` on its files, the anchor check and, for a code family, the oracle.

The steps depend on this step only. `j09-round-two` waits for all of them with its gate (`fix_steps.py --all-done`).

The gate checks that every accepted finding is in exactly one fix step and that no two fix steps have overlapping `touches`. If `fix_steps.py` has a defect, fix it in a step of this plan through an operator amendment. Do not edit a generated step by hand.

## Do not change

- Files outside `touches`. The `gate`. `tools/fix_steps.py`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
