---
id: 01-prepare-launcher
status: pending
depends_on: []
touches:
  - plans/ralphify-repositories/rollout.py
  - plans/ralphify-repositories/test_rollout.py
  - plans/ralphify-repositories/seeds/**
  - plans/ralphify-repositories/steps/01-prepare-launcher.md
lane: none
gate: python3 plans/ralphify-repositories/test_rollout.py && python3 scripts/check_context.py && git diff --check
evidence: ""
---

# Prepare the child plan launcher

Implement the plan-local operator launcher described in [plan.md](../plan.md). Use standard-library Python and the existing driver. Keep the run path outside the agent step. This step's tests create temporary repos and use a fake agent.

## Provision and run

- Read the fixed [allowlist](../targets.tsv). Require all names to match canonical direct child checkouts of the operator-supplied repos root. Check the Git top level and common Git directory before creating any branches. Reject path substitutions, duplicate Git identities, and unfamiliar existing branches or worktrees. Access the template checkout as an input. Materialize the pinned files or record their immutable snapshot and validate runner files against the pinned reference or an approved successor.
- Render and validate the three child steps using [child-plan.md](../child-plan.md) and [targets.md](../targets.md). Commit the plan on `rollout/ralphify` in a linked worktree. Name each seed worktree directory after the target repo because the driver derives the runtime namespace from that basename. Keep base and current user branches in place. Give the agent access to the worktree and the required gate entry point. Limit each agent to its own step worktree and avoid passing sibling mounts or deployment credentials.
- Require exported `ROLLOUT_STATE` and `RALPH_WORK` outside the repositories. Keep one launcher lock per rollout and persist the target identity, base SHA, seed SHA, worktree, elapsed run status, exit code, final plan SHA, and evidence location with atomic writes. Check the worktree and branch identity on resume. Rerun unfinished work through the existing driver. Confirm a completed result before reusing it. When an interrupted child might still be running, check its state before relaunching. Leave base refs alone and never push.
- The operator-facing `run` uses a bounded process pool. Supply the child agent explicitly. Keep parent-specific agent overrides, budgets and timeouts out of the child environment unless the operator explicitly sets them for the children. Enable `--on-limit handoff`. Exit nonzero if any child fails or remains blocked. Preserve results for successful children and surface each blocked gate and work directory. Avoid passing user data in logs. The fixture tests must cover an unknown target, a dirty or changed baseline, reuse after interruption, and preservation of a successful lane when another stops.

## Verify without writing to targets

- Implement `verify`, using the recorded local state and the allowlist. Read `refs/heads/plan/ralphify` in each target with Git plumbing. Do not call the driver's `--status` here. It can create a branch or worktree. Require the recorded plan SHA to match, descend from the seed, and have precisely the expected completed steps with driver evidence. Check for the required template files, both `AGENTS.md` links, the Docker test script, and committed verification notes. Associate the final Docker gate result and image/test evidence with that child plan SHA. Reject incomplete, stale, or foreign results. Print an aggregate result with repo names and commit IDs.
- Prove two disposable repos can be seeded and run by the actual driver with a fake agent. Check that the allowed child plans finish, an interrupted rerun resumes, a failed gate remains incomplete, an unrelated repo stays untouched, and parent verification rejects absent or mismatched results. Record the smoke test outcome in this step.
