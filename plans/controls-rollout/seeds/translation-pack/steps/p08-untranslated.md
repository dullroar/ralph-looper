---
id: p08-untranslated
status: pending
depends_on: [p01-pack-contract]
touches:
  - src/deterministic_controls/checks/translation_untranslated.py
  - src/deterministic_controls/catalog/translation.untranslated-heuristic.toml
  - tests/test_translation_untranslated.py
  - tests/fixtures/translation_untranslated/**
  - plans/translation-pack/steps/p08-untranslated.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_untranslated.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the check `translation.untranslated-heuristic` (advisory only)

Read `plans/translation-pack/plan.md` first (pack contract, "Untranslated"). Use `checks/translation_common.py` of `p01` without change. This is a heuristic. It can be wrong in both directions. So it is **advisory only**: its findings have severity `info`, its catalog status is `advisory`, and no document of this release may ever call it `required`.

## Change

- `checks/translation_untranslated.py` with `entry(context)`. For each target file of the mapping, split the prose into segments (paragraphs, list items, table cells, headings). Skip front matter, fences, inline code, URLs, link destinations, `{{macro}}` and `[[macro]]` tokens, and the do-not-translate phrases of the parameter `dnt` (a text file, optional). For each segment count the words and the words that are in the **source-language stopword list**. The list is a parameter `source_stopwords` (a list of words). The default is the English list in `plan.md`. A target language is not hard coded. Optional parameter `target_stopwords`: words that are removed from the source list, because they are also words of the target language.
- Parameters `threshold` (default `0.30`, share of stopwords) and `min_words` (default `6`, shorter segments are skipped). One rule: `translation.untranslated-heuristic.segment`. The finding gives the path, the line and the share. The message says that it is a heuristic.
- `catalog/translation.untranslated-heuristic.toml`: id `translation.untranslated-heuristic`, status `advisory`, severity `info`. The `summary` says "advisory heuristic, never required".
- No `mapping` parameter: no findings.

## Fixtures and tests

Follow the fixture rule in `plan.md`. Fixtures use any pair of languages, and can use made-up word lists through the parameters, so the test does not depend on one language. Good: a fully translated page; a page of code and URLs only; a short English heading (under `min_words`); an English phrase that is in `dnt`. Bad: a paragraph left in the source language; a table cell left in the source language. Tests assert:

- the bad fixture gives the rule ID, the path and a line;
- the run exits `0` (severity `info` does not fail), and the result status is `passed`;
- the catalog entry has status `advisory` and the check is not mandatory (test the catalog value, not a count);
- a word that is in `target_stopwords` does not count.

## Do not change

- Files outside `touches`. The `gate` command. `translation_common.py`.

## Already done by earlier steps

- p01-pack-contract: the scanner and the finding helpers.

## Done when

- The gate passes. The bad fixture is reported with severity `info`. The good fixtures give no finding.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
