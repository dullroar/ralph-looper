---
id: j05-ingest
status: pending
depends_on: [j03-batch-jurors, j04-outside-jurors]
touches:
  - review/report-*.md
  - review/findings-*.jsonl
  - plans/v4-es-1/steps/j05-ingest.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py ingest
gate: ls review/report-*.md review/findings-*.jsonl > /dev/null && grep -qi 'recall' review/report-*.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: ingest the Jury replies

No model work. The `run` command rebuilds the packets in `.probe/` (it fails if the digest differs from the record of `j01-packets`), copies the tracked `review/inbox/` there, runs `tools/jury_ingest.py`, and copies `review/report-<date>.md` and `review/findings-<date>.jsonl` back. The report has the canary recall for each juror. The findings have the status `open`. The command does not use `--enqueue`: the old queue is archived.

## Do not change

- Files outside `touches`. The `gate`. `loop/`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
