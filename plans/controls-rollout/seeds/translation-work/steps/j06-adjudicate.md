---
id: j06-adjudicate
status: pending
depends_on: [j05-ingest]
touches:
  - review/findings-*.jsonl
  - review/adjudication-notes.md
  - plans/v4-es-1/steps/j06-adjudicate.md
lane: none
gate: python3 tools/jury_gate.py --stage adjudicated && test -s review/adjudication-notes.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Adjudicate every Jury finding

You are the fresh-context adjudicator. You are not a juror. The translator was `claude-sonnet-5-5`. This step runs on Claude (owner decision 2026-11-23: Codex is reserved for the owner's own use), with the host's standard model, which is not the translator's model. Read the model that the driver reports in its usage block and write it in `review/adjudication-notes.md`. If the reported model is `claude-sonnet-5-5`, stop and set `status: blocked`: the adjudicator must not be the translator's model. Another vendor is possible only if the owner approves it.

## Change

- Read `review/report-<date>.md` and `review/findings-<date>.jsonl`. For each finding, check the quotes against the English source (`translation/source.json` names the clone; the English text is also in the packets of the report) and the Spanish file. Set `status` to `accepted`, `rejected`, `duplicate`, `needs-human` or `needs-source-issue`, and write a one-line `reason`. Never decide by majority vote.
- Set `needs-human` for every finding about playfulness, a guarantee, the 40-rule, safety or the acronym. Set `needs-source-issue` for a defect of the English.
- Do not change a Spanish file. Fixes come in later steps.
- Write `review/adjudication-notes.md`: counts for each status and the list of `needs-human` ids with one line each for Jim.

## Do not change

- Files outside `touches`. The `gate`. Any field of a finding except `status` and `reason`.

## Done when

- The gate passes: no finding is `open`.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
