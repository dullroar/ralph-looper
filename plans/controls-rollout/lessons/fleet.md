# Lessons from the `fleet` wave

Targets: `compliance_poc`, `ffmpeg_mcp`, `gpx_parser`, `lmdb-fs`, `metadata_mcp`, `pandoc_mcp`, `sample_parse` and `vips_mcp`. Child plan: `adopt-controls`. Review date: 2026-11-24 (UTC).

| Target | Final plan commit | Operator amendments |
| --- | --- | --- |
| `compliance_poc` | `c733c6a59f4a5993a17760a15c8746a83c15648b` | 3 (a02 may edit two estimator scripts and `scripts/build_indexes.py`) |
| `ffmpeg_mcp` | `2552b7c22e3eedbc08a7c60fa8c3ebdd7ab2b75a` | 2 (a02 may edit `.dockerignore`) |
| `gpx_parser` | `b65c1bb1180f35dfe1cd0606472fa04c236b04ea` | 2 (a02 may edit `.dockerignore`) |
| `lmdb-fs` | `0004e414f71017823879f70c5e73e2d46dbba641` | none |
| `metadata_mcp` | `8d9b048f4557af4988bc17b0124898798c69eb11` | 2 (a02 may edit `.dockerignore`) |
| `pandoc_mcp` | `1180a94dadf6efdd0d7660efaa532b8b92e75a66` | none |
| `sample_parse` | `ba322dd2c27b103094db13725e6cc110a0d047f6` | none |
| `vips_mcp` | `0993374021f7d57b586fbe1f76f9630c07dc56d7` | none |

`python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave fleet` printed `verified done` for all eight targets and `verify: 8/8 targets pass`.

I read the child branches `plan/adopt-controls` with Git plumbing only (`git show`, `git ls-tree`). I did not change any target repository. I did not run the Docker gates again. The child step a04 and the verify gate ran them.

What I checked: I read `docs/controls-adoption.md` of each target, with the pilot review checks:

- Probes (step a03). In all eight repositories, each probe failed with the expected rule ID: `markdown.local-links.missing-file`, `context.index-freshness.stale`, `plans.schema.missing-gate`, `security.secrets.*`, `repo.forbidden-artifacts.tracked`. The unreadable-file probe gave exit `3` (status `error`), never a pass. The restored or clean copy passed (exit `0`). The shim gave exit `1` and the line `FAIL check_plan.py` for a plan step without a gate.
- Rollback. Every record shows a clean clone of the base commit that passes the old `check_context.py`, and a clean clone of `HEAD` that passes the new shim. Every record gives Option A (change the pin) and Option B (revert).
- Receipt. Every receipt has the same pin (`3a2e9f3d95136958c54f73c831e84b971fc9a054`), the `ci` profile, seven checks passed and state `advisory`.
- Existing commands. Every receipt or record keeps the old scripts, the Docker gate and the old `check` job.
- Secret guard exceptions: `none` in all eight records.
- `compliance_poc` workflows. `claude.yml` and `claude-code-review.yml` did not change. The blob IDs on `plan/adopt-controls` are equal to the blob IDs on `master` (`6b15fac7af3da593de10cdc0e8203a0ae7d722bd` and `37e66f3fdb9bf08934a867db03d080da14f1c592`). The `controls` job in `context.yml` has `permissions: contents: read` and no `secrets.` reference. It has no `env` entry with a secret. The `claude.yml` workflow already used `secrets.CLAUDE_CODE_OAUTH_TOKEN` before the adoption, and it is unchanged.
- Defects in the repositories: none found that block the next step. One latent gap exists in `lmdb-fs` (see Change).
- Noisy checks: none. `security.personal-data` also fires on the synthetic token. This overlaps with `security.secrets`. It is not noise.

## Keep

- Keep the order of the child steps: secret guard (a00), audit (a01), apply (a02), probes (a03), verify (a04). All eight repositories finished with it.
- Keep the pin to `v0.1.2` (commit `3a2e9f3d95136958c54f73c831e84b971fc9a054`). No target had a `context.index-freshness` failure on folder `README.md` files.
- Keep the probe method of the pilot: a throwaway clone in an excluded `.probe/` folder, the rule ID read from the JSON, the token built at run time and committed only in the clone.
- Keep the rule that the shim exits `2` if the library cannot run.
- Keep the old `check` job, the Docker gate and the tests in the first adoption. Keep the `controls` job next to them. Accept the repeated secret guard steps.
- Keep the Dockerfile recipe: install `git` as root, build the shim cache at image build time as the run user, change nothing in the run command, `--network none` or `--read-only`. All eight repositories used it and passed the verify gate.
- Keep `docs/controls-adoption.md` with the sections "Where the tools did not fit", Probes, Rollback and Receipt.
- Keep `fanout.py amend` for scope changes. The audit log of each target shows every amendment. The three `.dockerignore` amendments and the three `compliance_poc` amendments are all there.

## Change

