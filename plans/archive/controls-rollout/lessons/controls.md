# Lessons from the `controls` wave

Target: `deterministic-controls`, child plan `bootstrap`. Final plan commit: `7b5caeaff8567681d731f445eb43997bd429cc3f`. Review date: 2026-11-24 (UTC).

I checked the library against [the spec](../child-specs/controls.md). I ran `bash scripts/release_check.sh` in a temporary clone of `plan/bootstrap`. It passed: 196 unit tests, self check with profile `full` (7 checks passed), and a wheel build. The wheel is `deterministic_controls-0.1.0-py3-none-any.whl`. Its SHA-256 in this run is `697bd8c6057c25e5fa02c607beb0419df3642be2d9c121965410bc0b5c338929`.

## Keep

- Give each check its own catalog file, its own module, its own test file and its own fixture directory. Steps b04 to b07 ran in parallel with no merge conflict.
- Keep the fail-closed rules: exit `2` for a bad manifest, root or invocation, exit `3` for an internal error, and `security.secrets` as a mandatory check that cannot be disabled. `docs/fault-matrix.md` names a test for each fault.
- Keep the compatibility tests that run the old template script and the new check on the same fixtures.
- Keep the adoption tools small: `audit`, `plan`, `apply`, `receipt`. `apply` refuses a dirty tree, a detached HEAD and a bad commit, and it changes nothing then.
- Keep the shim contract: old output lines, exit `0` or `1` as before, exit `2` if the library cannot run, and never a pass without a result.
- Keep the secret guard in the first commit (b00) of the child. It ran on every step.
- Keep the fixture suffix `.fixture` for plan fixtures. It hides them from the repository checks.

## Change

- List in `touches` every test file that an earlier step left as a placeholder, and every file that a changed behavior can break. The operator widened `touches` for b02 (`tests/test_contract.py`) and for b08 and b10 (the b01 placeholder tests). Each case blocked the step for three attempts. Check the whole test suite for tests that the step makes obsolete.
- Tell the child agent in the step text to run the full unit test suite, not only its own test file, before it commits.
- Do not use `agent: local` for any step. The three local steps made no edit in 70+ minutes each (see Route evidence).
- Do not compare wheel digests between two builds. A rebuild of the same commit gave a different digest: the `release_check.sh` run in this review gave `697bd8c6…`, and b11 recorded `b046088d…`. The wheel is not reproducible. Record the digest of the wheel that the operator publishes, in the release step.
- State the exact rule for the `first_pass_rate` column in the route report before it is used to judge a route (see Route evidence).
- In the seed for a later wave, copy the shim and cache rule as written in the spec. The shim needs the network once for each pinned commit.

## Library defects

none

Probes that I ran, all as expected:

- `python3 -m deterministic_controls --help` lists `list`, `version`, `explain`, `check`, `adopt`. `adopt --help` lists `audit`, `plan`, `apply`, `receipt`.
- `check --root <dir without controls.toml> --profile quick` prints `configuration error: manifest not found` and exits `2`.
- `check --root <repository> --profile quick --format json` gives `schema_version`, `tool_version`, `repository_revision`, `control_revision`, `config_digest`, `profile`, `status`, and for each check `check_id`, `status`, `duration_ms`, `findings`, and `reason` for a skipped check. In profile `quick`, `security.secrets` runs and the other six checks are `skipped` with a reason.
- `tests/test_adopt.py` covers the five audit classes, a dry run, idempotent apply, a dirty tree, a detached HEAD, no push, the receipt fields and the shim with a fake cache, with no cache and with no network.
- `docs/fault-matrix.md` and `tests/test_mutation.py`, `tests/test_metamorphic.py` hold the mutation and the metamorphic cases. Times: 100 files 0.03 s, 1,000 files 0.24 s, 10,000 files 2.32 s.

Not proved by a probe: the shim creating a real virtual environment from the pinned git URL. The tests use a fake cache. Step 08 and the first adoption in a real repository prove it.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, rows for this wave:

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic-controls | claude | claude-sonnet-5-5 | 12 | 18 | 100% | 1619 | 84.0 | 12151536 | 199426 | 5.9197 |
| deterministic-controls | local | - | 3 | 3 | 0% | 16200 | 5400 | 0 | 0 | not reported |

Reading:

- The cloud agent (`claude-sonnet-5-5`) finished all 12 steps (b00 to b11). It used 18 attempts for 12 steps.
- The report shows `100%` first pass. The Git history does not agree: b02 and b08 were blocked after three attempts, because their `touches` did not cover an obsolete test. The operator widened `touches`, and the next attempt passed. I did not find why the report shows `100%`. Do not use it as a first-attempt rate for this wave. The report has no row that shows which steps needed more than one attempt.
- The local route (3 steps, 3 attempts, 0%, 16,200 seconds) did not pass. It is the bootstrap measurement in the plan: no edit in 70+ minutes. The fallback was the cloud agent. The owner decision of 2026-11-23 turns the local route off.
- No Codex steps ran in this wave.
