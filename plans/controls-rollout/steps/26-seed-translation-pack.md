---
id: 26-seed-translation-pack
status: pending
depends_on: [24-review-translation-adopt]
touches:
  - plans/controls-rollout/seeds/translation-pack/**
  - plans/controls-rollout/steps/26-seed-translation-pack.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-pack && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `translation-pack` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-pack.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-pack/` as [waves/translation-pack.tsv](../waves/translation-pack.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Read the translation tools listed in the spec at `plan/adopt-ralph` in the translation repository (read only, with `git show`). Copy the rules, edge cases and negative fixtures that the child needs into the seed. Apply `lessons/controls.md` and `lessons/translation-adopt.md`.

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
