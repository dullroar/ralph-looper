---
id: j02-batch-requests
status: pending
depends_on: [j01-packets, g02-lane-requests]
touches:
  - plans/v4-es-1/records/j02-batch-requests.md
  - plans/v4-es-1/steps/j02-batch-requests.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py requests
gate: python3 plans/v4-es-1/gatelib.py keys plans/v4-es-1/records/j02-batch-requests.md rows lenses input-sha256 dry-run && grep -q '^lenses: 13$' plans/v4-es-1/records/j02-batch-requests.md && grep -q '^dry-run: ok$' plans/v4-es-1/records/j02-batch-requests.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: build the Jury batch input, one set for each lens and packet

No model work. The `run` command rebuilds the packets in `.probe/` (it fails if the digest differs from the record of `j01-packets`), writes the batch input with `tools/jury_requests.py build`, and runs `tools/batch.py build ... --dry-run`. It records the row count, the 13 lenses and the digest of the input in `plans/v4-es-1/records/j02-batch-requests.md`, and deletes `.probe/`. The operator builds the real request file in `j03-batch-jurors`, because the model is chosen there.

## Do not change

- Files outside `touches`. The `gate`. The tools.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
