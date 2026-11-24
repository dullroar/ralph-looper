---
id: c05-retrospective
status: pending
depends_on: [c04-assert-reuse, j10-gate-7]
touches:
  - translation/cookbook.md
  - translation/runs/v4-es.1.yaml
  - plans/v4-es-1/steps/c05-retrospective.md
lane: none
gate: for k in '^edition: v4-es.1' '^source:' '^previous_edition:' '^models:' '^inputs:' '^segments:' '^findings:' '^canary_recall:' '^gates:' '^tokens:' '^notes:'; do grep -Eq "$k" translation/runs/v4-es.1.yaml || exit 1; done && test -s translation/cookbook.md && grep -q 'rehearsal' translation/cookbook.md && python3 plans/v4-es-1/gatelib.py verify && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Update the cookbook and write the run file

## Change

- Write `translation/cookbook.md` (create it if it does not exist): the procedure of section 12 of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md`, updated with what this plan learned: what broke, glossary changes, reviewer performance (canary recall for each juror from `review/report-*.md`) and the real spend for each phase and route. Take the spend from `python3 tools/model_report.py`, the batch cost records (the records of `j03-batch-jurors` and `c03-delta-batch` name the totals) and the route report of the Ralph runner if the operator put one in `plans/v4-es-1/records/`. Say what you could not measure.
- Add the result of the rehearsal (`translation/rehearsal/impact.json` and `reuse-report.md`) as the acceptance test of the cookbook.
- Write `translation/runs/v4-es.1.yaml` with the template of section 12 of the synthesized plan: edition, source (repository, tag, commit from `translation/source.json`), previous edition, acronym, models (exact IDs from `loop/ledger` or the records), inputs, segment counts, findings, canary recall, human review (role, no name), gates, tokens and notes. Use only facts that a file or a record in the repository shows. Write `unknown` for the rest.

## Do not change

- Files outside `touches`. The `gate`. Other plan steps.

## Done when

- The gate passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
