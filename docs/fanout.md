# Fan-out tool: run child plans in other repositories

`lib/fanout.py` sends one wave of child plans from a parent plan to other repositories. It replaces the two plan-local launchers in `plans/archive/ralphify-repositories/` and `plans/archive/sharpen-mcp-suite/`. It uses the Python standard library only.

The operator runs this tool. Agents do not run `provision` or `run`.

## What the tool does not do

- It does not push, force or change a remote. It does not change a GitHub setting.
- It does not change the base branch or the current branch of a checkout.
- It does not pass credentials or parent settings (budgets, models) to the children. Only the variables that you name with `--child-env KEY` go to the children.
- It does not write prompts, tokens or local paths into tracked files.

## Setup

Export two variables. Both must be absolute paths without links.

| Variable | Meaning |
| --- | --- |
| `REPOS_ROOT` | The parent directory of the canonical checkouts. Each target is a direct child of this directory. |
| `RALPH_WORK` | The runtime root. It must be outside all Git checkouts and must not overlap `REPOS_ROOT`. |

The tool keeps its state in `$RALPH_WORK/fanout/<parent-plan>/<wave>/`:

| Path | Content |
| --- | --- |
| `targets/<repo>.json` | The record of one target: identity, base SHA, seed digest, seed commit, worktree, run result. |
| `worktrees/<repo>/` | The linked worktree on `rollout/<child_plan>`. The directory has the repository name, so the driver uses `$RALPH_WORK/<repo>/<child_plan>/`. |
| `logs/<repo>.out` | The driver output for that target. |
| `wave.lock` | One lock for each wave. `provision` and `run` hold it. |

The tool writes each record atomically. You can stop it at any time and start it again.

## Wave manifest

A parent plan has one file for each wave: `plans/<parent-plan>/waves/<wave>.tsv`. The file is UTF-8 text with tab-separated columns. The first row that is not a comment is the header. Lines that start with `#` are comments.

| Column | Meaning |
| --- | --- |
| `repo` | The repository directory name. It must be a direct child of `$REPOS_ROOT`. |
| `base` | The base branch in that repository. |
| `child_plan` | The plan name in the target. |
| `mode` | `seed`: copy `source` into `plans/<child_plan>/` and commit it. `pinned`: the plan is already committed at commit `source`. |
| `source` | For `seed`, a directory relative to the parent plan directory. For `pinned`, a full commit SHA. |
| `run` | `yes`: run the driver. `no`: provision only. The operator runs the plan later. |

Example:

```text
# Wave 1 of the controls rollout.
repo	base	child_plan	mode	source	run
example-api	main	controls	seed	seeds/controls	yes
example-cli	master	controls	pinned	0123456789abcdef0123456789abcdef01234567	no
```

A repository can occur only once in a wave.

## Commands

Each command takes `--plan-dir DIR` (the parent plan directory) and `--wave NAME`.

```bash
python3 lib/fanout.py ready     --plan-dir plans/<parent-plan> --wave <wave>
python3 lib/fanout.py provision --plan-dir plans/<parent-plan> --wave <wave>
python3 lib/fanout.py run       --plan-dir plans/<parent-plan> --wave <wave> \
  --agent claude --jobs 3 [--runner PATH] [--child-env KEY ...]
python3 lib/fanout.py status    --plan-dir plans/<parent-plan> --wave <wave>
python3 lib/fanout.py verify    --plan-dir plans/<parent-plan> --wave <wave>
python3 lib/fanout.py published --plan-dir plans/<parent-plan> --wave <wave>
```

### ready

Read only. For each target, the tool checks that:

- the target is a clean canonical checkout under `$REPOS_ROOT`. The checkout owns its Git directory, and no other target has the same Git directory.
- the base branch exists.
- no branch or worktree for the child plan exists without a record.
- a recorded target has the same base SHA and the same seed digest.
- the seed passes the target's `scripts/check_plan.py`, if the target has one. The tool copies the base and the seed into a temporary directory and runs the checker there.
- the driver can list a ready child step.

