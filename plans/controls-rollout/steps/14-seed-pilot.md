---
id: 14-seed-pilot
status: pending
depends_on: [09-runner-adopts-controls, 13-publish-template]
touches:
  - plans/controls-rollout/seeds/pilot/**
  - plans/controls-rollout/steps/14-seed-pilot.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave pilot && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `pilot` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/adopt-controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/pilot/` as [waves/pilot.tsv](../waves/pilot.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Write one seed for each pilot repository. Copy each repository brief from the archived ralphify `targets.md`. Use a cloud agent for a02 (no `local`) in the pilot.

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
