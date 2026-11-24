---
id: t08-verify
status: pending
depends_on: [t05-routing-map, t06-batch-tool, t07-archive-loop]
touches:
  - plans/adopt-ralph/steps/t08-verify.md
lane: none
tier: light
gate: python3 -m unittest discover -s tools -p 'test_*.py' && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 tools/check_routing_map.py && python3 scripts/secret_guard.py --tracked && python3 -I tools/verify.py --fast && grep -Eq '^verify-fast-same: (yes|no)' plans/adopt-ralph/steps/t08-verify.md && grep -Eq '^tool-tests-same: (yes|no)' plans/adopt-ralph/steps/t08-verify.md && grep -Eq '^queue-counts-same: (yes|no)' plans/adopt-ralph/steps/t08-verify.md && grep -Eq '^secret-history-count: [0-9]+' plans/adopt-ralph/steps/t08-verify.md && grep -Eq '^runner-status: ok' plans/adopt-ralph/steps/t08-verify.md && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prove that the new layout and the old results agree

## Change

- Run the commands of the baseline again (see "Baseline" in the step file `t01-baseline.md`): `verify.py --fast`, `verify.py --release --no-gates`, the tool tests, `next_task.py --counts`, the tracked file count and `git status`. Compare each result with the baseline.
- Write the comparison in "Comparison" below, one line each, at the start of the line: `verify-fast-same: yes|no`, `tool-tests-same: yes|no` (the count may be higher only by the tests that this plan added: list them), `queue-counts-same: yes|no`, and `file-count-delta: N (<list of added paths>)`. A `no` needs a reason on the same line. A `no` without a reason that is one of this plan's added files means failure: write "Resume notes".
- Runner view. Make a scratch clone of this branch outside the repository (use `RALPH_WORK`, not `/tmp`). Run the runner's status view there: `ralph-looper --repo <scratch clone> --plan adopt-ralph --status` (the runner is in the `ralph-looper` checkout under `REPOS_ROOT`; read its `--help` first). Write `runner-status: ok` if it prints the step table without an error, and the first line of its output.
- Run `python3 scripts/secret_guard.py --history`. Write `secret-history-count: N`. Any count above 0 is blocking: set the status `blocked` and say so.
- List each exception in `.secret-guard-allow` that this plan added (it must be none), under "Exceptions".

## Do not change

- Files outside `touches`. The `gate` command. Do not push. Do not delete the scratch clone's source branch.

## Already done by earlier steps

- t01-baseline: the numbers. t00 to t07: all the work.

## Done when

- The gate passes. The comparison is complete.

## Comparison

(write the lines here)

## Exceptions

(none)

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
