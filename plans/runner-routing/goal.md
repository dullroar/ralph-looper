# Goal: upgrade the runner for routed, multi-repository plans

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `runner-routing` in the `ralph-looper` repository. Read `AGENTS.md`, then `plans/runner-routing/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the `gate` command. If it fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Keep the bash and PowerShell drivers equal in behavior. Change both in the same commit.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

Make `ralph-looper` the tool that the [controls rollout](../controls-rollout/plan.md) needs. When this plan is done, one plan can mix executors step by step: a coding agent, a local model, a deterministic script, or an operator action. The driver itself guarantees that an agent cannot change its own gate or work outside `touches`. One tested fan-out tool replaces the two plan-local launchers of 2026-11-22. A route report shows what each executor cost and how often its first attempt passed. A deterministic secret guard makes sure that no secret is tracked, committed or pushed, in any repository.

This plan is the first increment. It uses the current driver. Every later plan runs on the driver that this plan produces.

## Done when

- `bash tests/run.sh`, `python3 tests/test_fanout.py`, `python3 tests/test_report.py`, `python3 tests/test_check_records.py` and `python3 tests/test_secret_guard.py` pass.
- `scripts/secret_guard.py` finds tokens, passwords, private keys and forbidden files in commits, pushes, CI and the driver before each merge. `scripts/install_hooks.sh` installs the hooks. The history audit of all repositories is recorded.
- `./ralph-looper --capabilities` prints `step-agent`, `operator-step`, `script-step`, `local-agent`, `gate-from-plan-branch` and `touches-enforced`, one for each line.
- `python3 lib/fanout.py --help` lists `ready`, `provision`, `run`, `status`, `verify` and `published`.
- `python3 lib/report.py` summarizes a ledger by agent, route and model.
- `plans/runner-routing/baseline.tsv` records the 13 repositories and passes `scripts/check_records.py`.

## Out of scope

- The shared controls library. The [controls rollout](../controls-rollout/plan.md) builds it.
- Changes to any other repository. This plan only reads the other repositories.
- A scheduler, a database, a service or a new policy language.
- Calls to a model API from the driver. Batch API work is a plan-level tool in the repository that uses it.
