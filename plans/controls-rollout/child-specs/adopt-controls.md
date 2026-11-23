# Child spec: `adopt-controls` in the pilot and fleet repositories

Waves `pilot` (2 repositories) and `fleet` (8 repositories). Source phases: 8 and 9. All ten repositories came from `repo-template` on 2026-11-22. They have `scripts/check_context.py`, `.github/workflows/context.yml`, a Dockerfile and `scripts/test_docker.sh`. Write one seed for each repository: `seeds/<wave>/<repo>/`.

For each repository, copy its brief from the archived [repository-specific Docker gates](../../archive/ralphify-repositories/targets.md) into the seed's `plan.md`, under "Repository brief". Copy the Docker gate exactly. For the fleet, also copy every rule from `lessons/pilot.md` that applies.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| a01-audit | script | Read-only audit with the pinned library. | none |
| a02-apply | local, fallback cloud (pilot: cloud agent) | Apply the adoption in advisory mode. Keep all existing gates. | a01 |
| a03-probes | cloud agent | Known-bad probes, rollback test and receipt. | a02 |
| a04-verify | cloud agent, light | Full gates from a clean clone, including Docker. | a03 |

The pilot uses a cloud agent for a02 so that defects come from the library, not from the executor. The fleet uses `local` for a02 if `lessons/pilot.md` and the route report do not advise against it.

## Step details

- **a01.** `agent: script`. `run:` creates a temporary virtual environment outside the repository, installs the pinned library, and writes `python3 -m deterministic_controls adopt audit --root . --format json` to `docs/controls-audit.json`. Touches `docs/controls-audit.json`. Gate: the JSON parses, has `schema_version`, and the classification is not `blocked`. A `blocked` result stops the child for review.
- **a02.** Touches `scripts/check_context.py`, `scripts/controls-requirements.txt`, `controls.toml`, `.github/workflows/context.yml`, `scripts/AGENTS.md`, `AGENTS.md`, `docs/controls-adoption.md`. Run `adopt plan`, review the diff, then `adopt apply`. Keep the existing `context` job and any Docker job. The controls job is advisory: it is not required in branch protection yet, but it fails honestly (no `continue-on-error`). Add the controls rules to `AGENTS.md` (same text as the template). Do not change product code, tests or the Docker gate. Gate: `python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && git diff --check`.
- **a03.** Touches `docs/controls-adoption.md` and its step file. In a temporary copy of the worktree, create each probe and check that the check fails with the expected rule ID: a broken relative link, a stale index, a step without `gate`, a synthetic token in a Markdown file, a tracked `driver.out`, and an internal error (an unreadable file or a forced exception). Then restore the copy and check that it passes. Test the rollback: the previous library pin (or the pre-adoption scripts from the base commit) gives the same pass result on the clean tree. Write the receipt with `adopt receipt` into `docs/controls-adoption.md` as a JSON block.
- **a04.** Touches its step file only. Clone the worktree into a temporary directory. Run `python3 scripts/check_context.py` and the repository's Docker gate (`bash scripts/test_docker.sh`). For the FUSE repositories, the real mount test must pass with zero skips. Record commands, test counts and the UTC date.

## Special cases

- `compliance_poc`: do not change `claude.yml` or `claude-code-review.yml`. They use secrets. The controls job must have no secrets and must not depend on them. Base branch `master`.
- `duckdb-fs` and `lmdb-fs`: the Docker gate needs FUSE. Keep the device-free test run separate from the mount run.
- `gpx_parser`, `sample_parse`: base branch `master`.
- `metadata_driven_gx`: the `demo_weather` output is a contract for `duckdb-fs`. Do not change it.
