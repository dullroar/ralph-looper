---
gist: "Read me when: you add or change the opt-in translation and Markdown checks of the deterministic-controls library for release v0.2.0."
---

# Plan: the translation and Markdown pack (v0.2.0)

This file is the high-level plan. The detail is in `steps/`. Every step is self-contained. Read this file for the shared facts.

## Approach

The library already has the core (CLI, manifest, result contract, catalog) and seven checks. This plan adds ten checks in two groups. Each check has its own catalog file, module, test file and fixture directory, as the earlier checks have. Look at `checks/markdown_links.py`, `catalog/markdown.local-links.toml` and `tests/test_markdown_links.py` for the pattern. Step `p01` writes the shared contract and helpers. Steps `p02` to `p08` run in parallel. Step `p09` adds known-bad fixtures, mutation tests and fail-closed tests for the whole pack. Step `p10` prepares the release.

The facts below come from the tools of the Spanish edition of an English book (repository `aprende-a-programar-como-un-bicho-raro`, commit `f776cf00cc39fd81de763d25072597f838a39339`). That repository is not available here. Use only the facts in this plan and in the step files. A later review compares each check with the matching tool of that repository.

## Facts about this repository (confirmed on `main`, release 0.1.2)

- Package `deterministic_controls`, source in `src/`. Python 3.11 or later. **Standard library only at run time** (`tomllib`, `json`, `re`, `unicodedata`, `hashlib`). No YAML, no `markdown-it`, no `polib`. Tests use `unittest`.
- A check module has `entry(context)` and returns a list of `Finding` (`core/api.py`). It reads files only through the `Context` helpers, never writes, and does not catch its own errors. An exception gives status `error` and exit `3`.
- Catalog file `src/deterministic_controls/catalog/<check-id>.toml`: `id`, `summary`, `version`, `status`, `severity`, `module`, `entry`, optional `parameters` defaults. Policy (`core/policy.py`): a finding with severity `warning` or `error` fails the run (exit `1`). Severity `info` never fails. The catalog `status` does not change this.
- `controls.toml` accepts only `schema_version`, `profile`, `enabled`, `disabled` and `parameters`. A parameter table is `[parameters."<check-id>"]`. A check runs only if it is in `enabled`. So the pack is opt-in: do not add the new checks to this repository's own `controls.toml`.
- A check that is enabled and has no configuration (its parameters are absent) must **pass with no findings**. A check with a configuration that is wrong (file missing, bad TOML, bad key) must give a finding, never a pass.
- Fixture rule. Store each Markdown fixture file with the extra suffix `.fixture` (for example `a.md.fixture`). The test copies the fixture tree to a temporary directory and removes the suffix before it runs the check. Other file types (TOML, JSON, JSONL) are stored as they are. Build a fixture that holds a secret or a personal path at run time. Fixture text must hold no real names, no e-mail addresses and no local paths.
- Each test file adds `<repo>/src` to `sys.path` at its top, so `python3 -m unittest discover -s tests` works without an install.
- Tests assert behavior: rule IDs, paths, exit codes, subset membership, `__version__`. A test must not assert an empty registry, a count of checks or a literal version. `tests/test_fail_closed.py` and `tests/test_mutation.py` list checks by their own fixed lists. A new check does not change them.
- The secret guard (`scripts/secret_guard.py`, hooks, CI job) is already installed. Do not change it. Do not add an exception to `.secret-guard-allow`.
- Install line for consumers (put it in the documents of `p10`): `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@3a2e9f3d95136958c54f73c831e84b971fc9a054"` is release `v0.1.2`. The commit of `v0.2.0` does not exist before the release. Use the placeholder `<commit>`.

## Pack contract (decided here, written down in `p01`)

- Rule IDs have the form `<check-id>.<rule>`, for example `translation.fences.code-differs`. Findings give the **target** path and the line in the target. The message names the source path.
- Source and target are paired by a **mapping file**: a TOML file named by the parameter `mapping` (a path inside the repository). It holds the source root, the target root, optional path renames and optional anchor renames. The source tree must be inside the checked root (a check cannot read outside it). A source tree outside the root is a limit; write it in the docs.
- Fail closed. A pair whose target is missing is a finding. A fence that never closes, a table that cannot be read or a diagram that the check does not understand is a finding. It is never a skip.
- Waiver. A finding is waived only by a row in an exception file named by the parameter `exceptions` (TOML or JSONL). A row names the check rule, the target path and a non-empty reason. A row that matches no finding is itself a finding (`stale-exception`). Nothing else turns a finding off.
- Advisory checks give severity `info`. `translation.untranslated-heuristic` is always advisory.
- Pack-wide test for "generic": a check is in the pack only if it works on any Markdown-to-Markdown translation that has a source manifest, with no language, book or project name in its code. Language lists, glossaries and word lists are parameters or files, not code.

