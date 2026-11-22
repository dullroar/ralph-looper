---
id: 02-verify-rollout
status: pending
depends_on: [01-prepare-launcher]
touches:
  - plans/ralphify-repositories/steps/02-verify-rollout.md
lane: none
gate: python3 plans/ralphify-repositories/rollout.py verify && python3 scripts/check_context.py && git diff --check
evidence: ""
---

# Verify all ten target plan branches

Run this parent step after the operator launch has succeeded. Use the same exported `ROLLOUT_STATE` as the launcher. Run the read-only verifier from your step worktree. Review the result for each entry in the [allowlist](../targets.tsv). Check the Docker gate evidence against the matching [repo brief](../targets.md), including both real FUSE mounts and the offline compliance suite. Record each repo, final plan commit, Docker test result, and UTC date below. Keep raw logs and local paths in the external run state.

If a target is incomplete or its branch changed, record the exact missing or mismatched result. The parent gate must fail until the target is verified. The operator resumes that child plan using its existing state. Preserve completed results and leave branch integration to the repository owner.

## Results

Pending rollout.
