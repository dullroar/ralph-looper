---
id: p06-chunks
status: pending
depends_on: [p01-pack-contract]
touches:
  - src/deterministic_controls/checks/translation_chunks.py
  - src/deterministic_controls/catalog/translation.chunks.toml
  - tests/test_translation_chunks.py
  - tests/fixtures/translation_chunks/**
  - plans/translation-pack/steps/p06-chunks.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_translation_chunks.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the check `translation.chunks`

Read `plans/translation-pack/plan.md` first (pack contract, "Segments" and "Chunks"). Use `checks/translation_common.py` of `p01` without change. A chunk is a unit of source text with a stable ID and a digest. The check compares the chunks of a **source manifest** with the chunks that the target holds. It needs no Markdown parser.

## Change

- `checks/translation_chunks.py` with `entry(context)`. Parameters: `source_manifest` and `target_manifest`, paths to JSONL files. Source row: `id`, `path`, `digest` (SHA-256 hex of the source text). Target row: `id`, `path`, `source_digest`, optional `status` and optional `text` or `text_digest`. Define and document the row format in the module docstring and in the catalog `summary`. Stable rule IDs:
  - `.missing`: a source ID has no target row.
  - `.orphan`: a target ID is not in the source manifest.
  - `.duplicate`: an ID appears twice in one manifest.
  - `.stale`: the target `source_digest` differs from the source `digest`.
  - `.empty`: a target row has an empty text (when the row carries text).
  - `.fuzzy`: a target row has status `fuzzy` or `needs-review`.
  - `.bad-manifest`: a row is not valid JSON, lacks `id` or `digest`, or the file is missing. Never a pass.
- Optional parameter `custom_id_digits` (default `12`): rule `.custom-id` checks that a target row field `custom_id` equals `<id>` plus the first N hex digits of the source digest, for repositories that use a batch tool. Skip the rule when no row has `custom_id`.
- `catalog/translation.chunks.toml`: id `translation.chunks`, status `advisory`, severity `error`. The `summary` says why the check is generic.
- No `source_manifest` parameter: no findings.

## Fixtures and tests

Follow the fixture rule in `plan.md`. A good pair of manifests and one bad pair for each rule. Edge cases: two chunks with one ID in the source; a chunk ID that differs only by case; an ID applied twice in the target; an empty manifest (it passes only if both manifests are empty); a blank line in the JSONL file; a row with a Unicode ID. Compute digests in the test (`hashlib`), do not store opaque literals that nobody can check. The test asserts for each bad fixture the rule ID, the path and exit code `1`. Good fixtures give exit `0`.

## Do not change

- Files outside `touches`. The `gate` command. `translation_common.py`.

## Already done by earlier steps

- p01-pack-contract: the parameter loader, the finding and exception helpers.

## Done when

- The gate passes. Each bad fixture fails for its own rule. Each good fixture passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