## Rules taken from the translation tools

These facts are the inputs for the step files.

- **Mask and protect** (`mask.py`). Withheld lines are never changed: front matter, fenced blocks and whole-line HTML comments. Fence open: up to 3 spaces, then 3 or more backticks or tildes. A closing fence uses the same character and at least the same length. Inline code, autolinks, link destinations, bare URLs, HTML tags, `{{macro}}` and `[[macro]]` tokens are protected tokens. A table row `|a|b|` has separators that are unescaped `|` outside code spans; `\|` is cell text. The multiset of protected tokens in the target must equal the source's: report each token that is dropped, duplicated or invented.
- **Segments** (`segment.py`, `invariants.py`). A document is split into blocks and labels. Each segment has a stable ID (`s-...`) and a source hash. A coverage check reports orphan, duplicate, stale, missing, empty and fuzzy entries (invariant I16).
- **Links** (`link_audit.py`, `anchors.py`, invariant I4). Parse Markdown links, images and HTML `href` and `src`, never inside code. Skip `{{...}}` and `[[...]]` macros. A destination with a scheme (`https:`, `mailto:`) is external: it must equal the source and is never fetched. A relative path must exist after the path renames of the mapping. A `#fragment` must match a heading ID of the target file: GitHub style (NFC, lower case, letters, marks and digits kept, accents kept, `-` and `_` kept, spaces become `-`, other punctuation dropped, a duplicate gets `-1`, `-2`, ...) or an explicit `id=` or `name=` attribute. Source fragments are mapped through the anchor renames. A line anchor `#L12` or `#L12-L20` must be a valid range inside the target file (`a >= 1`, `b >= a`, `b <= line count`). Link destinations of the target must equal those of the source after both maps. A link into the source repository's URL from the target is a finding (foreign repository link).
- **Fences** (invariant I13). Code and output blocks equal the source byte for byte. Fence count, order, fence character and language tag equal. Fence kinds named in the parameter `translatable_kinds` (default `["mermaid"]`) are not compared here.
- **Mermaid** (`mermaid.py`, invariants I5 and I10). Only text labels may change: `accTitle`, `accDescr`, quoted node labels, edge labels in `|...|`, subgraph labels, participant aliases, message, note and block text, state and transition labels. Everything else is the **skeleton**: diagram type, node IDs, arrows, shapes, directives, `classDef`, `class`, `style`. The skeleton is the diagram with every label emptied, and it must equal the source's. The label slots (line and role) must equal. Supported types: `flowchart`/`graph`, `sequenceDiagram`, `stateDiagram-v2`. An unknown type, an unquoted node label, `click`, a directive or a multi-line `accDescr` is "not understood": report it. Label syntax problems: empty label; label over several lines; a double quote inside a quoted label (use `#quot;`); `|` or a double quote in an edge label; `;` in a message, note, block, participant or transition label (the entities `#quot;`, `#gt;`, `#lt;` are legal).
- **Structure.** Heading count and levels equal. Table row count and cell count in each row equal. Footnote references and definitions equal. Bold span count equal (`**x**`). Front matter keys equal and enum values unchanged (invariant I6).
- **Glossary** (`glossary_check.py`, invariant I7). A glossary has terms with `id`, `en`, `es` (the target rendering) and a list `banned`. Rules: every term has a non-empty `id`, `en` and target; IDs are unique; a banned word is a non-empty string; an approved rendering is not in its own banned list; a banned word is not the approved rendering of another term. Target rule: if the source segment holds a term, the target holds its approved rendering, and holds none of its banned words. Skip code, URLs and link destinations.
- **Chunks** (invariant I16 and the batch tool). A chunk ID plus the first 12 hex digits of the source digest is the request `custom_id`. A result with an unknown ID, a changed source digest, or an ID applied twice is rejected.
- **Untranslated** (invariant I9). Count the words of a prose segment (word = letters, with one inner apostrophe). Count the words that are in a list of unambiguous source-language function words (`the and of to is are was were that with for this you your not from it be can what which when if or by an at on in has have will would should does do been being their there then than these those into about because while where who how why also only just but more most some any each every other such both`; words that exist in the target language are left out of such a list). If the share is over a threshold, report the segment. Skip fences, inline code, URLs, link destinations, protected tokens, front matter and do-not-translate phrases.
- **Do-not-translate (DNT) phrases.** A text file with one phrase per line is protected text. Each DNT phrase of the source that appears in a segment must appear in the target (invariant I8). Match whole words only. The generator of such a list stays in the translation repository.
- **Negative fixtures.** Each known-bad fixture is a planted defect in a good control. The control must be clean, the fixture must fail, and it must fail for the stated rule (a whole-word match: `I6` must not match `I16`). A fixture that does not fail, or fails for another reason, is a defect of the test.
  The planted defects of the source tools that apply to the pack:

  | Defect | Rule family |
  | --- | --- |
  | a code span changes (`total > 40` becomes `total >= 40`) | fences, tokens |
  | a code span is dropped; a sentence with a number is dropped | tokens, digits |
  | the front matter key or an enum value is translated | front matter |
  | a macro ID changes (`[[entry:m4]]` becomes `[[entry:m5]]`) | tokens |
  | a Mermaid `accDescr` line is removed | Mermaid |
  | two Mermaid branch edges are swapped; one node ID is renamed in one edge only | Mermaid |
  | a paragraph, a table cell or a table row is deleted | chunks, structure |
  | a fence changes kind (`text` to `console`) | fences |
  | a heading is translated but a link keeps the source fragment | links |
  | a link goes to the source repository; an image comes from it | links |
  | a path is renamed, but a link keeps the old name; two files map to one name | links, mapping |
  | two chunks have one ID; a chunk is missing from the target; a source digest is stale | chunks |
  | a glossary term has a banned rendering in the target | glossary |
  | a segment is left in the source language | untranslated |

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| [p01-pack-contract](./steps/p01-pack-contract.md) | cloud agent | Pack layout, mapping parameters, shared helpers, the pack document. | none |
| [p02-fences](./steps/p02-fences.md) | cloud agent | `translation.fences`. | p01 |
| [p03-links](./steps/p03-links.md) | cloud agent | `translation.links`. | p01 |
| [p04-structure](./steps/p04-structure.md) | cloud agent | `translation.structure`. | p01 |
| [p05-glossary](./steps/p05-glossary.md) | cloud agent | `translation.glossary`. | p01 |
| [p06-chunks](./steps/p06-chunks.md) | cloud agent | `translation.chunks`. | p01 |
| [p07-markdown-pack](./steps/p07-markdown-pack.md) | cloud agent | `markdown.required-headings`, `markdown.front-matter`, `markdown.document-ids`. | p01 |
| [p08-untranslated](./steps/p08-untranslated.md) | cloud agent | `translation.untranslated-heuristic` (advisory). | p01 |
| [p09-fixtures-and-matrix](./steps/p09-fixtures-and-matrix.md) | cloud agent | Known-bad fixtures, mutation and fail-closed tests, fault matrix. | p02 to p08 |
| [p10-release-prep](./steps/p10-release-prep.md) | cloud agent | Docs, catalog page, changelog, version `0.2.0`, release check, history scan. | p09 |

