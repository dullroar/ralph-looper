---
id: g01-lane-tools
status: pending
depends_on: []
touches:
  - tools/fix_steps.py
  - tools/inbox_check.py
  - tools/jury_gate.py
  - tools/test_fix_steps.py
  - tools/test_inbox_check.py
  - tools/test_jury_gate.py
  - tools/fixtures/jury/**
  - plans/v4-es-1/steps/g01-lane-tools.md
lane: none
gate: python3 plans/v4-es-1/gatelib.py tests tools/test_fix_steps.py tools/test_inbox_check.py tools/test_jury_gate.py && python3 plans/v4-es-1/gatelib.py tests && python3 plans/v4-es-1/gatelib.py verify && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the three tools of the Jury lane

The Jury lane needs three small tools. Standard library only. Each has `--help`, a `Run me when:` line in its docstring and tests with fixtures.

## Change

- `tools/fix_steps.py` has this command line (the plan steps use it): `--findings GLOB --plan-dir DIR` writes the steps; the same with `--check` writes nothing and proves the result; `--humor FILE.jsonl --plan-dir DIR` writes the humor steps; `--all-done DIR`. It reads the adjudicated `review/findings-*.jsonl` (see `plan.md`, "Contracts") and write one `plans/v4-es-1/steps/fix-po-<name>.md` for each PO file, or `fix-code-<family>.md` for each code family, that has accepted findings (and `human_decision: accepted`). Also write `fix-humor-*.md` from `translation/humor-decisions.jsonl` on `--humor`. Several findings in one file make one step, so that the `touches` of two fix steps never overlap. A step touches its PO file, its generated Markdown and its own step file. Set `lane: none`, `depends_on` to the generator step (`j08-fanout-fixes` or `h02-humor-ingest`), `tier: light` for a mechanical fix (a number, a glossary term, a link) and no tier for a fix that changes meaning. The gate of a fix step is `python3 plans/v4-es-1/gatelib.py verify <po> <md> && python3 plans/v4-es-1/gatelib.py guard && git diff --check`. For a code family add the anchor check and the oracle for that family (find the commands in `tools/anchors.py` and `tools/oracle.py`). Keep the step body to the findings and their exact quotes. `--all-done DIR` exits 0 only when every `fix-*.md` in `DIR/steps` has `status: done`. `--check` proves that every accepted finding is in one step and that the `touches` are disjoint.
- `tools/inbox_check.py` (no arguments needed; defaults are `review/inbox` and the table below): check `review/inbox/` against `plans/v4-es-1/records/j04-outside-jurors.tsv`. For the files that start with `outside-`: at least 5 jurors, at least 3 vendors, `in_loop` is `no` in each row, every file has a row, at least 2 jurors on lens L11, and each file has the header line and the JSONL of the master prompt (reuse the parser of `tools/jury_ingest.py`; do not copy it).
- `tools/jury_gate.py --stage adjudicated|human|final`: `adjudicated` = no finding is `open`. `human` = every `needs-human` row has `human_decision` and `human_reason`. `final` = Gate 7: also no unresolved `critical` or `major` finding (an accepted one needs a `done` fix step), a tracked `review/report-*.md` that reports canary recall for each juror, `translation/humor-decisions.jsonl` complete for the humor register, `cold-reader-result: pass` in `plans/v4-es-1/records/j04-outside-jurors.md`, and no `needs-human` row without a decision. Take the exact exit criteria from "Phase 7" of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md` (Gate 7).
- Each tool fails closed: a missing or unreadable file is an error, never a pass.

## Do not change

- Files outside `touches`. The `gate`. `tools/jury_ingest.py`, `tools/jury_packet.py` (use them). `loop/STOP`.

## Done when

- Each tool has a known-good fixture that passes and a known-bad fixture for each rule that fails for the expected reason (assert the message, not only the exit code). Examples of bad fixtures: two findings on one PO file, four jurors, two vendors, an `open` finding, a `major` finding with no fix step.
- The gate passes. Run the full tool suite before you commit.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
