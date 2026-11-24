# Goal: add the translation and Markdown pack to deterministic-controls, release v0.2.0

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `translation-pack` in this repository. Read `AGENTS.md`, then `plans/translation-pack/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the full unit test suite (`python3 -m unittest discover -s tests -v`) and the `gate` command. If one fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, tag, change a remote or change a GitHub setting. Never run `ralph-pusher`. Never install packages, create a virtual environment or use the network.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

This repository is `deterministic-controls`. It holds a small, versioned library of deterministic checks for repositories that follow the `repo-template` layout. Release `v0.1.2` has the core, seven checks and the adoption tools.

This plan builds release `v0.2.0`: an opt-in **translation and Markdown pack**. The pack holds the generic checks for any Markdown-to-Markdown translation that has a source manifest. A Spanish edition of an English book already runs mature, tested checks in its own `tools/`. This plan promotes the generic parts. Project-specific parts stay in that repository. These are the oracle families, the BICHO acronym rules, the path maps and the locale layer.

A check goes into the pack only if it is useful for any Markdown-to-Markdown translation with a source manifest. Each check step writes down that test for its check, in the check's catalog summary and in `docs/translation-pack.md`.

## Done when

- `python3 -m unittest discover -s tests -v` passes.
- Each new check has a good fixture and a bad fixture for each rule. The tests assert the rule ID, the path and the exit code.
- A repository that has no translation configuration passes with the pack present. Enabling a pack check without its parameters does not fail the run.
- `python3 -m deterministic_controls check --root . --profile full` exits `0` in this repository.
- `bash scripts/release_check.sh` passes from a clean clone.
- The version is `0.2.0` in `pyproject.toml` and in `src/deterministic_controls/__init__.py`.
- `python3 scripts/secret_guard.py --history` is run and its finding count is recorded.
- Every step of this plan is `done` with evidence.

## Out of scope

- Tagging or publishing `v0.2.0`. The operator does that after the review.
- Language packs, toolchain packs, a `--fix` mode, a service, a database or a dashboard.
- Spanish-specific rules (register, inverted marks, stopword lists for one language, locale catalogs, oracle families, acronym rules, path maps). They stay in the translation repository.
- Any repository other than this one. The child has no copy of the translation repository: all facts it needs are in `plan.md` and in the step files.
