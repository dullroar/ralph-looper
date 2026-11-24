---
id: 03-seed-controls
status: done
depends_on: [01-preflight, 02-owner-decisions, 04-create-controls-repo]
touches:
  - plans/controls-rollout/seeds/controls/**
  - plans/controls-rollout/steps/03-seed-controls.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave controls && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-23T23:39:50Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Write the seed for the `controls` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/controls/` as [waves/controls.tsv](../waves/controls.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

This is the first seed. `lessons/` is empty. Write `loop.yaml` with `jobs: 4` so that the child runs its parallel steps together. Give each step the executor from the spec. Use `agent: local` with `fallback:` set to the `child_agent` decision for the four port steps.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

The seed is in `seeds/controls/`. It follows the spec, with these differences. Each one follows a fact in the target.

- **New step `b00-secret-guard`.** The target is a copy of `repo-template`. It has no secret guard. The contract and decision `secret_guard` need the guard from the first commit, but the spec adds it only in `b06`. `b00` installs the runner guard, the hooks and the CI job first. The child cannot read this repository, so the seed carries copies in `seeds/controls/reference/` (`secret_guard.py`, `install_hooks.sh`, `test_secret_guard.py`). The copies are from this branch, with no change.
- **`b00` and the generated indexes.** The seeded `plans/bootstrap/plan.md` makes `plans/AGENTS.md` of the target stale. The target step gates run `check_context.py`, which checks the indexes. A seed cannot write outside `plans/bootstrap/`. So `b00` regenerates `plans/AGENTS.md` and `scripts/AGENTS.md`. `b09` and `b10` also touch `scripts/AGENTS.md`, because they add or change scripts.
- **`b09` also depends on `b08`.** `b09` replaces `scripts/check_context.py` with the shim that `b08` writes. The spec lists only `b04` to `b07`. In this repository the shim runs the library from `src/` (dogfood mode), not from a cached environment.
- **Check registration.** The spec says that `list` reads one catalog file for each check, but not how `check` finds the code. The seed adds the catalog keys `module`, `entry` and `mandatory`. `b06` needs `mandatory` for the rule that `security.secrets` cannot be disabled.
- **Fixtures.** The template checks scan all Markdown files. Bad Markdown fixtures would fail them. The seed sets a fixture rule: Markdown fixture files end in `.fixture`, and secrets, personal paths and forbidden tracked files are built at run time.
- **Gates.** Gates that run the package use `PYTHONPATH=src`. The package is not installed in the repository.
- **Receipt fields.** The spec points to section 8.2 of the source plan. The source plan is not in this repository. `b08` lists the receipt fields itself (revision, pin, profile, checks, files, commands kept, enforcement state, rollback).
- **Pins.** `pins.tsv` has no row yet. The `bootstrap` child builds the library, so it needs no install line. `b08` writes the install line with the placeholder `<commit>` into its templates.
- **Gate check.** `fanout.py ready` runs only the target plan checker. It does not run `check_context.py` on the seed. A later review step should check that the child step gates pass in the first iteration.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
