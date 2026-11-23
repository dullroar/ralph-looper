---
id: 31-seed-translation-work
status: pending
depends_on: [25-publish-translation-adopt, 30-record-pack-pin]
touches:
  - plans/controls-rollout/seeds/translation-work/**
  - plans/controls-rollout/steps/31-seed-translation-work.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-work && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `translation-work` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-work.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-work/` as [waves/translation-work.tsv](../waves/translation-work.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

This is the most important seed of the program. Read `translation/routing.md`, `review/CHECKPOINT-part3.md`, `translation/part3/spanish-adoption-plan-draft.md` and sections 7 to 9, 11.9 and 12 of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md` in the translation repository at its working branch (read only). Apply all lessons files. Use the `v0.2.0` pin for step x01.

Give every step its executor from the spec and the routing map. Give each operator step exact instructions and a gate that checks the outside result. Give each batch step a USD cap placeholder that Jim must set, and make the gate fail while the placeholder is there. Make the lanes independent as the spec says, so that `--jobs 4` runs them together.

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
