---
id: 35-route-report
status: done
depends_on: [21-publish-fleet, 32-publish-translation-work]
touches:
  - plans/controls-rollout/route-report.md
  - plans/controls-rollout/steps/35-route-report.md
lane: none
agent: script
run: python3 lib/report.py --work "$RALPH_WORK" --by plan --format md > plans/controls-rollout/route-report.md
gate: test -s plans/controls-rollout/route-report.md && grep -q '|' plans/controls-rollout/route-report.md && python3 scripts/check_context.py && git diff --check
claimed_by: script cli-default
claimed_at: "2026-11-24T15:31:41Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Write the route report for the program

Script step. The driver runs `run` and then the gate. No model is used. The report has no paths and no prompts. `check_context` scans it for secrets and personal paths.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
