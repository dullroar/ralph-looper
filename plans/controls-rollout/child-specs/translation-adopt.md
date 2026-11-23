# Child spec: `adopt-ralph` in aprende-a-programar-como-un-bicho-raro

Wave `translation-adopt`. Base branch: `translation_branch` in [decisions.tsv](../decisions.tsv) (default `loop/es-v4`). This child moves the Spanish edition from its private loop (`loop/ralph.sh`, `loop/queue/*.jsonl`, `loop/STATE.md`) onto the `repo-template` layout and the Ralph runner. It adds pinned CI controls, a written routing map and a Batch API tool. It does **not** change translated content, PO files, locked code or the book build.

## Facts to copy into the seed

- The repository is an edition of an English source pinned in `translation/source.json`. `tools/verify.py` checks that every tracked file maps to the pinned English source, or is registered as edition-owned. A new tracked file that is not registered fails invariant `I1` (the `TRANSLATING.md` blocker of iteration 192 is the example). Register each new edition-owned path in the inventory or allowlist that `tools/verify.py` reads, as H3-001 to H3-002 did for the guides.
- `docs/` is book content (translated from English `docs/`). It is not the template's human-docs folder. Do not add `docs/README.md` unless registration makes `verify.py --fast` pass. If it does not, put the human-docs index in a new edition-owned file (for example `GUIA-DEL-REPO.md`) and record the deviation in `AGENTS.md`.
- `tools/lock_code.py --install-hook` installs a pre-commit hook that protects locked code. Install it in each worktree. Never bypass it.
- The pre-push hook allows only `loop/push-backup.sh` to push `loop/es-v4`. Do not change it in this child. The operator changes it if the decision row `translation_push` says so.
- `loop/STOP` is Jim's Part III checkpoint (`review/CHECKPOINT-part3.md`). Keep it. Do not run or resume `loop/ralph.sh`.
- `review/packets/`, `review/repo-bundle.zip`, `review/canaries.key.json` and `review/units.index.jsonl` must stay untracked.
- The existing CI: `pdf-release-gate.yml`, `sandbox-gate.yml`. Keep them and their job names.
- `tools/translate.py` already exports masked pending segments (`--export-pending`) and imports drafts (`--drafts ... --draft-model ... --task-id ...`) with full schema, placeholder and invariant checks. The batch tool uses these two paths. It does not duplicate them.
- `tools/model_report.py` and `loop/ledger/usage.jsonl` (untracked) hold the cost history by task kind and model.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| t01-baseline | cloud agent, light | Record the current verification results. | none |
| t02-layout | local, fallback cloud | Template layout and agent contract, registered as edition-owned. | t01 |
| t03-memory | local, fallback cloud | One memory file for each trap in `loop/SIGNS.md`. | t02 |
| t04-controls | cloud agent | Pinned controls in advisory CI, plus `verify.py --fast` in CI. | t02 |
| t05-routing-map | cloud agent | Measured routing map for every task kind. | t02 |
| t06-batch-tool | cloud agent | `tools/batch.py` for the Message Batches API, with offline tests. | t02 |
| t07-archive-loop | local, fallback cloud | Mark the old loop as archived. Point to the new plans. | t03, t04 |
| t08-verify | cloud agent | Prove that the new layout and the old results agree. | t05, t06, t07 |

t02 runs first and registers every path that this child adds. After t02, t03, t04, t05 and t06 run together. Only t02 touches the edition-owned registry, so their `touches` do not overlap.

## Step details

