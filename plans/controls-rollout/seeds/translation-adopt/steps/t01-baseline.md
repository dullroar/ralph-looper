---
id: t01-baseline
status: pending
depends_on: [t00-secret-guard]
touches:
  - plans/adopt-ralph/steps/t01-baseline.md
lane: none
tier: light
gate: grep -Eq '^verify-fast: exit [0-9]+' plans/adopt-ralph/steps/t01-baseline.md && grep -Eq '^verify-release-no-gates: exit [0-9]+' plans/adopt-ralph/steps/t01-baseline.md && grep -Eq '^tool-tests: [0-9]+ tests' plans/adopt-ralph/steps/t01-baseline.md && grep -Eq '^queue-counts: .+' plans/adopt-ralph/steps/t01-baseline.md && grep -Eq '^tracked-files: [0-9]+' plans/adopt-ralph/steps/t01-baseline.md && grep -Eq '^git-status: clean' plans/adopt-ralph/steps/t01-baseline.md && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Record the current verification results

Step `t08` must reproduce these numbers. Record them exactly.

## Change

Run each command. Write the result in the section "Baseline" below, one line each, at the start of the line, in the formats `verify-fast: exit N ...`, `verify-release-no-gates: exit N ...`, `tool-tests: N tests, <result>`, `queue-counts: <output>`, `tracked-files: N (<files that t00 added>)` and `git-status: clean`. The keys are:

- `verify-fast:` the exit code and the last summary line of `python3 -I tools/verify.py --fast`.
- `verify-release-no-gates:` the same for `python3 -I tools/verify.py --release --no-gates` (exit `3` means "passed but incomplete", which is the expected result without the gates).
- `tool-tests:` the test count and the result of `python3 -m unittest discover -s tools -p 'test_*.py'`.
- `queue-counts:` the output of `python3 tools/next_task.py --counts`.
- `tracked-files:` the output of `git ls-files | wc -l`, and the list of files that `t00` added (`git diff --name-status <first commit of this plan>^ HEAD --stat` is enough).
- `git-status:` a summary of `git status --short` (it must be clean).

If a command needs the English clone and it is missing, write that under "Resume notes" and stop.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- t00-secret-guard: the guard and the registration. The tracked file count already includes its files.

## Done when

- The gate passes. Every key has a value, not a placeholder.

## Baseline

(write the six lines here)

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
