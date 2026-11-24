---
id: t06-batch-tool
status: pending
depends_on: [t02-layout]
touches:
  - tools/batch.py
  - tools/test_batch.py
  - tools/fixtures/batch/**
  - translation/prompts/batch-*.md
  - plans/adopt-ralph/steps/t06-batch-tool.md
lane: none
gate: python3 -m unittest tools/test_batch.py && python3 scripts/build_indexes.py --check && python3 -I tools/verify.py --fast && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write `tools/batch.py` for the Message Batches API

The operator submits bulk drafts and reviews through the Message Batches API. The tool never runs in CI and never runs in an agent step. Tests use recorded fixtures only, with no network. Use the standard library only (`urllib`), no SDK.

## Change

- Reuse `tools/translate.py`: `--export-pending` writes the masked pending segments. `--drafts ... --draft-model ... --task-id ...` imports drafts with all checks. The batch tool uses these two paths. It does not copy their logic.
- `build`: read `--export-pending` JSONL or reviewer input JSONL. Write a request file. `custom_id` is the segment ID plus the first 12 hex digits of the source hash. The stable style guide and glossary go in one `system` block with `cache_control` `{"type": "ephemeral"}`. The model ID is a required argument. Prompts that the tool needs go to `translation/prompts/batch-*.md`.
- `submit`: needs `ANTHROPIC_API_KEY` in the environment and `--max-usd`. It refuses without both. It prints the batch ID. It reads the running total from the cost records and refuses a submission whose cap would take the total over USD 100 (program cap, owner decision of 2026-11-23). Each submission records its own cap and the running total.
- `status`; `collect` (write a drafts JSONL that `translate.py --drafts` accepts, and a cost record); `reconcile` (reject results whose `custom_id` does not match a current pending segment or whose source hash changed; never apply a result twice). `--dry-run` writes nothing.
- Secrets. The tool reads the key only from `ANTHROPIC_API_KEY`. It never writes the key, the request headers or a full response envelope to a file or a log. A test builds a synthetic key at run time and proves that it does not appear in any file that `build`, `submit --dry-run` or `collect` writes.
- Fixtures in `tools/fixtures/batch/` (recorded responses, JSONL): success, partial errors (`errored`), expired requests, a duplicate result and a stale source hash. A batch result line has `custom_id` and `result.type` (`succeeded`, `errored`, `canceled` or `expired`). Test each case. A case that the tool must refuse is a known-bad fixture. Write a fixture that holds a secret at run time. Never store it.
- A test that submits for real is not allowed. Inject the HTTP function in tests.

## Do not change

- Files outside `touches`. The `gate` command. `tools/translate.py` (use it, do not edit it).
- Never call the network. Never run `submit` without `--dry-run`.

## Already done by earlier steps

- t02-layout: the registration (`tools/` and `translation/` are owned) and `build_indexes.py`.

## Done when

- The gate passes. Run the full tool test suite before you commit.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
