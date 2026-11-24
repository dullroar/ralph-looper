---
id: p09-fixtures-and-matrix
status: pending
depends_on: [p02-fences, p03-links, p04-structure, p05-glossary, p06-chunks, p07-markdown-pack, p08-untranslated]
touches:
  - tests/test_translation_negative.py
  - tests/test_translation_mutation.py
  - tests/test_translation_fail_closed.py
  - tests/fixtures/translation_negative/**
  - docs/fault-matrix.md
  - src/deterministic_controls/checks/translation_*.py
  - src/deterministic_controls/checks/markdown_required_headings.py
  - src/deterministic_controls/checks/markdown_front_matter.py
  - src/deterministic_controls/checks/markdown_document_ids.py
  - src/deterministic_controls/catalog/translation.*.toml
  - src/deterministic_controls/catalog/markdown.required-headings.toml
  - src/deterministic_controls/catalog/markdown.front-matter.toml
  - src/deterministic_controls/catalog/markdown.document-ids.toml
  - tests/test_translation_common.py
  - tests/test_translation_fences.py
  - tests/test_translation_links.py
  - tests/test_translation_structure.py
  - tests/test_translation_glossary.py
  - tests/test_translation_chunks.py
  - tests/test_translation_untranslated.py
  - tests/test_markdown_required_headings.py
  - tests/test_markdown_front_matter.py
  - tests/test_markdown_document_ids.py
  - tests/fixtures/translation_*/**
  - tests/fixtures/markdown_required_headings/**
  - tests/fixtures/markdown_front_matter/**
  - tests/fixtures/markdown_document_ids/**
  - plans/translation-pack/steps/p09-fixtures-and-matrix.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_negative.py' -v && python3 -m unittest discover -s tests -p 'test_translation_mutation.py' -v && python3 -m unittest discover -s tests -p 'test_translation_fail_closed.py' -v && python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m deterministic_controls check --root . --profile full && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prove the pack can fail: known-bad fixtures, mutation tests, fail-closed tests, fault matrix

Read `plans/translation-pack/plan.md` first. A check that never fails proves nothing. Steps `p02` to `p08` tested each check alone. This step tests the pack as a whole. Read `tests/test_mutation.py`, `tests/test_fail_closed.py` and `docs/fault-matrix.md` for the pattern. Do not change those three files. The long `touches` list is on purpose: if a new test shows a defect in a pack check, fix it in the check and in its own test file, and write each fix under "Results". Do not weaken an earlier test.

## Change

- `tests/test_translation_negative.py`: a catalog of the planted defects in the table of `plan.md` ("Negative fixtures"). Each row has a good control, a mutation of it and the expected rule ID. Build the pairs in a temporary directory at run time, or keep them in `tests/fixtures/translation_negative/` (Markdown with the suffix `.fixture`). The control must be clean (exit `0`). The mutation must fail (exit `1`) **for the stated rule**, matched as a whole word. A row that does not fail, or fails for another rule, fails the test. Cover every defect row of the table with at least one case.
- `tests/test_translation_mutation.py`: start from a good pair and apply one mutation at a time (drop a fence, swap two Mermaid edges, drop a table cell, change a link fragment, rename a file without a path rename, remove a chunk row, change a source digest, weaken a glossary banned list in a copy of the check). Each mutation turns a pass into the expected failure. Also two metamorphic tests: file order and repeated runs do not change the findings; renaming the root directory changes only the path root.
- `tests/test_translation_fail_closed.py`: for each pack check: an exception inside the check, a timeout, an unreadable file (invalid UTF-8) and a missing mapping file give status `error` or a finding, and a nonzero exit. Never exit `0`. Opt-in tests: a repository with no pack configuration and no pack check enabled passes; with each pack check enabled and no parameters it passes with no findings; a pack check named in `enabled` that is not in the catalog is exit `2`. Reuse the helpers of `tests/test_mutation.py` by import.
- `docs/fault-matrix.md`: add a section for the pack. One row for each pack check and fault (missing file, unreadable file, malformed input, internal error, timeout, bad configuration), the expected result and the test that proves it. Add measured times for 100 and 1,000 file pairs (build them at run time; assert only a loose bound). Write in Simplified Technical English. Keep the links valid.
- The full profile on this repository must still pass: the pack is not enabled in `controls.toml`.

## Do not change

- Files outside `touches`. The `gate` command. `tests/test_mutation.py`, `tests/test_fail_closed.py`, `controls.toml`.

## Already done by earlier steps

- p01 to p08: the shared helpers and all pack checks, each with good and bad fixtures.

## Done when

- The gate passes. The negative catalog covers every defect row of `plan.md`. The fault matrix lists every pack check.

## Results

(none)

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date. Write under "Results": the number of negative cases, and each fix that you made to an earlier file, with the reason.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
