# Controls adoption

`ralph-looper` runs the deterministic controls in CI. This file records how.

## The pin

- Library: `deterministic-controls` v0.2.0.
- Commit: `d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5`.
- The pin is in `scripts/controls-requirements.txt`.
- The enabled checks are in `controls.toml` (profile `ci`).

## What `adopt apply` changed

- It added `scripts/controls-requirements.txt` and `controls.toml`.
- It replaced `scripts/check_context.py` with the library shim.
- It added the job `controls` to `.github/workflows/context.yml`.
- It rewrote `scripts/install_hooks.sh`. We restored that file from the base commit. It is unchanged.

We also made these changes by hand:

- The job `check` stays. The ruleset requires it.
- The job `runner-tests` runs `tests/run.sh` and the four Python tests.
- Every `actions/checkout` is pinned to a full commit SHA (`# v4.4.0`).
- `AGENTS.md` has a rule that CI runs the controls in all cases.

## Receipt

Command: `python3 -m deterministic_controls adopt receipt --root . --commit <pin>`.

- Date: 2026-11-24.
- Base revision: `04b21fb9cf6d020111f0818cbade062c732fb84d`.
- Profile: `ci`. Enforcement state: `advisory`.
- Checks enabled: 16. The receipt ran before the index and the links were rebuilt. It showed `context.index-freshness` and `markdown.local-links` as failed. Both pass after this change.

## Probes

Date: 2026-11-24. Each probe ran in a clone of this repository under `.probe/copy`. The clone is excluded from Git. Command: `python3 -m deterministic_controls check --root .probe/copy --profile ci --format json`. One defect at a time. We restored the clone after each probe.

The clean clone passed all 16 checks (exit code 0).

| Defect planted | Exit code | Check | Rule ID |
| --- | --- | --- | --- |
| A link to a file that does not exist, in a document | 1 | `markdown.local-links` | `markdown.local-links.missing-file` |
| A new script with a "Run me when" line, and no index rebuild | 1 | `context.index-freshness` | `context.index-freshness.stale` |
| A plan step with the `gate` key removed | 1 | `plans.schema` | `plans.schema.missing-gate` |
| A committed file with a token that looks like an AWS access key. The token was built at run time. | 1 | `security.secrets` | `security.secrets.aws-access-key-id` |
| A tracked file `ledger.jsonl`, added with `git add -f` | 1 | `repo.forbidden-artifacts` | `repo.forbidden-artifacts.tracked` |

Notes:

- The secret check reads the files at `HEAD`. A file that is only staged or only on disk is not enough. The check passed until we committed the file in the clone.
- A tracked file `.pem` (forced with `git add -f`) also fails. The rule is `security.secrets.forbidden-file`.
- We ran the shim `scripts/check_context.py` in the clone on the step without a gate. It exited with code 1 and printed `FAIL check_plan.py`.
- No planted defect and no token is in a tracked file of this repository.

## Rollback

- To go back to an earlier pin: change the commit in `scripts/controls-requirements.txt`. Then run `scripts/check_context.py` once to build the environment.
- To remove the adoption: revert the merge commit of the adoption pull request.
- The cached environment is in `~/.cache/deterministic-controls/<commit>/`. It is safe to delete.
