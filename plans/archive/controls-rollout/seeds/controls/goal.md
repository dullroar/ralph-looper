# Goal: bootstrap the deterministic-controls library, release v0.1.0

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `bootstrap` in this repository. Read `AGENTS.md`, then `plans/bootstrap/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the `gate` command. If it fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, change a remote or change a GitHub setting. Never run `ralph-pusher`.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

This repository is `deterministic-controls`. It holds a small, versioned library of deterministic checks for repositories that follow the `repo-template` layout. The library runs the same checks in a developer shell, in a pre-commit hook and in CI. A check never changes a file. An agent never certifies its own work: the checks run independently and without condition.

This plan builds release `v0.1.0`. It has the core (CLI, manifest, result contract, catalog), the first checks (plans, index freshness, Markdown links, secrets, personal data, forbidden artifacts) and the adoption tools (audit, plan, apply, receipt). The repository must run its own checks in its own CI.

## Done when

- `python3 -m unittest discover -s tests -v` passes.
- `python3 -m deterministic_controls check --root . --profile full` exits `0` in this repository.
- `bash scripts/release_check.sh` passes from a clean clone. It prints the SHA-256 of the wheel.
- Every check has a known-good fixture that passes and known-bad fixtures that fail for the expected rule.
- The secret guard runs in CI, in the pre-commit hook and in the pre-push hook.
- Every step of this plan is `done` with evidence.

## Out of scope

- Tagging or publishing `v0.1.0`. The operator does that after the review.
- Language packs, translation checks, a `--fix` mode, a service, a database or a dashboard.
- Any repository other than this one.
