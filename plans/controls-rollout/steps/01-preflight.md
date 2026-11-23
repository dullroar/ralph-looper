---
id: 01-preflight
status: pending
depends_on: []
touches:
  - plans/controls-rollout/steps/01-preflight.md
lane: none
tier: light
gate: for c in step-agent operator-step script-step local-agent gate-from-plan-branch touches-enforced; do ./ralph-looper --capabilities | grep -qx "$c" || exit 1; done && python3 lib/fanout.py --help >/dev/null && python3 lib/report.py --help >/dev/null && python3 scripts/check_records.py plans/runner-routing/baseline.tsv --min-rows 13 && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Check the runner features, the baseline and the drift since it

This plan needs the [runner-routing](../../runner-routing/plan.md) features. The gate checks them in this worktree, which comes from `main`. If it fails, `runner-routing` is not merged. Stop and record that as a blocker.

## Do

1. Compare each `commit` in `plans/runner-routing/baseline.tsv` with the current default-branch commit of that repository under `$REPOS_ROOT` (`git -C ... rev-parse <base>`). Read only.
2. For each repository that moved, list the commits (`git log --oneline <old>..<new>`) and say if they change layout, checks, CI or Docker gates.
3. Confirm that `gh` is signed in (`gh auth status`) and that Docker answers (`docker version`). Do not change anything.
4. Record the results below. Do not write local paths.

## Results

(fill in)

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
