---
gist: "Read me when: you want the final state of the controls rollout: the adoption matrix, what the program does not prove, the route evidence and the backlog."
---

# Final audit of the controls rollout

Audit date: 2026-11-24 (UTC). Step: `36-final-audit`.

This audit reads the records of the plan. It does not change any other repository. The audit agent could run commands only inside this worktree. So it could not run the context check in the other repositories again. Section 2 says what that means.

## 1. Verdict

The program is one coherent system. It is not finished in four places:

0. **The `fleet` wave does not verify now.** `lmdb-fs` fails `fanout.py verify` (see section 3 and B13).

1. **No repository has enforced protection.** All 14 rows of `enforcement.tsv` have the state `documented-gap`. The reason is an owner decision: the ruleset keeps the admin bypass and has no code owner review. Agents use the owner's credentials, so an agent can merge past a red check.
2. **The adoption of `ralph-looper` is not in this repository.** Step `09-runner-adopts-controls` has `status: done`. But this branch has no `controls.toml`, no `scripts/controls-requirements.txt` and no `docs/controls-adoption.md`. `git log --all` shows no commit for them. The step file still has "Resume notes" that say the step was blocked on network access. The gate of step 09 passed, because it only runs the old checks and the runner tests. The gate did not require the files. See B1.
3. **The `v4-es-1` translation plan is written and not run.** This is by design (see the goal).

## 2. Adoption matrix

Source of each cell: `pins.tsv`, `enforcement.tsv`, the lessons files and the wave manifests. "Receipt" is the file `docs/controls-adoption.md` in the repository. The receipt of a repository is on its adopted branch. The audit agent read the receipts through the lessons of the review steps, not from the repositories.

Pins in `pins.tsv`:

| Tag | Commit |
| --- | --- |
| `v0.1.0` | `651543baf8d308ec4e0ca0e69fb12a52fb0d6848` |
| `v0.1.1` | `0323de273a158608f7280867e12994141bccd1e6` |
| `v0.1.2` | `3a2e9f3d95136958c54f73c831e84b971fc9a054` |
| `v0.2.0` | `d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5` |

Rollback has two options in every child record. Option A: change the pin in `scripts/controls-requirements.txt` to an earlier commit. Option B: revert the adoption commits with `git revert` (the commit list is in the Rollback section of `docs/controls-adoption.md`). The exact revert command needs the adoption commit IDs. Those IDs are in each record. This audit does not copy them, because it did not read them.

| Repository | Pin | Profile | Receipt | Enforcement state | Rollback |
| --- | --- | --- | --- | --- | --- |
| `deterministic-controls` | own source (self check at its own revision) | `full` | release record of `v0.1.0` and `v0.2.0` | `documented-gap` (check: `check+controls`) | Move the pin of each consumer to an earlier tag. |
| `repo-template` | `v0.1.x` (wave `template`; final plan commit `a658fce8`) | `ci` | `docs/controls-adoption.md` | `documented-gap` (check: `context`) | Option A or B of the record. |
| `ralph-looper` | **not found in this repository** (see B1) | not recorded | **not found** | `documented-gap` (check: `check`) | Not applicable until B1 is closed. |
| `metadata_driven_gx` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `duckdb-fs` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `compliance_poc` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `ffmpeg_mcp` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `gpx_parser` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `lmdb-fs` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `metadata_mcp` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `pandoc_mcp` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `sample_parse` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `vips_mcp` | `v0.1.2` | `ci` | `docs/controls-adoption.md` | `documented-gap` | Option A or B of the record. |
| `aprende-a-programar-como-un-bicho-raro` | `v0.2.0` is the pin set by plan step `x01` of `v4-es-1` (not yet run); the adoption wave used the pin of its seed | `ci`, then pack in advisory mode | `translation/controls-adoption.md` | `documented-gap` (check: `controls+secret-guard`) | Option A or B of the record. Do not resume `loop/ralph.sh`. `loop/STOP` stays. |

