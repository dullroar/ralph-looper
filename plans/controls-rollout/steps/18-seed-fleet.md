---
id: 18-seed-fleet
status: pending
depends_on: [17-publish-pilot]
touches:
  - plans/controls-rollout/seeds/fleet/**
  - plans/controls-rollout/steps/18-seed-fleet.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave fleet && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `fleet` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/adopt-controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/fleet/` as [waves/fleet.tsv](../waves/fleet.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Write one seed for each of the eight fleet repositories. Apply `lessons/pilot.md`. Use a cloud agent for a02 (no `agent: local`). If `## Library defects` in any lessons file is not `none` and no newer pin fixes it, set this step `blocked` with the reason.

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
