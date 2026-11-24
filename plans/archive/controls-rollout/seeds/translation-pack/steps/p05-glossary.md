---
id: p05-glossary
status: pending
depends_on: [p01-pack-contract]
touches:
  - src/deterministic_controls/checks/translation_glossary.py
  - src/deterministic_controls/catalog/translation.glossary.toml
  - tests/test_translation_glossary.py
  - tests/fixtures/translation_glossary/**
  - plans/translation-pack/steps/p05-glossary.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_glossary.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the check `translation.glossary`

Read `plans/translation-pack/plan.md` first (pack contract, "Glossary", "Do-not-translate"). Use `checks/translation_common.py` of `p01` without change. The source tool reads YAML. The library has no YAML parser, so the pack glossary is **TOML** (and optionally JSON). Name the file in the parameter `glossary`.

## Change

- `checks/translation_glossary.py` with `entry(context)`. Glossary format: an array of tables `[[terms]]` with `id`, `en` (source text), `target` (approved rendering) and `banned` (list of strings, may be empty). Optional parameter `dnt` names a text file with one do-not-translate phrase per line. Stable rule IDs:
  - `.bad-glossary`: a term without `id`, `en` or `target`; a duplicate `id`; a `banned` entry that is empty or not a string; an approved rendering that is in its own `banned` list; a banned word that is the approved rendering of another term.
  - `.missing-rendering`: the source segment holds the term (`en`), but the target holds no approved rendering.
  - `.banned-term`: the target holds a banned word.
  - `.dnt-missing`: a DNT phrase of the source is not in the target.
- Match whole words, after Unicode NFC, ignoring letter case. Skip fences, inline code, URLs and link destinations. An exception row (shared helper) may waive a finding for a path. Source and target are paired by the `mapping` parameter. Write the matching rule in the catalog `summary` and in the module docstring (`docs/` belongs to `p01` and `p10`).
- `catalog/translation.glossary.toml`: id `translation.glossary`, status `advisory`, severity `error`. The `summary` says why the check is generic.
- No `glossary` parameter: no findings. A glossary file that is missing or bad TOML: `.bad-glossary`, never a pass.

## Fixtures and tests

Follow the fixture rule in `plan.md`. A good glossary and target, and one bad fixture for each rule. Edge cases: an accented term; a term inside a code span (skipped); a term inside a link destination (skipped); a term that is a prefix of a longer word (no match); the same word banned for one term and approved for another; a waived finding; a stale exception row. Use made-up terms in fixtures. The test asserts for each bad fixture the rule ID, the path and exit code `1`. Good fixtures give exit `0`.

## Do not change

- Files outside `touches`. The `gate` command. `translation_common.py`, `docs/`.

## Already done by earlier steps

- p01-pack-contract: the mapping loader, the scanner, the finding and exception helpers.

## Done when

- The gate passes. Each bad fixture fails for its own rule. Each good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