The tool prints one line for each target. It exits nonzero if one target fails.

### provision

The tool creates the branch `rollout/<child_plan>` from `base` in a linked worktree. For `seed`, it copies the seed and commits only the seed files. For `pinned`, the branch starts at the pinned commit. The tool records the identity, the base SHA, the seed digest, the seed commit and the worktree.

The tool refuses:

- an unknown repository or a path that is not the canonical checkout (for example, a link).
- a dirty checkout.
- an existing branch or worktree without a record.
- a base that advanced after provisioning.
- a seed that changed after provisioning.

`provision` is safe to run again. It continues a provisioning that stopped.

### run

The tool provisions each target if necessary. Then it runs the driver for each `run=yes` target in a pool of `--jobs` processes. It passes `--agent` and `--on-limit handoff` to the driver. It uses the driver next to `lib/` unless you give `--runner PATH`.

The tool records the exit code, the final plan SHA, a digest of the gate logs and the elapsed time. A stopped or blocked target does not stop the others. A target that is done is verified again and is not run again. The tool does not start a target whose driver lock is still held.

Record status values:

| Status | Meaning |
| --- | --- |
| `provisioned` | The seed is committed. The driver did not run yet. |
| `running` | The driver started. If no driver holds the lock, the next `run` starts it again. |
| `done` | The driver exited 0 and the result passed the checks of `verify`. |
| `limit` | The agent hit a usage limit (driver exit 75). Run again, with the same or another agent. |
| `blocked` | A step is blocked (driver exit 11). Read the gate logs. |
| `locked` | Another driver held the lock for this child plan (driver exit 3). |
| `stopped` | Any other exit, or a result that failed the checks. |

### status

Read only. The tool prints the recorded state of each target.

### verify

Read only. The tool uses Git plumbing only (`git rev-parse`, `git cat-file`, `git ls-tree`, `git merge-base`). It does not call the driver's `--status`, because that can create branches.

- For `run=yes`: the recorded plan SHA is equal to `refs/heads/plan/<child_plan>`. The plan descends from the seed commit. The plan has the same step files as the seed. Each step is `done`, has driver evidence and has the original gate text from the seed. The gate logs did not change.
- For `run=no`: the seed commit is on `rollout/<child_plan>`.

The tool prints a total line. It exits nonzero if one target fails.

### published

The tool runs `git fetch origin` in each target. This is the only change: it updates remote-tracking refs. Then the tool checks that the final commit (the seed commit for `run=no`) is an ancestor of `origin/<base>`. It exits nonzero if one is not.

## Normal procedure

1. Write the seeds and `waves/<wave>.tsv` in the parent plan. Commit them.
2. Run `ready`. Fix each failure.
3. Run `run`. Use `--child-env` only for variables that the children need.
4. Run `verify`.
5. Review and merge each `plan/<child_plan>` branch into its base through a pull request.
6. Run `published`.

## Recovery

| Situation | Action |
| --- | --- |
| The tool or the computer stopped. | Run the same `run` command again. Recorded worktrees are reused after an identity check. Done targets are not run again. |
| `limit` | Run `run` again later, or with another `--agent`. |
| `blocked` or `stopped` | Read `logs/<repo>.out` and the driver gate logs in `$RALPH_WORK/<repo>/<child_plan>/logs/`. Fix the cause in the child plan. Then run `run` again. |
| "driver lock is held" | A driver still runs for that target. Wait for it, or stop it. Then run `run` again. |
| "base branch advanced after provisioning" | The base changed before the child finished. Remove the worktree and the `rollout/<child_plan>` branch, delete `targets/<repo>.json`, then provision again. |
| "seed differs from the provisioned seed" | Restore the seed, or start again as above. |
| "no recorded provenance" | A branch, worktree or runtime directory exists that the tool did not create. Find out where it came from. Do not delete it before you know. |
| `verify` fails for a done target | The plan branch, a gate or a gate log changed after the run. Find out why before you merge. |
