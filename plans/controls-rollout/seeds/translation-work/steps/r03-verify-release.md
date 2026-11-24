---
id: r03-verify-release
status: pending
depends_on: [r02-publish]
touches:
  - plans/v4-es-1/steps/r03-verify-release.md
lane: none
agent: script
run: python3 plans/v4-es-1/gatelib.py verify-release plans/v4-es-1/records/r02-publish.md
gate: python3 plans/v4-es-1/gatelib.py verify-release plans/v4-es-1/records/r02-publish.md
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Script: check the published assets against the build

No model work. The command downloads each asset of the release `v4-es.1` (public GitHub API, no credentials) and compares its SHA-256 with the `asset:` lines of `plans/v4-es-1/records/r01-release-gates.md`. A missing asset, an extra difference in a name or a different hash fails the step.

## Do not change

- Files outside `touches`. The `gate`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
