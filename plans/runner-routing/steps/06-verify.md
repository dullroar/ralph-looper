---
id: 06-verify
status: pending
depends_on: [05-docs]
touches:
  - plans/runner-routing/steps/06-verify.md
lane: none
tier: light
gate: bash tests/run.sh && bash tests/run-pwsh.sh && python3 tests/test_fanout.py && python3 tests/test_report.py && python3 tests/test_check_records.py && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
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

(fill in)

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