Notes on the matrix:

- The pilot and fleet receipts all show seven checks passed and the state `advisory` at adoption. Step 34 then recorded each state in `enforcement.tsv`. No receipt was updated afterwards in the evidence that this audit read.
- The receipt text of a fleet repository can name a wrong base revision. The Rollback section of the record is the correct source (fleet lessons).
- `lmdb-fs` has an allowlist `.dockerignore` without `!controls.toml`. The image runs the library with its default `ci` configuration, not with `controls.toml`. The fleet lessons ask the operator to add the line. This audit found no record that it was added. See B5.

### Enforcement gaps

From `enforcement.tsv` (all 14 rows, date 2026-11-24):

- All rows: `documented-gap`. The ruleset keeps the admin bypass in `pull_request` mode. There is no code owner review. A producer with the owner's credentials can merge with `--admin` past a red check.
- Workflow probes ran on the pilot `vips_mcp` only. The other 13 rows show one probe (an `.env` file in CI), blocked. The audit assumes the same ruleset shape. This is not measured for each repository.
- `vips_mcp`: 7 of 11 probes were blocked (`env-file`, `allow-blanket`, `remove-controls-job`, `rename-check`, `path-filter`, `blanket-ignore`, `checker-crash`). Four got through: `continue-on-error`, `if-false`, `remove-check-id` and `swap-pin`. The probe `delete-fixture` did not apply (no `tests/fixtures`). The row says that code owner review is needed to stop the four. So an attacker with a normal pull request can weaken the CI job and the pin in the repositories that use the same ruleset shape.
- The translation repository was made public on 2026-11-24 (owner decision) so that its ruleset is enforced. The hook `loop/push-backup.sh` can no longer push directly to `loop/es-v4`.
- Hooks (secret key and `.env` file) blocked at pre-commit and pre-push in all repositories where the probe ran. Hooks run on one machine and a producer can skip them.

## 3. Baseline comparison

The baseline is `plans/runner-routing/baseline.tsv` (13 repositories, 2026-11-23). The audit agent could not run the context check in the other repositories (commands outside this worktree were denied). So the right column is from the review records, not from a new run.

| Repository | Baseline context check | Baseline test command and result | Result after the rollout (source) |
| --- | --- | --- | --- |
| `ralph-looper` | pass | `bash tests/run.sh` pass | `python3 scripts/check_context.py` passes now (run in this step). `tests/run.sh` was the gate of step 09 (passed). The controls library is not wired in (B1). |
| `repo-template` | pass | none | `fanout.py verify` passes. 31 unit tests pass, with the smoke test (lessons `template`). |
| `aprende-a-programar-como-un-bicho-raro` | absent | `tools/verify.py --fast` fail | Step t08 compared with the baseline: `verify.py --fast` same, tool tests same (10 failures, 5 errors, 1 skip as before), queue counts same (322 done). The context check now exists. The failures are old and are not fixed. |
| `compliance_poc` | pass | Docker gate, not run | Seven checks pass. The Docker gate ran in step a04 and the verify gate. |
| `duckdb-fs` | pass | Docker gate, not run | Same. |
| `ffmpeg_mcp` | pass | Docker gate, not run | Same. |
| `gpx_parser` | pass | Docker gate, not run | Same. |
| `lmdb-fs` | pass | Docker gate, not run | Same. The Docker gate does not use `controls.toml` (B5). |
| `metadata_driven_gx` | pass | Docker gate, not run | Same. |
| `metadata_mcp` | pass | Docker gate, not run | Same. |
| `pandoc_mcp` | pass | Docker gate, not run | Same. |
| `sample_parse` | pass | Docker gate, not run | Same. |
| `vips_mcp` | pass | Docker gate, not run | Same. |