## Parallelism

- `p01` runs first. It writes the only shared module of the pack, `checks/translation_common.py`.
- `p02` to `p08` run together. Each touches only its own module, catalog file, test file, fixture directory and step file. They must not edit `translation_common.py`, `docs/`, `controls.toml` or any file of another step. If a step needs a helper that does not exist, it puts the helper in its own module and writes that under "Resume notes" for the review. `loop.yaml` sets `jobs: 4`.
- `p09` waits for all of them. `p10` runs last.

## Risks

- **A secret or personal data is committed.** Fixtures hold synthetic text only. Build secret-like strings at run time. Do not add an exception to pass a step.
- **A check is not generic.** The text of each catalog `summary` and of `docs/translation-pack.md` states why the check works on any translation. A check that needs a language list takes it as a parameter.
- **A check passes when it should fail.** Every rule has a bad fixture that must fail for its own rule ID. `p09` adds mutation tests.
- **The pack breaks a repository that does not use it.** A check runs only if enabled. An enabled check without parameters passes. `p09` tests both.
- **An agent step cannot run a command.** Agent sessions cannot install packages, use the network, run Docker or write outside the worktree. If a command is denied, run a simpler one. If a step blocks three times on one denied command, write it under "Resume notes" and stop. The operator amends the step.
- **The wheel build needs the network.** `p10` builds a wheel inside the gate. If it cannot, write that under "Resume notes". Do not change the gate.
