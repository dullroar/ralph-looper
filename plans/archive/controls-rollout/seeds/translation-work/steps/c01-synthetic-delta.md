---
id: c01-synthetic-delta
status: pending
depends_on: []
touches:
  - tools/rehearsal.py
  - tools/test_rehearsal.py
  - tools/fixtures/rehearsal/**
  - plans/v4-es-1/steps/c01-synthetic-delta.md
lane: none
gate: python3 plans/v4-es-1/gatelib.py tests tools/test_rehearsal.py && python3 plans/v4-es-1/gatelib.py tests && python3 plans/v4-es-1/gatelib.py verify && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Build the cookbook rehearsal fixture and its tool

The cookbook rehearsal (section 12, item 12, of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md`) is the acceptance test of the cookbook. It runs on a small synthetic English release, not on the real book.

## Change

- `tools/fixtures/rehearsal/`: a tiny English tree "old" and a tiny English tree "new", the matching Spanish PO files and Markdown for "old", a source map and an identifier map. The delta has these six changes: a new paragraph, a changed code identifier, a moved heading, a new API symbol, a changed diagram, and a change that only touches a generated English file (it must be traced back to its authored source, never translated directly). Add one unchanged file whose neighbor changed.
- `tools/rehearsal.py` with two commands. `impact`: run `tools/impact.py` (reuse its functions) and `msgmerge` on the fixture, write the schedule (`translate_units`, fuzzy entries, `model_calls_needed`, `reused_spanish_units`, gates) to `translation/rehearsal/impact.json`, and write the fuzzy entries to `translation/rehearsal/fuzzy.jsonl` in the pending format of `tools/translate.py --export-pending`. Assert that only the affected units are scheduled. `import-assert`: import the reconciled drafts (`translation/rehearsal/drafts.jsonl`) with `tools/translate.py --drafts`, then assert the reuse (each untouched Spanish unit is byte-equal, with no draft requested for it) and that every code, graph, book and link gate that the schedule names was run. Write `translation/rehearsal/reuse-report.md`, with the line `model-calls-for-reused-units: 0` (the gate of `c04-assert-reuse` reads it). Both commands work on fixture paths only and change nothing else.
- Known-bad fixtures: a schedule that includes an unaffected unit; a draft for an untouched unit; a gate that the change reaches but the run skipped. Each must fail for its own message.

## Do not change

- Files outside `touches`. The `gate`. `tools/impact.py`, `tools/translate.py` (use them). Never call the network or the Batch API.

## Done when

- The gate passes. Run the full tool suite before you commit.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