The baseline says `not-run` for the Docker gate, so there is no earlier result to compare. The new result is "passed in step a04". That shows the gate works after the change. It does not show that the gate gave the same result before.

`deterministic-controls` is not in the baseline. It did not exist on 2026-11-23.

The `fanout.py verify` command was run for the seven waves on 2026-11-24. Six pass: `controls`, `template`, `pilot`, `translation-adopt`, `translation-pack` and `translation-work` (the last one: `verified seeded`, as the plan is not run on purpose).

**The `fleet` wave fails: 7 of 8 targets pass.** The failing target is `lmdb-fs`. The message is `plan/adopt-controls differs from the recorded plan SHA`. The branch moved after the recorded run (recorded final plan commit in the review: `0004e414f71017823879f70c5e73e2d46dbba641`). The audit agent could not read that repository, so it does not know the new commit. The probable cause is the follow-up change that the fleet lessons ask for (add `!controls.toml` to `.dockerignore`). This is a guess. See B13.

## 4. Route summary

Source: `route-report.md` (output of `lib/report.py`). Rows for the plans of this program:

| Plan | Route | Steps | Attempts | USD |
| --- | --- | --- | --- | --- |
| `runner-routing` | `claude` (Opus 5.5) | 4 | 4 | 8.7622 |
| `runner-routing` | `claude` (Sonnet 5.5) | 3 | 6 | 1.9425 |
| `runner-routing` | `codex` (`gpt-6.1-terra`) | 2 | 2 | not reported |
| `controls-rollout` | `claude` (Sonnet 5.5) | 16 | 19 | 15.7471 |
| `controls-rollout` | `script` | 2 | 2 | 0.0 |
| `bootstrap` (controls wave) | `claude` | 12 | 18 | 5.9197 |
| `bootstrap` (controls wave) | `local` | 3 | 3 | not reported |
| `adopt-controls` (template, pilot, fleet) | `claude` | 46 | 86 | 15.3138 |
| `adopt-controls` | `script` | 10 | 10 | 0.0 |
| `adopt-ralph` (translation) | `claude` | 9 | 21 | 5.0281 |
| `translation-pack` | `claude` | 10 | 10 | 6.8716 |

Sum of the reported `claude` rows of the program (`runner-routing`, `controls-rollout`, `bootstrap`, `adopt-controls`, `adopt-ralph`, `translation-pack`): 59.59 USD. This is the sum of the cost column. It does not include the `codex` and `local` rows (cost not reported) or the Batch API (not used by this plan).

Fallback rate: no step used a fallback executor in the waves that the lessons describe. The only fallback was an operator amendment. The `local` route has 3 attempts and 0 passes (the bootstrap measurement).

First-pass rate: **the column is not usable.** It shows 92% to 100% for rows with 1.5 to 3.3 attempts per step. The lessons say this in every wave. This audit does not quote it. Use attempts per step:

| Wave or plan | Attempts for each agent step |
| --- | --- |
| `bootstrap` (controls) | 1.50 (18 for 12) |
| `template` | 1.50 (9 for 6) |
| `pilot` | 3.25 (13 for 4, both repositories) |
| `fleet` | 1.59 (51 for 32) |
| `translation-adopt` | 2.33 (21 for 9) |
| `translation-pack` | 1.00 in the step files; the repository row shows 28 for 22 across two waves |

Which routing rules the evidence supports:

