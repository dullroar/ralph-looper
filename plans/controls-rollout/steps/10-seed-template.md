---
id: 10-seed-template
status: done
depends_on: [08-record-pin]
touches:
  - plans/controls-rollout/seeds/template/**
  - plans/controls-rollout/steps/10-seed-template.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave template && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-24T01:41:52Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Write the seed for the `template` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/template.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/template/` as [waves/template.tsv](../waves/template.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Apply `lessons/controls.md`. In m04, list the old checker scripts that the step deletes in its `touches`.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

Differences from the spec [template.md](../child-specs/template.md), with the reason:

- Added step `m00-secret-guard`. The child plan contract needs the secret guard, the hooks and a blocking CI step in the first adoption commit. The template has none of them. The spec has no step for this. `m01` and `m02` depend on `m00`. The three reference files are in `seeds/template/reference/`. They equal the runner copies on 2026-11-24.
- `m01` also touches `.github/workflows/context.yml`. `adopt apply` writes a `controls` job there. `m03` then sets the final form. `m00`, `m01` and `m03` run one after the other, so there is no overlap.
- `m02` also touches `plans/AGENTS.md` and `docs/README.md` (the docs index is edited by hand). `m05` also touches `docs/README.md`. They run one after the other.
- `m03` has its own test, `tests/test_workflow.py`, for the workflow rules. The spec has no test for it.
- `m04` touches the old scripts that it deletes (lessons: `controls.md`, first "Change" rule) and `scripts/AGENTS.md`. Every step text tells the agent to run the full unit suite (second rule).
- `docs/routing.md` text is written in `m02` from the routing policy facts, without the `local` route (owner decision 2026-11-23). The seed links only the public URL.
- No step uses `agent: local`. No step compares wheel digests.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
