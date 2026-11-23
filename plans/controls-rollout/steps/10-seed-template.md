---
id: 10-seed-template
status: pending
depends_on: [08-record-pin]
touches:
  - plans/controls-rollout/seeds/template/**
  - plans/controls-rollout/steps/10-seed-template.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave template && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `template` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/template.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/template/` as [waves/template.tsv](../waves/template.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Apply `lessons/controls.md`. In m04, list the old checker scripts that the step deletes in its `touches`.

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