| Rule | Supported? | Evidence |
| --- | --- | --- |
| A `script` executor for deterministic steps (secret guard, pin record, report). | **Yes.** | 12 script steps, all passed on the first attempt, 0 USD. |
| Do not use the local model on this host. | **Yes.** | 3 steps, 0 passes, 16,200 seconds in all. One host, one model. The result does not apply to other hardware. |
| A cloud agent (Sonnet 5.5) for seed, adoption and review steps. | **Yes, with cost.** | Every agent step finished. About 1.5 attempts for each step when the seed was right. |
| A better seed lowers attempts. | **Partly.** | `fleet` (1.59) followed the lessons of `pilot` (3.25). The causes in the lessons are scope errors in `touches`, not executor quality. Two data points. No control group. |
| Opus for planning steps and Sonnet for the rest. | **No.** | `runner-routing` used Opus for 4 steps (8.76 USD) and Sonnet for 3. The two groups did different work. No step ran on both. |
| Codex as a cheaper or equal route. | **No.** | The `codex` rows of this program have no cost and no first-pass value. Codex ran 2 steps of `runner-routing`. |
| `tier: light` saves money. | **No.** | No row separates light steps from the others. |
| The Batch API route for the translation work. | **Not tested.** | The tool exists and has offline tests. No batch ran. |

## 5. What the program does not prove

- **Determinism does not prove meaning.** The controls check form: links, structure, index freshness, schema, secrets, forbidden files, and in the pack, fences, links, structure, glossary and chunks. A passing result says nothing about whether a plan is a good plan, whether a translation is correct or whether a document is true. The pack records two known undetected defects: a changed macro ID (`[[entry:m4]]` to `[[entry:m5]]`) and a dropped number in prose.
- **Fixture coverage is partial.** The library has 369 unit tests, a fault matrix and 26 planted defects in the pack. The lessons for `controls` say one thing is not proved by a probe: the shim creating a real virtual environment from the pinned Git URL (tests use a fake cache). The first real adoptions used it and passed. The probes in each repository cover seven known-bad cases. A new kind of defect that nobody planted is not covered.
- **The pack is not shown equal to the local translation tools.** The lessons of `translation-pack` say the comparison "same result as the local tool" was not done. It stays open (B3).
- **The secret scan is best effort.** `security.secrets` and `scripts/secret_guard.py` find patterns, and forbidden files. They do not find a secret with no known pattern. A committed secret cannot be undone by a later fix. The guard runs in hooks (the producer can skip them), in the driver, and in CI. CI is the barrier, and it is not enforced (see section 2).
- **Enforcement is not proved.** See section 2. Probe results exist for one repository (`vips_mcp`) only. Four of 11 probes got through there.
- **PowerShell coverage is as the tests ran it.** `tests/run-pwsh.sh` runs only where `pwsh` is installed. The audit agent did not run it and did not find a record that it ran in this program. The bash driver and the PowerShell driver must be equal (AGENTS.md rule). This audit does not prove it for the changes of this program. The program mostly changed the plan files, `lib/fanout.py` and `lib/report.py`, which are Python and run on both.
- **The pin is a commit, not a signature.** A pin to a commit protects against a moved tag. It does not prove the commit is good. The wheel is not reproducible (lessons `controls`). Do not compare digests of two builds.
- **Cost is partial.** The `codex` and `local` rows have no cost. The `first_pass_rate` column is wrong. The report groups by repository, so one repository row holds several waves.
- **This audit did not re-run other repositories.** Sections 2 and 3 are from records. The `fanout.py verify` gate reads the child plans and passes.

## 6. Backlog

Each item has its evidence. Items B1 to B6 are defects or open work in this program. Items B7 to B10 are the planned later phases.

