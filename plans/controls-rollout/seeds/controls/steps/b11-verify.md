---
id: b11-verify
status: pending
depends_on: [b10-release-prep]
touches:
  - plans/bootstrap/steps/b11-verify.md
lane: none
tier: light
gate: rm -rf "${TMPDIR:-/tmp}/controls-b11" && git clone -q . "${TMPDIR:-/tmp}/controls-b11" && cd "${TMPDIR:-/tmp}/controls-b11" && bash scripts/release_check.sh && python3 scripts/secret_guard.py --tracked
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Verify everything from a clean clone

Read `plans/bootstrap/plan.md` first. This step changes only its own file.

## Do

1. Clone this worktree into a temporary directory outside the repository. Run `bash scripts/release_check.sh` there. The gate does the same.
2. Record under "Results" below: the unit test count and result, the summary of `docs/fault-matrix.md`, the measured times for 100, 1,000 and 10,000 files, the SHA-256 of the wheel, and the result of `secret_guard.py --tracked`.
3. Run `python3 scripts/secret_guard.py --history` in this repository. Record the finding count. If it is not zero, list the finding rule IDs and paths (never the secret). Do not add an exception.
4. List each exception in `.secret-guard-allow` and each inline `secret-guard: allow`. The owner reviews them.
5. Do not write local paths in this file.

## Results

(none)

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b00 to b10.

## Done when

- The gate passes. "Results" holds the numbers above.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
