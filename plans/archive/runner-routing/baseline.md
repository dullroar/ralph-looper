# Baseline of 13 repositories (2026-11-23 UTC)

This report gives the notes that [baseline.tsv](./baseline.tsv) cannot hold. Step 01-baseline-records recorded both files before the controls rollout changes anything.

## Method

- The `commit` column is the full SHA of the local default branch. The step did not fetch.
- The step ran each context check in a temporary `git worktree add --detach` of that commit, outside all repositories. It removed each temporary tree after the check.
- `seconds` is the wall time of `python3 scripts/check_context.py` in that tree. It is `0` when the check is absent.
- `ci_workflows` lists the files in `.github/workflows/` at that commit.
- The step did not run Docker tests. Each `not-run` with a Docker gate has the reason "Docker gate, recorded by the 2026-11-22 rollout". The archived [rollout record](../ralphify-repositories/steps/02-verify-rollout.md) has those results. All ten Docker gates passed on 2026-11-22.

## This repository

- `bash tests/run.sh` passed in 7.8 seconds. It ran the four scenarios: `kill -9` in a step, restart with another agent name, pusher backup, and remote cleanup.
- The context check passed. It also printed the step status of the `controls-rollout` and `runner-routing` plans.
- The local `main` is at the merge of pull request 8. The plan branch starts from the merge of pull request 7 and adds the run settings commit.

## Per repository

| Repository | Notes |
| --- | --- |
| `ralph-looper` | Has `lib/`, `tests/` and the two drivers in addition to the `repo-template` layout. |
| `repo-template` | Only the template layout. No tests. The `Dockerfile` is a work environment, not a test gate, so `test_command` is `none` and `test_result` is `not-run` (nothing to run). |
| `aprende-a-programar-como-un-bicho-raro` | See the next section. |
| `compliance_poc` | Two more workflows: `claude.yml` and `claude-code-review.yml`. Many files at the top level (prompts, samples, change-control notes). Live model tests are opt-in by environment variables and were skipped in the 2026-11-22 run (8 skips of 657). |
| `duckdb-fs` | Uses `uv` and `uv.lock`. The real FUSE mount test needs a FUSE-capable Docker run. The teardown fix after the rollout is in commit `e0286fcb63d5fee0a685b3334b85179e49fb1921`. |
| `ffmpeg_mcp` | Has a `plans/sharpen-mcp` plan with step 01 ready. |
| `gpx_parser` | Default branch is `master`. Thirty `.gpx` route files and `gpx_summary.csv` are at the top level, not in a data folder. |
| `lmdb-fs` | Uses `uv` and `uv.lock`. Has `tools/` and `data/` folders. The real FUSE mount test needs a FUSE-capable Docker run. The teardown fix after the rollout is in commit `d35caa20a7359ee92836968441efb4badc61756a`. |
| `metadata_driven_gx` | Many scripts and guides at the top level. The demo compares outputs with sample CSVs and ignores only `run_date`. |
| `metadata_mcp` | Has `sample-AGENTS.md` and `sample-CLAUDE.md` at the top level. Has a `plans/sharpen-mcp` plan with step 01 ready. |
| `pandoc_mcp` | Standard layout for an MCP server. |
| `sample_parse` | Default branch is `master`. Has `.pylintrc`, `.vscode/` and `LEARNTHIS.md`. |
| `vips_mcp` | Has a `plans/sharpen-mcp` plan with step 01 ready. |

All ten repositories of the 2026-11-22 rollout have `scripts/check_context.py`, a `Dockerfile` and `context.yml`. Their context checks passed with no warnings.

## Translation repository

- The repository does not use the `repo-template` layout. It has no `AGENTS.md`, no `scripts/check_context.py` and no `context.yml`. `context_check` is `absent`.
- The working branch `loop/es-v4` is the default branch. The local `main` branch has only the bootstrap commit and is not on `origin`. The record uses `loop/es-v4`.
- Its CI workflows are `pdf-release-gate.yml` and `sandbox-gate.yml`.
- `python3 -I tools/verify.py --fast` failed in 0.2 seconds. The `lock` check reported `I13 CHANGED` for three `gradlew.bat` files. A probable cause is line-ending conversion from `.gitattributes` in a new checkout. The step did not examine it more. The [controls rollout](../controls-rollout/plan.md) must examine it before it uses this check as a gate.