- Add `.dockerignore` to the `touches` of step a02 for every repository that has a `.dockerignore` with an allowlist (first rule `*`, then `!path` lines). `adopt apply` does not add `!controls.toml`. The image then has no manifest. Three repositories (`ffmpeg_mcp`, `gpx_parser`, `metadata_mcp`) failed the first a02 attempt with "manifest not found" and needed an operator amendment each. Write the instruction in the seed text: "Add `!controls.toml` to `.dockerignore` if it is an allowlist. Do not change the secret excludes."
- Fix `lmdb-fs` before the enforcement step. Its `.dockerignore` is an allowlist and has no `!controls.toml`. The wave passed, because the shim in the image runs the library with its default configuration for the `ci` profile. The image does not use `controls.toml`. The adoption record says so and asks the operator to add the line. The operator must add `!controls.toml` in the publish step or in a follow-up change. Then the Docker gate checks the real configuration.
- Tell the agent to find the repository files that the old index builder skips, before it runs `adopt apply`. In `compliance_poc`, the library requires a `Run me when:` line in two estimator scripts and the old `scripts/build_indexes.py` skipped them. This needed three amendments. Run `adopt audit` and read the index findings first. Put the files in `touches` of a02 from the start, or decide to report them and do not edit.
- Tell the agent to set `persist-credentials: false` on the checkout of the `controls` job, to match the `check` job. `sample_parse` did this by hand. `adopt apply` does not write it. The other targets keep the generated default. Decide once for all later seeds and write it in the seed text.
- Tell the agent that the receipt text can name a wrong base revision. The `rollback` text of the receipt names the commit of the clean clone, not the commit before the adoption. Use the Rollback section of the record and not the receipt text.
- Do not use `first_pass_rate` to judge a route. Count `attempts` against `steps` (see Route evidence).
- Keep every check advisory in `enforcement.tsv` until the enforcement step.
- Keep the rules of the `template` and `pilot` lessons that are not listed here. They still apply.

## Library defects

none new in this wave. The library had no failure of a check in these eight repositories.

Known usability points from the pilot are still open. They do not block the next seed. All eight records show them again:

- `adopt apply` rewrites `scripts/install_hooks.sh` (the `secretguard.path` fallback). Every child restored the file. Probe: run `adopt apply` on a repository that has the secret guard hooks, then `git status`.
- `adopt receipt` in a clean clone gives empty `files_added` and `files_changed` and the clone name as `repository`. Probe: run `adopt receipt --root <clean clone> --commit <pin>` and read the JSON.
- `adopt apply` does not know an allowlist `.dockerignore`. Probe: run `adopt apply` on a repository whose `.dockerignore` starts with `*`, build the image and run the shim. The manifest is missing. This is the new finding of this wave (3 repositories, plus the open gap in `lmdb-fs`). It is a gap of the tool fit and not a defect of a check, so it does not block the next seed. Report it to the library backlog.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, rows for this wave. Each fleet child has 5 steps: a00 to a04. The `claude` rows are the 4 agent steps (a01 to a04). The `script` row is the secret guard step (a00), which has no agent. The `codex` rows of these repositories come from earlier plans, not from this wave. I left them out.

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compliance_poc | claude | claude-sonnet-5-5 | 4 | 11 | 100% | 404 | 41 | 4507064 | 34807 | 1.7306 |
| compliance_poc | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| ffmpeg_mcp | claude | claude-sonnet-5-5 | 4 | 8 | 100% | 279 | 27.0 | 3092403 | 26198 | 1.2901 |
| ffmpeg_mcp | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| gpx_parser | claude | claude-sonnet-5-5 | 4 | 8 | 100% | 279 | 26.0 | 3005301 | 24478 | 1.1999 |
| gpx_parser | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| lmdb-fs | claude | claude-sonnet-5-5 | 4 | 4 | 100% | 243 | 51.0 | 2860492 | 22138 | 0.9853 |
| lmdb-fs | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| metadata_mcp | claude | claude-sonnet-5-5 | 4 | 8 | 100% | 265 | 29.0 | 2962736 | 26169 | 1.2447 |
| metadata_mcp | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| pandoc_mcp | claude | claude-sonnet-5-5 | 4 | 4 | 100% | 204 | 42.5 | 2771264 | 19816 | 0.9414 |
| pandoc_mcp | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| sample_parse | claude | claude-sonnet-5-5 | 4 | 4 | 100% | 232 | 44.0 | 2863385 | 21789 | 0.9783 |
| sample_parse | script | - | 1 | 1 | 100% | 0 | 0 | 0 | 0 | 0.0 |
| vips_mcp | claude | claude-sonnet-5-5 | 4 | 4 | 100% | 213 | 43.0 | 2478623 | 19883 | 0.9192 |
| vips_mcp | script | - | 1 | 1 | 100% | 1 | 1 | 0 | 0 | 0.0 |

Reading:

- The script executor passed on the first attempt in all eight repositories.
- The cloud agent (`claude-sonnet-5-5`) did the 4 agent steps in every repository. It passed on the first attempt (1 attempt for each step) in four repositories: `lmdb-fs`, `pandoc_mcp`, `sample_parse` and `vips_mcp`.
- It needed more than one attempt in the four others: `compliance_poc` (11 attempts for 4 steps), `ffmpeg_mcp`, `gpx_parser` and `metadata_mcp` (8 attempts for 4 steps each). These are the four repositories that had operator amendments. The extra attempts are the a02 attempts before the amendment and the attempts after it. The cause is the seed scope, not the executor.
- The report shows `100%` first pass for all rows. This does not agree with the attempt counts. The same disagreement was seen in the earlier waves. Do not use the column. Count `attempts` against `steps`.
- No step needed its fallback executor. The local and Codex routes were not used in this wave.
- The wave used 51 attempts for 32 agent steps (1.59 attempts for each step). The pilot had 2.25 and the `template` wave had 1.5. The wave cost 9.2895 USD for 2119 seconds of agent time.
- Apply the Change rules above. The `.dockerignore` rule alone would have removed 3 of the 4 repositories with amendments.
