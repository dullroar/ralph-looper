---
id: r04-archive
status: pending
depends_on: [r03-publish]
touches:
  - plans/runner-adopts-controls/steps/r04-archive.md
lane: none
agent: operator
gate: git fetch -q origin && git cat-file -e origin/main:plans/archive/controls-rollout/plan.md && git cat-file -e origin/main:plans/archive/runner-routing/plan.md && ! git cat-file -e origin/main:plans/controls-rollout/plan.md 2>/dev/null
evidence: ""
---

# Operator: archive the finished plans

In a separate pull request from `main`: `git mv plans/controls-rollout plans/archive/` and `git mv plans/runner-routing plans/archive/`. Fix links that break. Run `python3 scripts/build_indexes.py` and `python3 scripts/check_context.py`. Merge with a merge commit.

## Record

The driver sets `status: done` and writes `evidence` when the gate passes.
