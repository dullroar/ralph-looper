---
id: t00-secret-guard
status: pending
depends_on: []
touches:
  - scripts/secret_guard.py
  - scripts/install_hooks.sh
  - tools/test_secret_guard.py
  - tools/test_registry.py
  - tools/inventory.py
  - tools/test_inventory.py
  - tools/test_scratch_proof.py
  - translation/tooling-allowlist.txt
  - .github/workflows/context.yml
  - .secret-guard-allow
  - plans/adopt-ralph/steps/t00-secret-guard.md
lane: none
gate: python3 -m unittest tools/test_secret_guard.py tools/test_registry.py tools/test_inventory.py && bash scripts/install_hooks.sh --self-test && python3 scripts/secret_guard.py --tracked && grep -q 'secret_guard.py --tracked' .github/workflows/context.yml && grep -q 'secret_guard.py --range' .github/workflows/context.yml && grep -q '^.github/workflows/context.yml' translation/tooling-allowlist.txt && python3 -I tools/verify.py --fast && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Install the secret guard first, and register every path of this plan

This repository has no secret guard. Secrets must never be committed. The guard is required from the first commit, with no advisory phase. This step also registers all the paths that later steps add, because `tools/verify.py` fails on an unregistered file.

## Change

- Copy `plans/adopt-ralph/reference/secret_guard.py` and `install_hooks.sh` to `scripts/`. Make the script executable. Copy `reference/test_secret_guard.py` to `tools/test_secret_guard.py`. Do not change their text. The test finds the guard at `../scripts/secret_guard.py`.
- Hooks in this clone. Run `python3 tools/lock_code.py --install-hook` first (it may say that the hook exists; that is fine). Then run `bash scripts/install_hooks.sh`. It keeps the lock hook as `pre-commit.local` and calls it after the guard. Do not bypass either hook.
- `.github/workflows/context.yml` (new workflow, name `context`, job `secret-guard`): triggers `pull_request`, and `push` to `loop/es-v4`. `permissions: contents: read`. Checkout with `fetch-depth: 0`. Step `Secret guard on all tracked files` runs `python3 scripts/secret_guard.py --tracked`. Step `Secret guard on every commit of the pull request`, for pull requests only, runs `python3 scripts/secret_guard.py --range "$BASE_SHA..$HEAD_SHA"`, with both values from `github.event.pull_request.base.sha` and `.head.sha` through `env:`. Pin each `uses:` to a full 40-character commit SHA, with the tag in a trailing comment. Find the SHA with `git ls-remote --tags https://github.com/actions/checkout`. If you have no network, write that under "Resume notes". Do not use a tag.
- Add `.github/workflows/context.yml  # t00: secret guard job (new workflow, not in English)` to `translation/tooling-allowlist.txt`.
- In `tools/inventory.py` add owned rules: files `AGENTS.md`, `CLAUDE.md`, `controls.toml`, `GUIA-DEL-REPO.md`, `.secret-guard-allow` in `OWNED_FILES`; prefixes `memory/`, `plans/`, `scripts/` in `OWNED_PREFIXES`. Make no other change there.
- `tools/test_registry.py`: assert that each of these paths is classed `owned`: the files above, `memory/AGENTS.md`, `plans/AGENTS.md`, `plans/adopt-ralph/steps/t01-baseline.md`, `scripts/check_context.py`, `tools/batch.py`, `translation/routing.md`. Assert that `lessons/unregistered-new-file.md` is not `owned` (known bad). Assert behavior, not counts.
- Run `python3 scripts/secret_guard.py --history` and write the finding count under "Resume notes" (it is a record, not a gate). If the guard finds a real secret, stop and write "blocked".
- Run the full tool test suite. Fix a test in `touches` only if your change made it obsolete.

## Do not change

- Files outside `touches`. The `gate` command.
- Do not add a row to `.secret-guard-allow` to pass the guard. If the guard finds something, remove the cause. A real false positive needs a reason and a fingerprint, and the owner reviews it.

## Already done by earlier steps

- None. This is the first step.

## Done when

- The gate passes. The guard test and the hook self-test pass. The guard finds nothing in tracked files.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
