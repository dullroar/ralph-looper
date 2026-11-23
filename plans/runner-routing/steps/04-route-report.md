---
id: 04-route-report
status: blocked
depends_on: [03-step-routing, 07-secret-guard]
touches:
  - lib/usage.py
  - lib/report.py
  - tests/test_report.py
  - ralph-looper
  - ralph-looper.ps1
  - tests/run.sh
  - plans/runner-routing/steps/04-route-report.md
lane: none
gate: python3 tests/test_report.py && bash tests/run.sh && python3 lib/report.py --help && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Record the route in the ledger and report cost and first-pass rate by route

Routing decisions need measurements. The README lists "a model/cost report from `ledger.jsonl`" as not built. Build it now, so that every later wave can compare executors.

## Change

- `lib/usage.py`: add the fields `route` (from `RALPH_STEP_AGENT`: `claude`, `codex`, `copilot`, `local`, `script` or `operator`), `attempt` and `gate` (`pass`, `fail` or `none`) to each ledger line. Old ledger lines without them stay valid.
- `ralph-looper`, `ralph-looper.ps1`: pass the attempt number and the gate result to `lib/usage.py` (call it after the gate, or write a second short ledger line for the gate result; choose one and test it). Keep both drivers equal.
- `lib/report.py`: standard-library Python. Read one or more ledgers (`--ledger FILE`, repeatable) or all ledgers under `--work DIR` (default `$RALPH_WORK`, else `~/repo-work`). Group by `route`, `model` and optionally `--by plan` or `--by repo`. Print: steps, attempts, first-attempt gate pass rate, total and median wall time, tokens in and out, reported USD (and "not reported" where the agent gives none). `--format md|tsv|json`. Never print prompts, paths or user names. Exit 2 on unreadable input.
- **Secret guard before merge** (`ralph-looper`, `ralph-looper.ps1`): before the driver commits and merges a step, run `secret_guard.py --range <start commit>..HEAD` and `--staged` in the step worktree. Use the target repository's `scripts/secret_guard.py` if it exists, else the runner's own copy (`$HERE/scripts/secret_guard.py`), so that a repository without the guard is still protected. A finding fails the attempt with `result: <step> secret guard FAILED` and nothing is merged. Export `SECRET_GUARD` with the runner copy for the hooks. Add a test to `tests/run.sh` (touch it only for this test): a fake agent writes a synthetic key built at run time; the step fails and the key is not on the plan branch.
- `tests/test_report.py`: fixtures with old and new ledger lines, mixed routes, missing costs and a malformed line (counted and reported, not fatal unless `--strict`).

## Do not change

- Files outside `touches`. The gate command.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
