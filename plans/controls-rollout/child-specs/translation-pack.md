# Child spec: `translation-pack` in deterministic-controls

Wave `translation-pack`. Release `v0.2.0`. Source phase: 11, packs A and B. The translation repository has many mature, tested checks in `tools/`. Promote the generic parts into the shared library. Keep the project-specific parts (oracle families, BICHO acronym rules, path maps, the locale layer) in the translation repository. A check goes into the library only if it is useful for any Markdown-to-Markdown translation with a source manifest. Write down that test for each check.

## Sources to read (in the translation repository, at the adoption commit)

`tools/invariants.py`, `tools/mask.py`, `tools/segment.py`, `tools/glossary_check.py`, `tools/link_audit.py`, `tools/anchors.py`, `tools/mermaid.py`, `tools/dnt.py`, `tools/negative.py`, `tools/part2_negative.py` and their tests. Copy the facts that the child needs into the seed. The child does not have that repository.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| p01-pack-contract | cloud agent | Pack layout, source-to-target mapping parameters in `controls.toml`, shared fixtures layout. | none |
| p02-fences | local, fallback cloud | `translation.fences`: fenced code blocks are byte-identical where protected; fence count and language tags match. | p01 |
| p03-links | local, fallback cloud | `translation.links`: URLs, relative paths and anchors match under the mapping rules. | p01 |
| p04-structure | local, fallback cloud | `translation.structure`: tables and cell counts, footnotes, Mermaid fences, headings count. | p01 |
| p05-glossary | local, fallback cloud | `translation.glossary`: machine-readable glossary with exceptions. | p01 |
| p06-chunks | local, fallback cloud | `translation.chunks`: missing or duplicate chunk IDs and digests against a manifest. | p01 |
| p07-markdown-pack | cloud agent | Pack A additions: required headings and front matter keys, stable document IDs. Lint style stays advisory. | p01 |
| p08-untranslated | cloud agent | `translation.untranslated-heuristic`: advisory only, never `required`. | p01 |
| p09-fixtures-and-matrix | cloud agent | Known-bad fixtures from the translation repository's negative tests, mutation tests, fault matrix update. | p02 to p08 |
| p10-release-prep | cloud agent | Docs, catalog, changelog, version `0.2.0`, release check. | p09 |

Each check step touches only its module, catalog file, tests and fixtures. The pack is opt-in. A repository with no translation manifest must not fail because the pack exists.

## Acceptance

- Each check has a good fixture and a bad fixture for each rule, with rule ID, path and exit code asserted.
- On the translation repository at the adoption commit, each check gives the same pass or fail result as the matching local tool (record any difference and its cause in the step).
- `bash scripts/release_check.sh` passes from a clean clone.
