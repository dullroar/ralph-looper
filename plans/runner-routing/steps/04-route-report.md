---
id: 04-route-report
status: pending
depends_on: [03-step-routing]
touches:
  - lib/usage.py
  - lib/report.py
  - tests/test_report.py
  - ralph-looper
  - ralph-looper.ps1
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
- `tests/test_report.py`: fixtures with old and new ledger lines, mixed routes, missing costs and a malformed line (counted and reported, not fatal unless `--strict`).

## Do not change

- Files outside `touches`. The gate command.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
