---
id: p01-pack-contract
status: pending
depends_on: []
touches:
  - src/deterministic_controls/checks/translation_common.py
  - tests/test_translation_common.py
  - tests/fixtures/translation_common/**
  - docs/translation-pack.md
  - docs/README.md
  - plans/AGENTS.md
  - plans/translation-pack/steps/p01-pack-contract.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_common.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the pack contract and the shared helpers

Read `plans/translation-pack/plan.md` first. It has the pack contract (rule IDs, mapping file, fail-closed rule, exception file) and the rules taken from the translation tools. This step turns that contract into one shared module and one document. Steps `p02` to `p08` use the module and may not change it, so make it complete for them.

## Change

- `checks/translation_common.py` (standard library only). It gives the other checks:
  - a loader for the parameters `mapping` and `exceptions` (TOML; the exception file may also be JSONL). A missing parameter means "not configured". A parameter that names a missing or bad file raises a clear error type that the check turns into a finding with rule `<check-id>.bad-config`.
  - pairing of source and target Markdown files from the mapping (source root, target root, path renames, anchor renames; a default is the same relative path). A target that is missing gives a finding. A path that leaves the repository is refused.
  - a small Markdown scanner for the rules in `plan.md`: line classes (front matter, fenced block with its fence character, length and info string, HTML comment, table row, prose), an unclosed fence is reported, never ignored. It uses only the standard library.
  - a helper that builds a `Finding` with the pack rule ID format, and a helper that applies the exception file (including `stale-exception`).
- `docs/translation-pack.md`: the pack contract in plain words. The mapping and exception file formats with one example each, the opt-in rule, the "generic" test, the limit that the source tree must be inside the checked root, and a table with one row for each check of the pack (ID, status, one sentence). Rows for later checks say "added in step pN". Add the document to `docs/README.md`.
- `plans/AGENTS.md`: run `python3 scripts/build_indexes.py`. It lists this plan.
- Tests: good and bad fixtures for the mapping loader (missing parameter, missing file, bad TOML, path that leaves the root, missing target), the scanner (every line class, `~~~` and longer fences, an indented fence, a fence that never closes, a table row with `\|`) and the exception file (a waived finding, a stale row, a row with no reason). Assert behavior and error types, not counts of helpers.

## Do not change

- Files outside `touches`. The `gate` command. `controls.toml`: the pack is opt-in.
- Do not add a catalog file in this step. The module has no check of its own.

## Already done by earlier steps

- None in this plan. The library core, `Context` and `Finding` exist (`core/api.py`).

## Done when

- The gate passes. The full test suite passes. `docs/translation-pack.md` is linked from `docs/README.md` and its links are valid.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
