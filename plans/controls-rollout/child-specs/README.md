# Child plan contract

A seed step renders one child spec into `seeds/<wave>/` (or `seeds/<wave>/<repo>/` for a wave with more than one target). `lib/fanout.py` copies the seed into `plans/<child_plan>/` of the target and commits it. Follow these rules for every seed.

## Files

- `goal.md` with the Ralph loop prompt from the target's `plans/for-each-plan/goal.md` (or the template's, if the target has none yet). Name the child plan. Add the target's local rules.
- `plan.md` with a `gist: "Read me when: ..."` key, the approach, the step table with executors, the parallelism and the risks.
- `steps/<id>.md`, one for each step in the spec. Use the step template of the pinned `repo-template`. Set `status: pending`, empty `claimed_by`, `claimed_at` and `evidence`.

## Self-contained

- A child agent has no access to this parent plan. Copy every fact that it needs into the seed: pins, commands, repository brief, lessons that apply, and limits. Do not link to files in `ralph-looper`, except public GitHub URLs.
- Write the pinned library install line in full: `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@<commit>"`. Take `<commit>` from [pins.tsv](../pins.tsv).
- Do not write local paths, host names or user names.

## Keep seeds lean

The executor is a strong cloud agent. Write the goal, the limits, the facts it cannot find by itself, and a gate that proves the result. Do not write the implementation in prose: no function-by-function designs, no line-level instructions, no pre-written code. A step that would need that much detail is either small enough to do directly or must be split. Target: a step body of 10 to 30 lines.

## Steps

- `id` equals the file name stem. List exact `depends_on`, `touches` and `gate`. Include the step's own file in `touches`.
- Use `agent:` as the spec says. Do not use `agent: local` (owner decision 2026-11-23: the local model is too slow on this host; see `decisions.tsv`). A `script` step has a `run:` command and no model work.
- A gate proves the result. A gate that only checks that a file exists is not enough, except for an operator step that records an outside fact.
- Every step that adds or changes a check must show that a known-bad fixture fails for the expected reason and a known-good fixture passes.
- Steps that can run together must not touch the same files. Run `python3 scripts/check_plan.py` on a snapshot of the target with the seed in place. The seed step gate does this through `lib/fanout.py ready`.

## Limits for every child

- Keep existing entry points, tests, Docker gates, CI job names and documented commands.
- Never push, publish, change a remote or a GitHub setting. Never run `ralph-pusher`.
- Never put secrets in a CI job that runs pull-request code. Use `permissions: contents: read`. Pin actions to full commit SHAs.
- Keep runtime output outside the repository.
- **Secrets are never tracked, committed or pushed.** The first adoption commit in every child adds `scripts/secret_guard.py`, `scripts/install_hooks.sh` and a blocking CI job (`--tracked`, and `--range` on pull requests). The secret guard is required at once, not advisory. The child's last step runs `secret_guard.py --history` and records the count. Synthetic secrets in tests are built at run time. An exception needs a reason and a fingerprint, and the review step lists each new exception for the owner. After the operator merges a child, the operator runs `bash scripts/install_hooks.sh` in that clone.
