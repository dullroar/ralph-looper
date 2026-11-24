---
id: p07-markdown-pack
status: pending
depends_on: [p01-pack-contract]
touches:
  - src/deterministic_controls/checks/markdown_required_headings.py
  - src/deterministic_controls/checks/markdown_front_matter.py
  - src/deterministic_controls/checks/markdown_document_ids.py
  - src/deterministic_controls/catalog/markdown.required-headings.toml
  - src/deterministic_controls/catalog/markdown.front-matter.toml
  - src/deterministic_controls/catalog/markdown.document-ids.toml
  - tests/test_markdown_required_headings.py
  - tests/test_markdown_front_matter.py
  - tests/test_markdown_document_ids.py
  - tests/fixtures/markdown_required_headings/**
  - tests/fixtures/markdown_front_matter/**
  - tests/fixtures/markdown_document_ids/**
  - plans/translation-pack/steps/p07-markdown-pack.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_markdown_required_headings.py' -v && python3 -m unittest discover -s tests -p 'test_markdown_front_matter.py' -v && python3 -m unittest discover -s tests -p 'test_markdown_document_ids.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the Markdown pack checks (pack A)

Read `plans/translation-pack/plan.md` first. These three checks do not need a source or a mapping. They work on any Markdown repository, so they use the prefix `markdown.`. Use the scanner of `checks/translation_common.py` for front matter and fences, without change. Pass the parameters in `[parameters."<check-id>"]`.

## Change

- `markdown.required-headings`: parameter `rules`, a list of tables with `glob` (files) and `headings` (the heading texts that must exist, in this order, at the level in `level`). Rules: `.missing` (a heading is absent), `.order` (present but out of order). A heading inside a fence does not count.
- `markdown.front-matter`: parameter `rules`, a list of tables with `glob`, `required_keys` and optionally `allowed` (a table of key to list of allowed values). Rules: `.missing-file-block` (no front matter where required), `.missing-key`, `.bad-value`, `.unterminated` (front matter that never closes). Read only the simple `key: value` and `key: [a, b]` forms that the repository uses. A line that the reader does not understand is a finding (`.unreadable`), never a skip.
- `markdown.document-ids`: parameters `glob` and `key` (default `id`). Each matching file has a non-empty ID in its front matter; IDs are unique; an ID has no spaces. Optional parameter `registry`, a TOML file with `[ids]` mapping a path to its ID: an ID that differs from the registry is `.changed` (stable IDs), a registry path with no file is `.orphan`. Rules: `.missing`, `.empty`, `.duplicate`, `.changed`, `.orphan`.
- One catalog file for each check: status `advisory`, severity `error`. No lint-style check is added in this release. If you add any style rule, it is severity `info`.
- Without parameters, each check passes with no findings.

## Fixtures and tests

Follow the fixture rule in `plan.md`. For each check: one good fixture and one bad fixture for each rule. Edge cases: a heading with a trailing `#` or an explicit `{#id}`; a setext heading; a heading-like line inside a fence; an empty front matter block; a `---` rule that is not front matter (only the first line starts front matter); Unicode IDs; the same ID in two folders. The test asserts for each bad fixture the rule ID, the path and exit code `1`. Good fixtures and the no-parameter case give exit `0`.

## Do not change

- Files outside `touches`. The `gate` command. `translation_common.py`, `controls.toml`.

## Already done by earlier steps

- p01-pack-contract: the scanner (front matter, fences, headings) and the finding helpers.

## Done when

- The gate passes. Each bad fixture fails for its own rule. Each good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
