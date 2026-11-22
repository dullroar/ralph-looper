---
gist: "Read me when: you want to bring the ten approved repositories onto repo-template and run their Docker-verified migrations with Ralph."
---

# Ralphify the approved repositories

## Approach

`repo-template` supplies the layout, agent entry points, index and context checks, and plan format. `ralph-looper` takes a committed plan from the repository passed to `--repo`. It creates a plan branch, runs each step in its own worktree, reruns its gate, and merges successful steps into that plan branch. Use that same driver for this parent plan and for each child plan. The parent plan prepares a launcher and verifies the results. The launcher provisions and runs child plans as separate host processes under operator control. No driver or prompt changes are needed.

Use the [allowlist](./targets.tsv), [child plan contract](./child-plan.md), and [repo-specific gates](./targets.md). Resolve the target base commits when provisioning. At planning time the ten tracked trees were clean and their existing context checks printed passing results. The template and runner revisions inspected were `126277f5b34027bc3766b4ae0804746f90dce959` and `0a1c8b6fdbe79e5e182206ce99e10bad007d1aba`. Use those revisions as the source baseline. Check for drift before starting the rollout and record any approved change to the baseline.

## Steps

| Step | Goal | Depends on |
| --- | --- | --- |
| [01-prepare-launcher](./steps/01-prepare-launcher.md) | Build and test the launcher and child plan seeding against disposable repos. | None |
| Operator launch | Seed and run the ten child plans with bounded concurrency. | 01 |
| [02-verify-rollout](./steps/02-verify-rollout.md) | Check all ten committed results and record the rollout status. | 01 and successful operator launch |

## Run it

Start from a commit containing this plan. Set `RALPH_REPO`, `REPOS_ROOT`, `TEMPLATE_REPO`, `ROLLOUT_STATE`, and `RALPH_WORK` to absolute paths. Keep state and worktrees outside Git checkouts. Reuse the same paths on restart. Use a Bash host with Git, Python 3, Docker, and the approved agent CLI. Use a runner path without whitespace because the Bash driver expands its picker command as a string. Before launching any child, confirm that Docker works for the selected agent and for the driver. Use a host with working container FUSE for the two mount gates. During planning the Docker daemon responded from the host and `/dev/fuse` was present. Confirm a container mount on the chosen host before claiming that the mount gates can run there.

```bash
export RALPH_WORK
runner="$RALPH_REPO/ralph-looper"
"$runner" --repo "$RALPH_REPO" --plan ralphify-repositories \
  --agent "$RALPH_PARENT_AGENT" --jobs 1 --max-iterations 1 --on-limit handoff
```

The first command can exit `10` after its iteration limit even if the preparation step passed. Check `01-prepare-launcher` on `plan/ralphify-repositories` before proceeding. A `done` result and the committed launcher are required. Use the `_plan` worktree created by that run to execute the launcher. The `run` command below is the interface that step 01 will build.

```bash
parent_worktree="$RALPH_WORK/ralph-looper/ralphify-repositories/worktrees/_plan"
export ROLLOUT_STATE
python3 "$parent_worktree/plans/ralphify-repositories/rollout.py" run \
  --repos-root "$REPOS_ROOT" --template-repo "$TEMPLATE_REPO" \
  --runner "$runner" --agent "$RALPH_CHILD_AGENT" --jobs 2
```

Use one step at a time within each child. The operator may raise `--jobs` after checking Docker capacity and agent quota. Provision each target on its own `rollout/ralphify` branch from the named base branch. Launch the child against that linked worktree, with `--plan ralphify --jobs 1 --on-limit handoff`. Reuse its worktrees and state on retry. Let unaffected children finish if one child stops. Recover the stopped child from its recorded branch, exit code, work area, and last failed gate before retrying the launcher. Run the parent again after the launcher exits zero.

```bash
"$runner" --repo "$RALPH_REPO" --plan ralphify-repositories \
  --agent "$RALPH_PARENT_AGENT" --jobs 1 --on-limit handoff
```

Rollout work ends with local plan branches and pinned evidence. Merge each target branch into its base through that repository's normal review process. A restart never resets or replaces a branch with unknown provenance. The only writes to `ralph-looper` are the parent plan and its support files.

## Parallelism

There are ten target lanes and no migration dependency edges between them. The [dependency review](./targets.md#dependency-review) covers the GX demo and fixture, filesystem lineage, and the two uses of the Pandoc binary. Each child has a unique Git common directory, runner work area, image tag, and temporary output paths. Docker capacity, FUSE availability, and agent quotas are shared host limits. If a fresh baseline reveals a new hard dependency, pin independent inputs or add an explicit dependency before launching the affected lanes.
