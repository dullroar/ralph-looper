# Bring ten repositories onto the template and Ralph runner

## Ralph loop prompt

> Read `AGENTS.md`, this file, `plan.md`, and the assigned step. Work only in your `ralph-looper` step worktree and only on files in `touches`. Run the step gate and commit your work. Keep the gate intact. Record a blocker or resume notes if you cannot finish. The operator launches the target runs between the parent steps. Each target agent follows its own repository's `AGENTS.md` and child plan.

## Goal

Adopt the [repository template](https://github.com/dullroar/repo-template) and make plans runnable with `ralph-looper` in the ten repositories named in the [allowlist](./targets.tsv). Keep product behavior, repository history, and existing entry points. Use one child plan and one independent Docker build and test per target. Keep the parent plan and its launch tools here.

## Done when

- Each target's `AGENTS.md` links to both upstream repositories and requires future structure changes to account for their contracts. Each target has the template layout, generated indexes, a working context check, and a completed `ralphify` plan.
- Each target's `README.md` gives exact, repeatable Docker build and test commands and shows how to run a local plan. Each image runs that repo's real test gate with project-specific coverage. The two FUSE repos also pass a real mount test in Docker.
- Each target has a completed local `plan/ralphify` branch with context and Docker evidence. The parent gate checks the recorded target commits and results. Base branches are ready for owner review. The approved target list is the write boundary for migration work.
