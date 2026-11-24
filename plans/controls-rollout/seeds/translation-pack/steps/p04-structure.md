---
id: p04-structure
status: pending
depends_on: [p01-pack-contract]
touches:
  - src/deterministic_controls/checks/translation_structure.py
  - src/deterministic_controls/catalog/translation.structure.toml
  - tests/test_translation_structure.py
  - tests/fixtures/translation_structure/**
  - plans/translation-pack/steps/p04-structure.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_structure.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the check `translation.structure`

Read `plans/translation-pack/plan.md` first (pack contract, "Structure", "Mermaid", "Mask and protect"). Use `checks/translation_common.py` of `p01` without change. The Mermaid fences are the only fences that this check reads. `translation.fences` (step `p02`) skips them.

## Change

- `checks/translation_structure.py` with `entry(context)`. For each pair of the mapping compare the source and the target. Stable rule IDs:
  - `.headings`: the number or the levels of headings differ.
  - `.table-rows`, `.table-cells`: a table has a different row count, or a row has a different cell count. A cell separator is an unescaped `|` outside a code span. `\|` is cell text.
  - `.footnotes`: the footnote references and definitions differ.
  - `.bold-count`: the number of `**bold**` spans differs.
  - `.front-matter`: the front matter keys differ, or the value of a key that the parameter `fixed_front_matter_keys` names differs.
  - `.mermaid-skeleton`: a diagram skeleton or its label slots (line and role) differ.
  - `.mermaid-label`: a label breaks the Mermaid syntax (the rules in `plan.md`).
  - `.mermaid-unsupported`: the diagram is not understood. Never skip it.
- `catalog/translation.structure.toml`: id `translation.structure`, status `advisory`, severity `error`. The `summary` says why the check is generic. Each sub-rule can be turned off in the parameters by name (`disabled_rules`), so a repository can adopt the check in steps. A disabled rule drops its findings. An unknown rule name in `disabled_rules` is a `.bad-config` finding.
- No `mapping` parameter: no findings.

## Fixtures and tests

Follow the fixture rule in `plan.md`. One good pair and one bad pair for each rule. Mermaid cases: `flowchart`, `sequenceDiagram` and `stateDiagram-v2`, each good (labels translated, skeleton equal) and bad (a node ID renamed in one edge only; two branch edges swapped; `accDescr` removed; a double quote in a quoted label; `;` in a message). Also bad: a table with a deleted cell, a deleted row, an escaped pipe that changes the cell count, an unclosed Mermaid fence, an unsupported diagram type. The test asserts for each bad fixture the rule ID, the path and exit code `1`. Good fixtures give exit `0`.

## Do not change

- Files outside `touches`. The `gate` command. `translation_common.py`.

## Already done by earlier steps

- p01-pack-contract: the mapping loader, the scanner (fences, front matter, tables), the finding and exception helpers, and `docs/translation-pack.md`.

## Done when

- The gate passes. Each bad fixture fails for its own rule. Each good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
