---
id: 22-seed-translation-adopt
status: blocked
depends_on: [09-runner-adopts-controls, 13-publish-template]
touches:
  - plans/controls-rollout/seeds/translation-adopt/**
  - plans/controls-rollout/steps/22-seed-translation-adopt.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-adopt && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the seed for the `translation-adopt` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-adopt.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-adopt/` as [waves/translation-adopt.tsv](../waves/translation-adopt.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Read the translation repository under `$REPOS_ROOT` (read only) to confirm the facts in the spec: the edition-owned registry that `tools/verify.py` reads, how `README.md` and `CONTRIBUTING.md` are generated, and the task kinds in `loop/queue`. Put the confirmed facts in the seed. Apply `lessons/controls.md` and `lessons/template.md`.

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
