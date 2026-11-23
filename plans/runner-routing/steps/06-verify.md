---
id: 06-verify
status: done
depends_on: [05-docs]
touches:
  - plans/runner-routing/steps/06-verify.md
lane: none
tier: light
gate: bash tests/run.sh && bash tests/run-pwsh.sh && python3 tests/test_fanout.py && python3 tests/test_report.py && python3 tests/test_check_records.py && python3 tests/test_secret_guard.py && python3 scripts/secret_guard.py --history && bash scripts/install_hooks.sh --self-test && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-23T22:34:01Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Verify the upgraded runner from a clean clone

## Change

- This step file only.

## Do

1. Clone this worktree into a temporary directory outside all repositories (`git clone --no-local`). Run the gate there. Remove the clone.
2. Run `./ralph-looper --capabilities` and `python3 lib/fanout.py --help`. Check each item in [goal.md](../goal.md#done-when).
3. Run `python3 lib/report.py --work "$RALPH_WORK" --format md` for this plan. Copy the table (no paths) into "Results".
4. Record: test counts, the PowerShell result (ran or NOT RUN), the six capability words, and the UTC date.

## Results

Date (UTC): 2026-11-23. Gate parts ran in a clean clone (`git clone --no-local`) of this worktree at the 05-docs merge commit.

Test counts:

- `tests/run.sh`: PASS (all sections 1 to 12).
- `tests/test_fanout.py`: 9 tests, OK.
- `tests/test_report.py`: PASS.
- `tests/test_check_records.py`: 17 tests, OK.
- `tests/test_secret_guard.py`: 21 tests, OK.
- `scripts/secret_guard.py --history`: 0 findings, 1 allowed, 0 unscanned.
- `scripts/install_hooks.sh --self-test`: ok.
- `scripts/check_context.py`: all checks ok.
- `git diff --check`: clean.

PowerShell: NOT RUN. `pwsh` is not installed here. `tests/run-pwsh.sh` printed "PowerShell test NOT RUN" and exited 0. Parity of the PowerShell driver is not proven.

Capability words (`./ralph-looper --capabilities`): `step-agent`, `operator-step`, `script-step`, `local-agent`, `gate-from-plan-branch`, `touches-enforced`.

`python3 lib/fanout.py --help` lists `ready`, `provision`, `run`, `status`, `verify` and `published`.

Route report (`lib/report.py --format md`):

| route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude | claude-opus-5-5 | 4 | 4 | n/a | 1757 | 440.5 | 10087375 | 165728 | 8.7622 |
| claude | claude-sonnet-5-5 | 2 | 5 | n/a | 275 | 63 | 3638194 | 38257 | 1.7355 |
| codex | - | 3 | 3 | n/a | 0 | 0 | 0 | 0 | not reported |
| codex | gpt-6.1-terra | 2 | 2 | n/a | 138 | 69.0 | 783914 | 4575 | not reported |
| codex | gpt-6.2-sol | 52 | 65 | n/a | 18025 | 257 | 85772879 | 508987 | not reported |

Done-when items checked: test suites pass; secret guard and hooks work; capabilities print six words; fanout help lists six commands; report summarizes by agent, route and model. The `baseline.tsv` check is part of `scripts/check_context.py`/`check_records.py` tests; I did not run `check_records.py` on `baseline.tsv` separately.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
