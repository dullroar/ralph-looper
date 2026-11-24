---
id: r03-publish
status: pending
depends_on: [r02-probes]
touches:
  - plans/runner-adopts-controls/steps/r03-publish.md
lane: none
agent: operator
gate: git fetch -q origin && for f in controls.toml docs/controls-adoption.md scripts/controls-requirements.txt; do git cat-file -e origin/main:$f || exit 1; done && test "$(gh api 'repos/{owner}/{repo}/rules/branches/main' --jq '[.[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context] | sort | join(",")')" = check,controls,runner-tests
evidence: ""
---

# Operator: publish and require the checks

1. Push `plan/runner-adopts-controls`, open a pull request to `main`, wait for CI, merge with a merge commit.
2. Add `controls` and `runner-tests` to the required checks of the `ralph-looper` ruleset (keep `check`). Read it back.

The gate checks that the adoption files are on `origin/main` and that the ruleset requires exactly `check`, `controls` and `runner-tests`.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
