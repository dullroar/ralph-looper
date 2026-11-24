# Lessons from the `translation-pack` wave

Target: `deterministic-controls`. Child plan: `translation-pack`. Review date: 2026-11-23 (UTC).

| Target | Final plan commit |
| --- | --- |
| `deterministic-controls` | `0620d2c8f59de75ae21b87677f9046183f383657` |

`python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave translation-pack` printed `verified done` and `verify: 1/1 targets pass`.

I read the child branch `plan/translation-pack` with Git plumbing only. I did not change any target repository.

What I checked:

- Release check. I cloned `plan/translation-pack` into an excluded `.probe/` folder and ran `bash scripts/release_check.sh`. It passed: 369 unit tests, self check (profile `full`) `passed` with 7 checks, and the wheel `0.2.0` built. The step p10 record agrees (369 tests, 0 history findings).
- Opt-in. The self check passes with the pack not enabled in `controls.toml`. The test file `tests/test_translation_fail_closed.py` covers a repository with no pack configuration, and each pack check enabled with no parameters. Both pass with no findings. A pack check that is named but not in the catalog gives exit 2.
- Pack scope. The child has 10 steps (p01 to p10). All are `done` with driver-verified gates. The checks are `translation.fences`, `.links`, `.structure`, `.glossary`, `.chunks`, `.untranslated-heuristic` (advisory only, severity `info`) and `markdown.required-headings`, `.front-matter`, `.document-ids`.
- Negative coverage. Step p09 has 26 planted defects, each failing for its own rule, and mutation and fail-closed tests. Speed: 100 pairs 0.13 s, 1,000 pairs about 1.2 s.
- Known limits recorded by p09: a changed macro ID (`[[entry:m4]]` to `[[entry:m5]]`) and a dropped number in prose are not detected by any pack check.
- **Not done: agreement with the local translation tools.** The child spec asks that each check gives the same pass or fail result as the matching tool of the translation repository, or that each difference is explained. No child step records this comparison. The child has no access to that repository. I did not run it either: the local tools need `polib` and project mapping files that do not exist yet, and writing them is more than a review. The comparison stays open. The operator or a later step must do it before the pack is called equal to the local tools (see Change).

## Keep

- Keep the seed design: one contract step (p01) and a shared module that later steps may not change. Seven check steps then ran in parallel after p01 without a scope conflict.
- Keep the rule "a bad fixture must fail for its own rule ID, path and exit code". Step p09 turned it into one catalog of planted defects with a good control for each.
- Keep the fail-closed rule (a bad config, a missing file or an unreadable file is a finding or an error, never a pass).
- Keep the advisory-only rule for heuristics. The catalog status and the severity `info` are tested.
- Keep the opt-in rule and its tests. The pack is not enabled in the library's own `controls.toml`.
- Keep the step "Resume notes for the review" habit. The children wrote the real limits there (empty-string parameters, CRLF handling).

## Change

- Add a step to the child seed that runs each new check on the real target repository at its adoption commit and records pass or fail next to the matching local tool. Give the agent the target files in the seed or in a fixture copy, because the child cannot read the target repository. Without it, the acceptance line "same result as the local tool" cannot be checked.
- Tell the agent in the seed that the runner rejects a manifest parameter that the catalog file does not declare. Declare each parameter in the catalog with `""` as "not configured". Put the filter for `""` in the shared helper in the first contract step. Steps p02, p03 and p08 each found this again.
- Tell the agent that `translation_common.scan_markdown` removes `\r`. A check that must find a line ending difference reads bytes itself.
- Do not read the `deterministic-controls` rows of `lib/report.py` as one wave. The report groups by repository, so the rows hold all waves of that repository. Ask the operator to give a wave-specific report, or compare the counts before and after the wave.
- Decide before the next translation seed whether a token check (macro IDs, numbers) belongs in the pack. Today it is a documented limit in `docs/fault-matrix.md`.
- Keep the rules of the earlier lessons that are not listed here. They still apply.

## Library defects

none

No step shows a wrong or missing result of a core check. The two undetected defects (macro ID, dropped number) are documented limits of the pack, not defects of a check that exists.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, rows for `deterministic-controls`. The report groups by repository. These rows hold the `controls` wave and this wave together. I cannot separate them. The `translation-pack` child had 10 steps (p01 to p10).

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic-controls | claude | claude-sonnet-5-5 | 22 | 28 | 100% | 3532 | 134.0 | 27462321 | 454366 | 12.7913 |
| deterministic-controls | local | - | 3 | 3 | 0% | 16200 | 5400 | 0 | 0 | not reported |

Reading:

- The cloud agent (`claude-sonnet-5-5`) did all 10 steps of this wave. Each step has a driver-verified gate. In the step files, the claim times run from 03:05 to 03:23 UTC on 2026-11-24 with no sign of a retry. The cumulative row shows 28 attempts for 22 steps.
- The `local` row (3 steps, 0% first pass) is from the earlier `controls` wave. It did not run in this wave.
- Every step of this wave passed on the cloud route. No fallback executor was used.
- The cumulative cost of the repository is 12.7913 USD. The share for this wave is not separable.
