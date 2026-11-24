# Lessons from the `pilot` wave

Targets: `metadata_driven_gx` and `duckdb-fs`. Child plan: `adopt-controls`. Review date: 2026-11-24 (UTC).

| Target | Final plan commit |
| --- | --- |
| `metadata_driven_gx` | `ff0ef1e7bfca4b61a92e9583f9329cf3d1ef7432` |
| `duckdb-fs` | `bd785ee38c767fab5bfb871a5ad28a45669df5cd` |

`python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave pilot` printed `verified done` for both targets and `verify: 2/2 targets pass`.

I read the child branches `plan/adopt-controls` with Git plumbing only. I did not change any target repository. I did not run the Docker gates again. The child step a04 and the verify gate ran them.

What I checked in `docs/controls-adoption.md` of each target:

- Probes (step a03). Every probe failed for the expected rule ID, in both repositories: `markdown.local-links`, `context.index-freshness`, `plans.schema`, `security.secrets`, `repo.forbidden-artifacts`. The unreadable-file probe gave exit `3` (status `error`), not a pass. The restored copy passed all seven checks (exit `0`). The shim gave exit `1` for a plan step with no gate.
- Rollback. Both records show a clean clone at the base commit that passes the old `check_context.py`, and a clean clone of `HEAD` that passes the new shim. Both describe Option A (change the pin) and Option B (revert).
- Receipt. Both receipts show the same pin (`3a2e9f3d95136958c54f73c831e84b971fc9a054`), the `ci` profile, seven checks passed and state `advisory`.
- Existing commands. The old `check` job, the Docker gate and the tests are kept in both. `duckdb-fs` also keeps the `docker` job.
- Equal findings. The probe tables and the receipts come from the same pin and the same commit in a clean clone. I did not run a separate CI run. I found no record of a difference between the CI-equivalent run and the local run.

Defects in the repositories: none found. The only findings were in the library (see Library defects) and in the tool fit (see Change).

Noisy checks: none. `security.personal-data` also fires on the synthetic token. This overlaps with `security.secrets`. It is not noise, because both rules flag a real problem.

## Keep

- Keep the order of the child steps: secret guard (a00), audit (a01), apply (a02), probes (a03), verify (a04).
- Keep the probe method. Make each probe in a throwaway Git clone of `HEAD`. Read the rule ID from the JSON output. Assert the rule ID and the exit code.
- Keep the seven-row probe table. Keep the unreadable-file probe: it must give exit `3` and never a pass.
- Keep the rule that the shim exits `2` if the library cannot run. Never pass without a result.
- Keep the old `check` job, the Docker gate and the tests in the first adoption. Add the `controls` job next to them.
- Keep the rollback test and the receipt in `docs/controls-adoption.md`, with a "Where the tools did not fit" section.
- Keep the operator amendments with `fanout.py amend`. All three pilot amendments are in the audit log of each target.

## Change

- Pin the seed to the newest release, `v0.1.2` or later. The earlier pin `v0.1.1` made `context.index-freshness` fail on folder `README.md` files. Do not add an exception or edit those files.
- Tell the agent to run all probes in an excluded `.probe/` copy inside the worktree. The agent session cannot run `mktemp`. The operator chose this in amendment 2.
- Tell the agent to record the history count in a04. The gate does the clean clone and the Docker run (amendment 3). Do not ask the agent to do the clean clone.
- Tell the agent that `security.secrets` reads committed content. In a probe, commit the synthetic token in the copy before the check. Build the token at run time. Never write it in a tracked file.
- For a repository with a Docker gate that has no network (`--network none`): make the Dockerfile build the shim cache at image build time, as the test user. Add `git` and `python3-venv` to the image. Make a local Git commit of the copied files before the dependency sync, so the secret scan does not read `.venv`. Put this in the seed text of every repository that has a Dockerfile.
- Tell the agent that a re-run of `adopt apply` can rewrite `scripts/install_hooks.sh`. That file is outside `touches`. Revert the change in the step. Let the operator take it later, or add the file to `touches` in the seed.
- Tell the agent that `adopt apply` adds a `controls` job that repeats the secret guard steps of the existing `check` job. Accept the repeat. Do not delete the old job in the first adoption.
- Keep the rules of the `template` lessons that are not listed here. They still apply (pass `--commit`, write `docs/controls-adoption.md` by hand, no virtual environment in the agent session, run the shim once before the wave).
- Do not use `first_pass_rate` to judge a route. Count `attempts` against `steps` (see Route evidence).
- Keep every check advisory in `enforcement.tsv` until the enforcement step.

## Library defects

Defect found by this wave and fixed: with `v0.1.1`, `context.index-freshness` failed on `memory/README.md` and `scripts/README.md`, because it wanted a `gist` or a `Run me when:` line in a folder `README.md`. Probe: run `python3 -m deterministic_controls check --root <copy> --profile ci` at `v0.1.1` on a repository that has these files. The fix is in `v0.1.2`, and both pilot targets pin it. This defect does not block the next seed.

Open defects: none. These are usability points, not failures, and they do not block the next seed:

- `adopt apply` rewrites `scripts/install_hooks.sh` on a re-run (the `secretguard.path` fallback). The step cannot keep it when the file is outside `touches`. Probe: run `adopt apply` twice with the same pin, then `git status`.
- `adopt receipt` run in a clean clone gives empty `files_added` and `files_changed` and the name of the clone as `repository`. Probe: run `adopt receipt --root <clean clone> --commit <pin>` and read the JSON.

The earlier defect from the `template` wave (the `Run me when:` line in `scripts/controls-requirements.txt`) did not appear in the pilot. Both pilot records say that `adopt apply` wrote the line.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, rows for this wave. Each pilot child has 5 steps: a00 to a04. The `claude` rows are the 4 agent steps. The `script` row is the secret guard step (a00), which has no agent. The `codex` rows of these two repositories come from earlier plans, not from this wave. I left them out.

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| duckdb-fs | claude | claude-sonnet-5-5 | 4 | 13 | 100% | 647 | 25 | 6451870 | 42970 | 2.3386 |
| duckdb-fs | script | - | 1 | 1 | 100% | 1 | 1 | 0 | 0 | 0.0 |
| metadata_driven_gx | claude | claude-sonnet-5-5 | 4 | 13 | 100% | 562 | 21 | 4620607 | 36940 | 1.9983 |
| metadata_driven_gx | script | - | 1 | 1 | 100% | 1 | 1 | 0 | 0 | 0.0 |

Reading:

- The script executor passed on the first attempt in both repositories.
- The cloud agent (`claude-sonnet-5-5`) did the 4 agent steps in both repositories. It used 13 attempts for 4 steps in each. So at least some steps needed more than one attempt.
- The report shows `100%` first pass. This does not agree with 13 attempts for 4 steps. The same disagreement was seen in the `controls` and `template` waves. The column does not count the first attempt. Do not use it. Fix the column rule, or count `attempts` against `steps`.
- No step needed its fallback executor. The local and Codex routes were not used in this wave.
- The wave cost 4.3369 USD for 1209 seconds of agent time.
- Attempts per step were higher than in the `template` wave (2.25 against 1.5). The three operator amendments of each target changed the seed text during the wave, so the seed was not right at the start. Apply the Change rules above so that the next seeds need fewer attempts.
