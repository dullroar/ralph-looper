---
id: 36-final-audit
status: done
depends_on: [34-apply-enforcement, 35-route-report]
touches:
  - plans/controls-rollout/final-audit.md
  - plans/controls-rollout/steps/36-final-audit.md
lane: none
gate: for w in controls template pilot fleet translation-adopt translation-pack translation-work; do python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave $w || exit 1; done && python3 scripts/check_records.py plans/controls-rollout/enforcement.tsv --min-rows 14 && test -s plans/controls-rollout/final-audit.md && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-24T16:08:30Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Audit the program and write the backlog

Source phase 17. Confirm that the program is one coherent system, and say plainly what it does not prove.

## Change

- `final-audit.md`:
  - The adoption matrix: each repository, its pin, its profile, its receipt location, its enforcement state, and its rollback command.
  - The baseline comparison: run each repository's context check now and compare with `plans/runner-routing/baseline.tsv`.
  - The route summary from `route-report.md`: cost, first-pass rate and fallback rate by executor. Say which routing rules the evidence supports and which it does not.
  - The limits: determinism does not prove meaning; fixture coverage is partial; the secret scan is best-effort; the enforcement gaps from `enforcement.tsv`; PowerShell coverage as the tests ran it.
  - The backlog with the evidence for each item: language and toolchain packs (phase 12), the AI-generated control lifecycle (phase 13), fleet operations and upgrade waves (phase 16), the optional `gpx_mcp` adoption, and any open library defects.
  - The archive step: after the merge, move this plan and `runner-routing` to `plans/archive/` in a separate pull request.

## Results

(fill in)

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

Resolved: the operator recorded the lmdb-fs follow-up; the gate passes and the step is done. Earlier notes follow.

Partial (earlier). `plans/controls-rollout/final-audit.md` is written (adoption matrix, baseline comparison, route summary, limits, backlog, archive step). The gate does not pass yet.

- Blocker: `python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave fleet` exits 1. `lmdb-fs: plan/adopt-controls differs from the recorded plan SHA` (7 of 8 pass). The other six waves verify. The check, the record check, `check_context.py` and the file test pass.
- Why I stopped: the fix is in the `lmdb-fs` repository or in the operator's wave record. Both are outside `touches`, and the agent session cannot read other repositories. The operator must find the new commits on `plan/adopt-controls` in `lmdb-fs` (probably the `!controls.toml` fix from the fleet lessons) and record them with `fanout.py amend`, or re-record the SHA. Then run the gate again. Backlog item B13.
- Not done: a live re-run of the context check in the other repositories (commands outside this worktree were denied). Section 3 of the audit uses the review records and says so.
- Also in the audit: step 09 is `done` but ralph-looper has no `controls.toml` or `docs/controls-adoption.md` (B1).
- When the gate passes: set `status: done`, fill `evidence`, and update section 3 of `final-audit.md` and B13 in the same commit.
