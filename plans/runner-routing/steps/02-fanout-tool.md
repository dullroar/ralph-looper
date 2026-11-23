---
id: 02-fanout-tool
status: done
depends_on: []
touches:
  - lib/fanout.py
  - tests/test_fanout.py
  - docs/fanout.md
  - plans/runner-routing/steps/02-fanout-tool.md
lane: none
gate: python3 tests/test_fanout.py && python3 lib/fanout.py --help && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-23T22:13:31Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Combine the two plan-local launchers into one tested fan-out tool

A parent plan in this repository often runs child plans in other repositories. The [ralphify launcher](../../archive/ralphify-repositories/rollout.py) and the [MCP fan-out](../../archive/sharpen-mcp-suite/fanout.py) did this twice, with different code. Read both and their tests. Keep the safety properties of both. Build one general tool. The controls rollout uses it for every wave.

## Change

- `lib/fanout.py`: standard-library Python. The operator runs it. Agents do not run `run` or `provision`.
- `tests/test_fanout.py`: `unittest` tests with disposable Git repositories in a temporary directory and `tests/fake-agent.sh` through `AGENT_CMD`.
- `docs/fanout.md`: the human guide, with the wave format, the commands and the recovery procedure.

## Wave manifest

A parent plan holds `waves/<wave>.tsv` (UTF-8, header row, `#` comments). Columns:

| Column | Meaning |
| --- | --- |
| `repo` | Repository directory name. It must be a direct child of `$REPOS_ROOT`. |
| `base` | Base branch in that repository. |
| `child_plan` | Plan name in the target. |
| `mode` | `seed`: copy `source` into `plans/<child_plan>/` and commit it. `pinned`: the plan is already committed at commit `source`. |
| `source` | For `seed`, a directory relative to the parent plan directory. For `pinned`, a full commit SHA. |
| `run` | `yes`: run the driver. `no`: provision only (the operator runs the plan later). |

## Commands

All commands take `--plan-dir DIR` (the parent plan directory) and `--wave NAME`. State is in `$RALPH_WORK/fanout/<parent-plan>/<wave>/`. Use atomic writes and one lock for each wave.

- `ready`: read only. Check that each target is a clean canonical checkout under `$REPOS_ROOT` with a unique Git common directory, that the base branch exists, that the seed passes the target's plan checker (copy it into a temporary snapshot of the base and run `scripts/check_plan.py` there if present), and that the driver can list the child steps. Print one line for each target. Exit nonzero if one fails.
- `provision`: create the branch `rollout/<child_plan>` from `base` in a linked worktree under the state directory. Name the worktree directory after the repository. Copy the seed and commit only the seed files. Record target identity, base SHA, seed digest, seed commit and worktree. Refuse a dirty base, an unknown existing branch, a different seed digest for an existing branch, or a path that is not the canonical checkout. Never change the base branch or the current branch of the checkout.
- `run`: `provision` if needed, then run the driver for each target with `run=yes` in a bounded process pool (`--jobs N`). Pass `--agent` explicitly. Pass `--on-limit handoff`. Use the driver next to this file unless `--runner PATH` is given. Record exit code, final plan SHA, gate log digest and elapsed time. A stopped or blocked target does not stop the others. On restart, reuse recorded worktrees after an identity check, and do not relaunch a target whose driver lock is still held.
- `status`: read only. Print the recorded state for each target.
- `verify`: read only. Use Git plumbing (`git rev-parse`, `git cat-file`) on `refs/heads/plan/<child_plan>`. Do not call the driver's `--status`; it can create branches. For `run=yes` targets: the recorded plan SHA matches the ref, descends from the seed commit, and every step is `done` with driver evidence and the original gate text from the seed. For `run=no` targets: the seed commit exists on `rollout/<child_plan>`. Print an aggregate result. Exit nonzero if one target fails.
- `published`: read only, after `git fetch` of each target remote (fetch only). Check that the recorded final commit (or the seed commit for `run=no`) is an ancestor of `origin/<base>`. Exit nonzero if one is not.

Never push, never force, never change a remote or a GitHub setting. Never pass credentials or parent overrides (budgets, models) to children unless the operator gives them explicitly with `--child-env KEY`. Do not log prompts, tokens or local paths into tracked files.

## Tests must show

- Two disposable targets run to `done` with the fake agent. One stops on a simulated usage limit and resumes. The other keeps its result.
- A failed gate leaves its target incomplete and `verify` fails.
- `ready` and `provision` reject: an unknown repository, a dirty base, an advanced base after provisioning, a changed seed, a path substitution and a foreign existing branch.
- `verify` rejects a changed plan ref and a child step whose gate text differs from the seed.
- `published` passes after a fast-forward of the base in a bare "remote" and fails before.
- `pinned` mode works with a committed child plan.

## Do not change

- Files outside `touches`. The driver. The archived launchers.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)

Note for step 05: `docs/fanout.md` is new. Add it to the table in `docs/README.md` (step 05 owns that file).
