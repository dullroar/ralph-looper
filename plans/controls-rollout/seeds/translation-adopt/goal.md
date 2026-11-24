# Goal: move the Spanish edition onto the template layout and the Ralph runner

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `adopt-ralph` in this repository. Read `AGENTS.md` (if it exists), then `plans/adopt-ralph/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the full tool test suite (`python3 -m unittest discover -s tools -p 'test_*.py'`) and the `gate` command. If one fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, change a remote or change a GitHub setting. Never run `ralph-pusher`. Never run `loop/ralph.sh`. Never install packages, create a virtual environment or use the network.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

This repository is the Spanish edition of an English book. The English source is pinned in `translation/source.json`. Until now the work ran in a private loop (`loop/ralph.sh`, `loop/queue/*.jsonl`, `loop/STATE.md`). This plan moves the work onto the `repo-template` layout and the Ralph runner. It adds pinned CI controls, a written routing map and a Batch API tool.

This plan does **not** change translated content, PO files, locked code or the book build.

Library for the controls: `deterministic-controls` `v0.1.1`. Install line (for the operator and for CI, never for an agent step):

`python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@0323de273a158608f7280867e12994141bccd1e6"`

## Done when

- `python3 scripts/build_indexes.py --check`, `python3 scripts/check_context.py` and `python3 -I tools/verify.py --fast` pass.
- The secret guard runs in CI (`--tracked`, and `--range` on pull requests) and in the pre-commit and pre-push hooks. `secret_guard.py --history` is recorded.
- `translation/routing.md` maps every task kind of `loop/queue/**/*.jsonl` to a route, and `tools/check_routing_map.py` proves it.
- `tools/batch.py` has offline tests for build, submit (dry run), collect and reconcile.
- The old loop is marked as archived. `loop/STOP` and the queue history are unchanged.
- The results of `tools/verify.py` and the tool tests equal the baseline of t01, except for the files that this plan added.
- Every step of this plan is `done` with evidence.

## Out of scope

- Translated content, PO files, locked code, the book build and the English source pin.
- Pushing, publishing, a change of a remote or a GitHub setting. The pre-push hook of the repository. Required checks and branch protection.
- Running or resuming `loop/ralph.sh`. Removing `loop/STOP` (it is the Part III checkpoint of the owner).
- Running `tools/batch.py submit` for real. The operator does that later.