| ID | Item | Evidence | Priority |
| --- | --- | --- | --- |
| B1 | Close the adoption of `ralph-looper` (step 09). Add the pin, `controls.toml`, `docs/controls-adoption.md`, the `runner-tests` job and the AGENTS.md rule. Then fix the gate of the step so that it needs these files. | Step 09 has `status: done` but its "Resume notes" say "Blocked". No commit adds `controls.toml` or `docs/controls-adoption.md` (`git log --all`). `enforcement.tsv` names the check `check`, not `context`. | High |
| B2 | Make the protection real: code owner review for the policy files, and no admin bypass for agents, or a separate agent account. Then run all 11 probes in every repository. | `enforcement.tsv`: 14 of 14 rows `documented-gap`. `vips_mcp`: `continue-on-error`, `if-false`, `remove-check-id` and `swap-pin` got through. | High |
| B3 | Compare each pack check with the matching tool of the translation repository on the real repository. Record each difference. | Lessons `translation-pack`, section "Not done". | Medium |
| B4 | Fix the `first_pass_rate` rule in `lib/report.py`, and add a per-wave filter. | Lessons of all waves: the column shows 92% to 100% against 1.5 to 3.3 attempts per step. Lessons `translation-pack`: the report cannot separate waves of one repository. | Medium |
| B5 | Add `!controls.toml` to the `.dockerignore` of `lmdb-fs`. Teach `adopt apply` to do it for an allowlist. | Lessons `fleet`, sections Change and Library defects. Three repositories failed the first attempt for this cause. | Medium |
| B6 | Fix three open usability defects of the library: `adopt apply` rewrites `scripts/install_hooks.sh`; `adopt receipt` in a clean clone gives empty file lists and the clone name; `adopt audit --help` does not show `--commit`. Also confirm that `adopt apply` writes the `Run me when:` line of `scripts/controls-requirements.txt` (the pilot lessons say it did). | Lessons `template`, `pilot` and `fleet`. | Low |
| B7 | **Language and toolchain packs** (phase 12). Start with Python, shell and Docker, because 13 of the 14 repositories have a Docker gate or Python tools. | The seven core checks are language neutral. Each repository still keeps its own tests and Docker gate, so the controls do not yet check code. | Plan next |
| B8 | **AI-generated control lifecycle** (phase 13). The rule "AI writes the control, a deterministic run uses it" has one example (the pack, 10 steps, 6.87 USD, 10 attempts for 10 steps). A lifecycle needs a review and retire rule. | `translation-pack` route row and its lessons. One data point only. | Plan next |
| B9 | **Fleet operations and upgrade waves** (phase 16). A pin upgrade is a pull request in each repository. The `v0.1.1` to `v0.1.2` change was a real case (one defect, fixed in the library). `lib/fanout.py` already runs a wave, and `pin.sh` records the pins. Missing: a way to list which repository has which pin, and a rollout order. | `pins.tsv`, lessons `pilot`. | Plan next |
| B10 | Optional adoption in `gpx_mcp`. | Named in the step text. It is not in any wave manifest. The goal says a repository outside the manifests is out of scope. Add it only after a new decision in `decisions.tsv`. | Optional |
| B11 | Decide whether a token check (macro IDs, numbers) belongs in the translation pack. | Lessons `translation-pack`, section Change. | Medium |
| B13 | Fix the `fleet` verify failure for `lmdb-fs`. Find the commits on `plan/adopt-controls` after the recorded SHA. If they are the `!controls.toml` fix, record them with `fanout.py amend` or re-record the SHA. Then run `fanout.py verify --wave fleet` again. | `fanout.py verify --wave fleet` on 2026-11-24: `lmdb-fs: plan/adopt-controls differs from the recorded plan SHA`; 7 of 8 pass. This blocks the gate of step 36. | High |
| B12 | Drop the local route from the planning default, and keep the measurement. Revisit it only for new hardware. | Decision `local_route`; `bootstrap` route row. | Done in practice |

### Open library defects

Library defects that are open (the lessons list no failure of a check):

- Wheel digest differs between two builds of one commit (lessons `controls`). Record the digest of the published wheel only.
- The three usability points in B6 and the allowlist `.dockerignore` gap in B5.

## 7. Archive step

After this plan merges into `main`, move `plans/controls-rollout/` and `plans/runner-routing/` to `plans/archive/` in a separate pull request. Run `python3 scripts/build_indexes.py` and `python3 scripts/check_context.py` in that pull request. Do not do it before B1 is decided: the open step 09 note is part of the history of the plan. The operator decides whether B1 blocks the archive.

This step does not push. It does not make the pull request.
