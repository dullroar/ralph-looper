# Goal: ralph-looper adopts the deterministic controls

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `runner-adopts-controls` in the `ralph-looper` repository. Read `AGENTS.md`, then `plans/runner-adopts-controls/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the `gate` command. If it fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

`ralph-looper` runs the controls of every other repository, but it does not run them itself. Step `09-runner-adopts-controls` of `controls-rollout` is marked done, but no commit adds the pin, `controls.toml` or `docs/controls-adoption.md` (final audit, item B1). This plan closes that gap.

## Done when

- `scripts/controls-requirements.txt` pins `deterministic-controls` v0.2.0 (`d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5`). `controls.toml` exists. `scripts/check_context.py` is the library shim and passes.
- `.github/workflows/context.yml` has the jobs `check` (kept), `controls` and `runner-tests`. Every action is pinned to a full commit SHA. No job has a path filter, `continue-on-error` or a secret.
- The probes in a `.probe/` copy fail with the expected rule IDs. The record is in `docs/controls-adoption.md`.
- The pull request is merged, and the ruleset of `ralph-looper` requires `check`, `controls` and `runner-tests`.
- `plans/controls-rollout/` and `plans/runner-routing/` are in `plans/archive/`.
