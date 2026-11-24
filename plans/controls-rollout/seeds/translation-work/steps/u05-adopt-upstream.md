---
id: u05-adopt-upstream
status: pending
depends_on: [u04-record-source]
touches:
  - plans/v4-es-1/steps/adopt-*.md
  - translation/part3/spanish-adoption-plan-draft.md
  - plans/v4-es-1/steps/u05-adopt-upstream.md
lane: none
gate: grep -Eq '^\*\*Status: FINAL' translation/part3/spanish-adoption-plan-draft.md && ls plans/v4-es-1/steps/adopt-*.md > /dev/null && python3 plans/v4-es-1/gatelib.py verify && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Turn the draft adoption plan into steps

## Change

- Read `translation/part3/spanish-adoption-plan-draft.md` (tasks A1 to A7) and `translation/reports/impact-v4-es.1.json`. Compare the report with the inventory table of the draft. If the report lists a file that the table does not list, the draft is stale: write "Resume notes" with the extra file and stop.
- Write one step file `plans/v4-es-1/steps/adopt-a<n>-<name>.md` for each task of the draft that the report needs (A1 to A7; A7 only for approved source issues). Each step has `lane: none`, `depends_on`, `touches` (disjoint from every other step of this plan), a gate and the review that the draft names. A step that changes a PO file, translated content or a pin starts after `j10-gate-7`, so add `j10-gate-7` to its `depends_on`. `A5` (link and language-pair check) also needs the published repository: make it an operator step with a record and a gate that checks the outside result. Include the pin bump A6 for `loop/CONFIG.yaml`, `loop/STATE.md` and the manifest.
- Change the first status line of the draft to `**Status: FINAL.**`, and replace the pinned revision with the accepted one.
- Follow the format of the step template in `plans/for-each-plan/steps/00-step-template.md`.

## Do not change

- Files outside `touches`. The `gate`. Frozen code, Part II localized families and the sandbox.

## Done when

- The generated steps pass `python3 scripts/check_context.py` (plan schema and graph). The gate passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
