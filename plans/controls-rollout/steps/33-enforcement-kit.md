---
id: 33-enforcement-kit
status: done
depends_on: [17-publish-pilot]
touches:
  - plans/controls-rollout/enforcement-kit.md
  - plans/controls-rollout/probes/**
  - plans/controls-rollout/steps/33-enforcement-kit.md
lane: none
gate: test -s plans/controls-rollout/enforcement-kit.md && bash plans/controls-rollout/probes/self_test.sh && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate (enforcement-kit.md non-empty, probes/self_test.sh, check_context.py, git diff --check) passed on 2026-11-23; self_test: 19 checks ok"
---

# Write the protection checklist and the bypass probes

Source phase 10. Write what the operator needs to make the checks required, and the probes that prove a producer cannot get around them.

## Change

- `enforcement-kit.md`:
  - A capability table for the 14 repositories (the ten, `repo-template`, `ralph-looper`, `deterministic-controls`, the translation repository): visibility, and what the owner's GitHub plan supports for that visibility (rulesets, required status checks, required reviews, code owner review, bypass list). Read it with `gh api` (read only). Branch protection on a private repository needs a paid plan. Say so where it applies.
  - The exact `gh api` commands to create a ruleset that requires the `context` check (and `runner-tests` for `ralph-looper`), blocks force pushes and deletion of the base branch, requires a pull request, and requires code owner review for `.github/workflows/**`, `controls.toml`, `scripts/controls-requirements.txt`, `scripts/check_context.py` and `tests/fixtures/**`.
  - A `CODEOWNERS` text for those paths. Say clearly that `CODEOWNERS` has an effect only with a rule that requires code owner review.
  - Break-glass: a named human, a written reason, one-time scope, an audit note and a follow-up issue. Coding agents never get bypass rights.
- `probes/`: `make_probe.sh <repo> <probe>` creates a probe branch in a temporary clone (never in the checkout under `$REPOS_ROOT`) and prints the push command for the operator. Probes: commit a synthetic key (built at run time) and check that the pre-commit hook, the pre-push hook and CI each block it; commit a `.env` file; add a blanket exception to `.secret-guard-allow`; remove the controls job, rename the check, add `continue-on-error: true`, add `if: false`, add a path filter, remove a check ID from `controls.toml`, swap the pin to another commit, delete a bad fixture, add a blanket ignore. `self_test.sh` creates each probe in a disposable local repository and checks that the expected file change exists. It needs no network.

## Results

- `enforcement-kit.md`: capability table for the 14 repositories, ruleset JSON and `gh api` commands, `CODEOWNERS` text, probe table, break-glass rule, recording rules.
- The agent could not run `gh` (permission denied in this session). The visibility and plan columns say "read it". The kit has the read-only commands. Step 34 (operator) fills them. Only the facts that the repository already records are filled in (the library is public, the translation repository is private).
- `probes/make_probe.sh`, `probes/apply_probe.py`, `probes/self_test.sh`: 12 probes. The self-test makes each probe in a disposable local repository, checks both hooks block the two secret probes, and needs no network.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
