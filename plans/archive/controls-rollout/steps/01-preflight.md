---
id: 01-preflight
status: done
depends_on: []
touches:
  - plans/controls-rollout/steps/01-preflight.md
lane: none
tier: light
gate: for c in step-agent operator-step script-step local-agent gate-from-plan-branch touches-enforced; do ./ralph-looper --capabilities | grep -qx "$c" || exit 1; done && python3 lib/fanout.py --help >/dev/null && python3 lib/report.py --help >/dev/null && python3 scripts/check_records.py plans/runner-routing/baseline.tsv --min-rows 13 && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-23T23:34:28Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Check the runner features, the baseline and the drift since it

This plan needs the [runner-routing](../../runner-routing/plan.md) features. The gate checks them in this worktree, which comes from `main`. If it fails, `runner-routing` is not merged. Stop and record that as a blocker.

## Do

1. Compare each `commit` in `plans/runner-routing/baseline.tsv` with the current default-branch commit of that repository under `$REPOS_ROOT` (`git -C ... rev-parse <base>`). Read only.
2. For each repository that moved, list the commits (`git log --oneline <old>..<new>`) and say if they change layout, checks, CI or Docker gates.
3. Confirm that `gh` is signed in (`gh auth status`) and that Docker answers (`docker version`). Do not change anything.
4. Record the results below. Do not write local paths.

## Results

Date: 2026-11-23.

**Runner features.** `./ralph-looper --capabilities` lists all six: `step-agent`, `operator-step`, `script-step`, `local-agent`, `gate-from-plan-branch`, `touches-enforced`. `lib/fanout.py --help`, `lib/report.py --help` and `check_records.py` on the baseline (13 rows) all pass. `scripts/check_context.py` and `git diff --check` pass. `runner-routing` is merged.

**Drift since the baseline.** 12 of 13 repositories are at the baseline commit. They did not move: `repo-template`, the translation repository (`loop/es-v4`), `compliance_poc`, `duckdb-fs`, `ffmpeg_mcp`, `gpx_parser`, `lmdb-fs`, `metadata_driven_gx`, `metadata_mcp`, `pandoc_mcp`, `sample_parse` and `vips_mcp`.

Only `ralph-looper` moved: `c8b7b16` to `66e8308` (24 commits). All of them are the `runner-routing` work (steps 01 to 07, the merge of pull request 9 and one `PROMPT` change). They change CI and checks: the secret guard (`scripts/secret_guard.py`, hooks, a CI job), a `route` field in the usage ledger, and the secret guard before each merge. They add per-step executors, `lib/fanout.py` and `lib/report.py`. They do not change the layout of the repository, and they do not change the Docker gates. No other change was found.

**`gh` and Docker.** Not confirmed. The sandbox denied `gh auth status` and `docker version` in this run. See "Resume notes".

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

Done: items 1 and 2 of "Do", and the gate checks. Remaining: item 3. Run `gh auth status` and `docker version` (the operator, or an agent that may run them). Record the two results under "Results". Then set `status: done` and fill `evidence`. Do not mark the step done before then.
