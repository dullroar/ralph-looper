# Lessons from the `template` wave

Target: `repo-template`, child plan `adopt-controls`. Final plan commit: `a658fce8f56a397625d9491c44a14271992075c5`. Review date: 2026-11-24 (UTC).

`python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave template` printed `verified done` and `verify: 1/1 targets pass`.

I cloned `plan/adopt-controls` into a temporary directory. I ran `python3 -m unittest discover -s tests -v`. Result: 31 tests, 0 failures. This includes `test_template_smoke` (the fresh copy passes, fails with `plans.schema` for a step without a gate, and passes again; the old copy matches after `adopt apply`) and `test_workflow`.

Other checks, read with Git plumbing and in the clone:

- `AGENTS.md` has rule 5, "Do not weaken the controls". It names the pin, `controls.toml` and the workflows, and it says the driver checks the gate and `touches`. The routing summary is one sentence: "For routing, see `docs/routing.md`". `docs/routing.md` holds the policy. The summary in `AGENTS.md` is short but present.
- `plans/for-each-plan/steps/00-step-template.md` has the optional keys `agent`, `fallback`, `run`, `tier` and `acceptance_controls`, as comments. It has an operator-step example.
- `adopt apply` was used (commit `88cfe72`). Where it did not fit is recorded in `docs/controls-adoption.md`, section "Where the tools did not fit". I did not change any target repository.

## Keep

- Keep the secret guard as the first step of the child (m00). It ran on every step.
- Keep the shim contract: the old output lines, exit `2` if the library cannot run, and never a pass without a result.
- Keep the smoke test with two cases: a fresh copy and an old copy after `adopt apply`. Keep the known-bad plan that must fail with `plans.schema`. Assert exit codes and rule IDs, not versions.
- Keep the rule that the test skips with `library not available` only when there is no cache and no network.
- Keep the clean-clone verification, the receipt and the rollback test in the adoption document (m05). Later repositories can copy the format.
- Keep the optional routing keys as comments in the step template. Old plans still pass.
- Keep `docs/controls-adoption.md` as the place where each adoption records its gaps.

## Change

- Run `adopt apply` and then `python3 scripts/build_indexes.py --check` in the same step. Add the `Run me when:` line to `scripts/controls-requirements.txt` in the step, until the library writes it (see Library defects).
- Pass `--commit <pinned commit>` to `adopt plan` in every seed. Write it in the step text.
- Tell the agent to write `docs/controls-adoption.md` by hand. `adopt apply` does not write it.
- Do not tell an agent to install the library in a virtual environment. The agent session has no network and no install right. State the rule in the seed: the operator puts the pinned library on `PYTHONPATH` (this is already the rule of the parent plan).
- Expect the first run of the shim for each pinned commit to need the network. In the seed for each repository, tell the operator to run the shim once before the wave, so that the cache exists.
- Expect `apply` to add a `controls` job next to the existing `check` job in the workflow. Each seed must say what to do with the old job. Do not delete it in the first adoption.
- Put a one-sentence routing summary in `AGENTS.md` of each target, not only a pointer. The sentence must say that the cheapest executor does the work and that the gate decides.
- Do not use the `first_pass_rate` column to judge a route until the column rule is fixed (see Route evidence).

## Library defects

`adopt apply` writes `scripts/controls-requirements.txt` without a `Run me when:` line. Then `python3 scripts/build_indexes.py` and `--check` fail, because every file in `scripts/` needs that line. Probe: in a copy of the old template tree, run `adopt apply`, then `python3 scripts/build_indexes.py --check`. The m04 smoke test and the m01 step worked around it by hand. I did not run this probe again: I read the record in `docs/controls-adoption.md` and I ran the smoke test, which adds the line by hand. The next seed step must treat this as a defect to confirm. The step that confirms it asks the operator to release a patch version and run `pin.sh`, or it accepts the workaround in the seed text.

Usability defect (not a failure): `adopt plan` needs `--commit`, but the help text of `adopt audit` gives no hint. Probe: run `python3 -m deterministic_controls adopt audit --help` and look for `--commit`.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, row for this wave:

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| repo-template | claude | claude-sonnet-5-5 | 6 | 9 | 100% | 388 | 40 | 4285102 | 38708 | 1.6873 |

Reading:

- The cloud agent (`claude-sonnet-5-5`) did all 6 child steps (m00 to m05). It used 9 attempts for 6 steps. So at least three steps needed more than one attempt.
- The report shows `100%` first pass. This does not agree with 9 attempts for 6 steps. The same disagreement was seen in the `controls` wave. Do not use `first_pass_rate` as a first-attempt rate. Fix the column rule before the pilot, or count `attempts` against `steps`.
- No step needed its fallback executor. No other executor ran for this repository. The local route and Codex were not used in this wave.
- The wave cost 1.6873 USD for 388 seconds of agent time.
