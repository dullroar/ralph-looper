---
id: r02-probes
status: pending
depends_on: [r01-adopt]
touches:
  - docs/controls-adoption.md
  - plans/runner-adopts-controls/steps/r02-probes.md
lane: none
gate: python3 scripts/check_context.py && git check-ignore -q .probe/x && grep -q '^## Probes' docs/controls-adoption.md && for id in markdown.local-links context.index-freshness plans.schema security.secrets repo.forbidden-artifacts; do grep -q "$id" docs/controls-adoption.md || exit 1; done && git diff --check
evidence: ""
---

# Probe the controls

Goal: show that each core control fails on a planted defect in this repository, and passes on the clean copy.

## Facts you cannot find alone

- Work in a copy under `.probe/` in this worktree (`git clone -q . .probe/copy`). `.probe/` is excluded from Git. You cannot use `mktemp` or write outside the worktree.
- Plant one defect at a time, run `python3 -m deterministic_controls check --root .probe/copy --profile ci --format json`, read the rule ID from the JSON, then restore the copy. Defects: a broken local link, a stale generated index, a plan step without `gate`, a secret-shaped token built at run time (never commit it), a tracked forbidden file.
- Also run the shim in the copy on the step without a gate. It must exit non-zero.

## Record

Add a section `## Probes` to `docs/controls-adoption.md`: each defect, the exit code and the rule ID. Set `status: done` and fill `evidence`. If you cannot finish, write "Resume notes" below.

## Resume notes

(none)
