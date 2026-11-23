---
id: 03-seed-controls
status: pending
depends_on: [01-preflight, 02-owner-decisions, 04-create-controls-repo]
touches:
  - plans/controls-rollout/seeds/controls/**
  - plans/controls-rollout/steps/03-seed-controls.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave controls && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `controls` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/controls/` as [waves/controls.tsv](../waves/controls.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

This is the first seed. `lessons/` is empty. Write `loop.yaml` with `jobs: 4` so that the child runs its parallel steps together. Give each step the executor from the spec. Use `agent: local` with `fallback:` set to the `child_agent` decision for the four port steps.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

(none)

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