- **t01.** Touches its step file. Record: `python3 -I tools/verify.py --fast` result, `python3 -I tools/verify.py --release --no-gates` result, the tool test count (`python3 -m unittest discover -s tools -p 'test_*.py'`), `python3 tools/next_task.py --counts`, the tracked file count and the `git status` summary. These are the numbers that t08 must reproduce.
- **t02.** Touches `AGENTS.md`, `CLAUDE.md`, `memory/AGENTS.md`, `plans/AGENTS.md`, `plans/for-each-plan/**`, `scripts/**`, the human-docs index file, and the edition-owned registry file that `verify.py` reads. Register all paths that this child adds, also those of later steps: `AGENTS.md`, `CLAUDE.md`, `memory/**`, `plans/**`, `scripts/**`, the human-docs index, `controls.toml`, `.github/workflows/context.yml`, `translation/routing.md`, `tools/check_routing_map.py`, `tools/batch.py`, `tools/test_batch.py`, `tools/fixtures/batch/**`, `translation/prompts/batch-*.md`. `AGENTS.md` carries: the template rules; the authorization limits of section 11.8 of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md`; the locked-code and pinned-source rules; links to `repo-template` and `ralph-looper`, with the rule "Before changing this repository's structure, read both and account for their contracts." `CLAUDE.md` is `@AGENTS.md`. Copy `scripts/build_indexes.py`, `scripts/ctx_common.py` and `scripts/check_context.py` from the pinned template. Add `scripts/verify_fast.sh` that runs `python3 -I tools/verify.py --fast` with a `Run me when:` line. Gate: `python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 -I tools/verify.py --fast && git diff --check`.
- **t03.** Touches `memory/*.md` and `memory/AGENTS.md`. One file for each trap in `loop/SIGNS.md` and `loop/STATE.md` "Traps to remember", with a `gist` line. No local paths: replace them with placeholders. Gate as t02.
- **t04.** Touches `controls.toml`, `scripts/controls-requirements.txt`, `scripts/check_context.py`, `scripts/AGENTS.md`, `.github/workflows/context.yml`. Use `adopt apply` from the pinned library where it fits. Add `review/canaries.key.json`, `review/packets/**`, `review/repo-bundle.zip`, `review/units.index.jsonl` and `loop/driver.out*` to `repo.forbidden-artifacts`. The `context` workflow runs the controls and `python3 -I tools/verify.py --fast` on pull requests and on pushes to the base branch, with `permissions: contents: read` and pinned actions. It is advisory. Gate: t02 gate plus a probe: a temporary tracked `review/canaries.key.json` in a scratch copy fails `repo.forbidden-artifacts`.
- **t05.** Touches `translation/routing.md`, `tools/check_routing_map.py` and its step file. Use `python3 tools/model_report.py` and the ledger to measure cost, wall time and retry rate by task kind and model for the 549 iterations. Map each task kind to a route with the reason and the measurement:
  - Deterministic: segmenting, masking, invariants, oracle runs, link and anchor audits, packet building, `msgmerge`, impact maps, builds, imports, reports. Route `script` or CI.
  - Bulk drafts of new and fuzzy segments, minimal-edit deltas, automated reviewer passes, back-translation, canary scoring input. Route: Batch API through `tools/batch.py`, submitted by the operator, imported by a `script` step.
  - Bounded tool fixes, fixture additions, doc moves. Route `local` with a cloud fallback, only for kinds where the gate is strong.
  - Adjudication, review-fix with judgment, new tooling, prompt changes. Route: cloud agent, standard tier, with a model different from the one that produced the work under review.
  - Jury with outside vendors, native-speaker humor review, approvals, upstream pull requests, publication. Route `operator`.
  Record the expected cost change for each move from the measured history. Gate: `python3 tools/check_routing_map.py` passes. It checks that every task kind in `loop/queue/**/*.jsonl` has a row with a route from the list above, and that every row has a reason and a measurement or `no history`. Then `python3 scripts/check_context.py && python3 -I tools/verify.py --fast`.
- **t06.** Touches `tools/batch.py`, `tools/test_batch.py`, `tools/fixtures/batch/**`, and `translation/prompts/batch-*.md` if needed. t02 registered these paths. Commands: `build` (read `translate.py --export-pending` JSONL or reviewer input JSONL, write a request file; `custom_id` = segment ID plus the first 12 hex digits of the source hash; the stable style guide and glossary go in a cached system block), `submit` (needs `ANTHROPIC_API_KEY` in the environment and `--max-usd`; refuses without both; prints the batch ID), `status`, `collect` (write a drafts JSONL that `translate.py --drafts` accepts, and a cost record), and `reconcile` (reject results whose `custom_id` does not match a current pending segment or whose source hash changed; never apply a result twice). `--dry-run` writes nothing. The model ID is a required argument. The tool never runs in CI and never runs in an agent step. Tests use recorded fixture responses only, with no network: success, partial errors, expired requests, a duplicate result and a stale source hash. Gate: `python3 -m unittest tools/test_batch.py && python3 -I tools/verify.py --fast && git diff --check`.
- **t07.** Touches `loop/STATE.md`, `loop/RUN.md`, `README.md` (the contributor section only, through its PO source if the README is generated; check first) and its step file. Mark the old loop as archived at the current queue state. Say where new work lives (`plans/`). Do not delete `loop/` files, `loop/STOP` or the queue history. Gate: t02 gate.
- **t08.** Touches its step file. Run the t01 commands again. The results must equal the t01 baseline, except for the files that this child added and registered. Run the runner's `--status` view on a scratch clone to show that `plans/` is valid. Record the comparison.
