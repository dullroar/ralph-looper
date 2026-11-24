---
gist: "Read me when: you make the controls checks required on GitHub (step 34), test that a producer cannot bypass them, or need the break-glass rule."
---

# Enforcement kit

This file is for the operator (the repository owner). It has the checklist, the exact commands and the bypass probes for step 34. A coding agent never runs the commands that change a GitHub setting. An agent never gets bypass rights.

## What a required check does and does not do

- A CI check that is not required is a notice. A producer can merge a change that fails it.
- A check is enforced only when a ruleset (or branch protection) requires it, and the platform enforces that ruleset.
- `CODEOWNERS` has an effect only with a rule that requires code owner review. The file alone blocks nothing.
- The pre-commit and pre-push hooks run on the machine of the producer. They help, but a producer can skip them. CI and the ruleset are the barrier.
- Do not claim enforcement that the platform does not give. Record `documented-gap` with the reason (see "Record the result").

## 1. Read the capability of each repository (read only)

The agent that wrote this kit could not run `gh` (permission denied). So the table below shows only what GitHub documents. The operator fills the `Visibility` column from the commands that follow. Do this before step 34.

Run these read-only commands for each repository. `OWNER` is the account that owns the repositories.

```bash
OWNER=<owner>
gh api "users/$OWNER" --jq '{login, type}'
gh api "user" --jq '{login}'
gh repo list "$OWNER" --limit 100 --json name,visibility,defaultBranchRef
gh api "repos/$OWNER/<repo>" --jq '{private, visibility, default_branch, permissions}'
gh api "repos/$OWNER/<repo>/rulesets" --jq '.[] | {id, name, enforcement}'
gh api "repos/$OWNER/<repo>/branches/<base>/protection" --jq '.required_status_checks' || echo "no branch protection"
```

If the owner is a user account, the plan (Free, Pro) shows in the account billing page. The REST API shows it for the signed-in user as `plan.name` in `gh api user`. Use that value in the last column.

What GitHub documents (verify it on the day you apply, because plans change):

| Feature | Public repository | Private repository |
| --- | --- | --- |
| Rulesets (required checks, required pull request, block force push and deletion) | Yes, on all plans. | Only on a paid plan (Pro, Team, Enterprise). On Free the rules are stored but not enforced, or cannot be created. |
| Required status checks | Yes. | Paid plan. |
| Required reviews and code owner review | Yes. | Paid plan. |
| Bypass list | Yes (where rulesets are enforced). | Paid plan. |

Rows of the capability table (fill `Visibility` and `Plan` from the commands above):

| Repository | Base branch | Visibility | Plan | Rulesets | Required checks | Required reviews | Code owner review | Bypass list | Required check names |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `repo-template` | `main` | read it | read it | per row 1 of the feature table | same | same | same | same | `context` |
| `ralph-looper` | `main` | read it | read it | same | same | same | same | same | `context`, `runner-tests` |
| `deterministic-controls` | `main` | public (decision `visibility`) | read it | yes | yes | yes | yes | yes | `context` |
| `metadata_driven_gx` | `main` | read it | read it | per feature table | same | same | same | same | `context` |
| `duckdb-fs` | `main` | read it | read it | same | same | same | same | same | `context` |
| `compliance_poc` | `master` | read it | read it | same | same | same | same | same | `context` |
| `ffmpeg_mcp` | `main` | read it | read it | same | same | same | same | same | `context` |
| `gpx_parser` | `master` | read it | read it | same | same | same | same | same | `context` |
| `lmdb-fs` | `main` | read it | read it | same | same | same | same | same | `context` |
| `metadata_mcp` | `main` | read it | read it | same | same | same | same | same | `context` |
| `pandoc_mcp` | `main` | read it | read it | same | same | same | same | same | `context` |
| `sample_parse` | `master` | read it | read it | same | same | same | same | same | `context` |
| `vips_mcp` | `main` | read it | read it | same | same | same | same | same | `context` |
| `aprende-a-programar-como-un-bicho-raro` | `loop/es-v4` | private (plan risk list) | read it | **paid plan only** | **paid plan only** | **paid plan only** | **paid plan only** | **paid plan only** | `context` |

Rules for the last column group:

- A private repository on a free plan has no enforcement. Do not create a ruleset and call it protection. Record `documented-gap` for that repository (see section 6). The translation repository is private, so this applies to it unless the owner has a paid plan.
- The check name is the name that GitHub shows on the pull request, which is the job name. Check it on a recent pull request: `gh api "repos/$OWNER/<repo>/commits/<sha>/check-runs" --jq '.check_runs[].name'`. In some repositories the job id is `check` and the workflow name is `context`. Use the exact name that the command prints. If it is not `context`, use that name in every command below.
- For `ralph-looper`, `runner-tests` is the job that runs `tests/run.sh`. Use its exact name in the same way.
- `compliance_poc` has two workflows that use secrets (decision `compliance_poc_workflows`). The ruleset does not change them.

## 2. The ruleset

One ruleset for the base branch of each repository. It does these things:

1. Requires the `context` check (and `runner-tests` for `ralph-looper`), on a branch that is up to date with the base.
2. Blocks force pushes (`non_fast_forward`) and deletion of the base branch.
3. Requires a pull request. A direct push to the base branch is not allowed.
4. Requires code owner review. `CODEOWNERS` (section 3) limits that review to the policy files.
5. Has an empty bypass list. Break-glass (section 5) adds an entry for a short time.

Write the file `ruleset.json` in a temporary directory outside every repository. Change the `required_status_checks` list to the check names of the repository.

```json
{
  "name": "controls-required",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "context" } ]
      }
    }
  ]
}
```

For `ralph-looper`, use this value for `required_status_checks`:

```json
[ { "context": "context" }, { "context": "runner-tests" } ]
```

Create it, then read it back:

```bash
gh api --method POST "repos/$OWNER/<repo>/rulesets" --input ruleset.json
gh api "repos/$OWNER/<repo>/rulesets" --jq '.[] | {id, name, enforcement}'
gh api "repos/$OWNER/<repo>/rules/branches/<base>" --jq '.[].type'
```

The last command must list `deletion`, `non_fast_forward`, `pull_request` and `required_status_checks`.

To change a ruleset later, use `gh api --method PUT "repos/$OWNER/<repo>/rulesets/<id>" --input ruleset.json`. To test without effect first, set `"enforcement": "evaluate"` (available on Enterprise plans only). On other plans, apply to one repository first (`ralph-looper` or a pilot) and run the probes.

A sole owner cannot approve their own pull request. With `require_code_owner_review`, a pull request from the owner that changes a protected path then waits for a second code owner. Options: add a second human to `CODEOWNERS`, or use break-glass (section 5). Do not give the owner role a permanent bypass: an agent that works with the owner's credentials would get it too.

Use a token for coding agents that has write access to branches and pull requests but no admin access. A ruleset bypass needs admin access or an explicit bypass entry. An agent token has neither.

## 3. CODEOWNERS

Create `.github/CODEOWNERS` in each repository. It is a normal pull request, and the pull request itself touches a protected path. Merge it with break-glass, or before the ruleset exists.

```text
# Policy files. A change needs review by a code owner.
# This file has an effect only with a rule that requires code owner review.
/.github/workflows/**              @OWNER
/controls.toml                     @OWNER
/scripts/controls-requirements.txt @OWNER
/scripts/check_context.py          @OWNER
/tests/fixtures/**                 @OWNER
/.github/CODEOWNERS                @OWNER
/.secret-guard-allow               @OWNER
```

Replace `@OWNER` with the real owner login or a team. The last two lines go beyond the required list: without them a producer could change who must review, or add a blanket secret exception, with no review. Keep them. `scripts/secret_guard.py` and `scripts/install_hooks.sh` are good additions too.

Check the file: `gh api "repos/$OWNER/<repo>/codeowners/errors" --jq '.errors'` must print an empty list.

## 4. Bypass probes

A probe is a pull request branch that tries to get a bad change past the controls. The probe passes when the control **blocks** it. Run probes with `probes/make_probe.sh`. It clones the repository into a new temporary directory, never in the checkout under `$REPOS_ROOT`, and prints the push command. It never pushes.

```bash
export REPOS_ROOT RALPH_WORK
bash plans/controls-rollout/probes/make_probe.sh --hooks "$OWNER/<repo>" secret-key
bash plans/controls-rollout/probes/make_probe.sh "$OWNER/<repo>" continue-on-error
```

`--hooks` also installs the hooks in the clone, tries the commit and tries a push to a local bare repository. It prints `pre-commit: BLOCKED` and `pre-push: BLOCKED` when the hooks work. Use it for `secret-key` and `env-file`. Set `PROBE_JOB=<job id>` for the workflow probes when the job id is not `controls`. Use the job id of the `context` job for the rename and removal probes of that job.

Run the push command that the script prints. Then open a pull request from the probe branch to the base branch and read the result. Close the pull request and delete the probe branch afterwards. Each probe branch must be pushed by the operator, with the operator's credentials.

| Probe | What it changes | Expected block | How to read it |
| --- | --- | --- | --- |
| `secret-key` | Adds a file with a synthetic key built at run time. | Pre-commit hook, pre-push hook and the CI secret guard each fail. | `--hooks` output; then the CI job log of the pull request. |
| `env-file` | Adds a `.env` file. | Same three. The secret guard rejects the forbidden file name. | Same. |
| `allow-blanket` | Adds `*  **  ...` to `.secret-guard-allow`. | The guard ignores a blanket exception, and the code owner rule asks for review of `.secret-guard-allow`. | CI log, then the review request on the pull request. |
| `remove-controls-job` | Deletes the controls job from the workflow. | Code owner review on `.github/workflows/**`. The required check `context` is absent, so the merge is blocked (a missing required check blocks the merge). | Merge box of the pull request. |
| `rename-check` | Renames the job. | The required check name does not appear, so the merge is blocked. Code owner review also applies. | Merge box. |
| `continue-on-error` | Adds `continue-on-error: true` to the job. | Code owner review on the workflow file. A repository check that scans workflows for this key is a good addition. | Merge box, review request. |
| `if-false` | Adds `if: false` to the job. | A skipped job reports success for a required check, so only code owner review stops it. Confirm this in the pull request. | Merge box, review request. |
| `path-filter` | Adds a `paths:` filter to `pull_request`. | A pull request that touches other paths gets no check. The required check is then absent and the merge is blocked. Code owner review also applies. | Merge box. |
| `remove-check-id` | Removes a check ID from `controls.toml`. | Code owner review on `controls.toml`. The library fails if a mandatory check is missing. | CI log, review request. |
| `swap-pin` | Changes the pinned commit in `scripts/controls-requirements.txt`. | Code owner review on that file. Set `PROBE_ALT_COMMIT` to a real commit of the library to test a valid but different pin. | Review request. |
| `delete-fixture` | Deletes a bad fixture. | Code owner review on `tests/fixtures/**`. The library test that counts its fixtures fails, if the repository has one. | CI log, review request. |
| `blanket-ignore` | Adds an `[ignore]` section with `paths = ["**"]` to `controls.toml`. | The library rejects an unknown key (exit 2). Code owner review on `controls.toml`. | CI log, review request. |

If a probe is **not** blocked, the state is `documented-gap` for that repository. Write the probe name in the notes. Fix the gap or accept it in writing. Do not add an exception to make a probe pass.

Test the tool without a network: `bash plans/controls-rollout/probes/self_test.sh`. It makes each probe in a disposable local repository and checks the expected file change.

## 5. Break-glass

Use break-glass only when a required check or a protected-path review blocks a change that must go in, and no other way exists (for example, the check itself is broken). Rules:

1. **A named human.** The owner (or a named deputy) does it. No coding agent and no automation does it. Agents never get bypass rights.
2. **A written reason.** The reason is in an issue or in the pull request before the bypass: what blocks, why a normal fix is not possible, what the change is.
3. **One-time scope.** Add a bypass entry for one repository, with `bypass_mode` `pull_request`, for one pull request. Remove the entry right after the merge. Use this change to the ruleset (read the ruleset first, then put it back):

   ```bash
   gh api "repos/$OWNER/<repo>/rulesets/<id>" > ruleset.before.json
   # Edit a copy: set "bypass_actors" to one entry for the named person's role or team.
   gh api --method PUT "repos/$OWNER/<repo>/rulesets/<id>" --input ruleset.break-glass.json
   # Merge the one pull request.
   gh api --method PUT "repos/$OWNER/<repo>/rulesets/<id>" --input ruleset.before.json
   gh api "repos/$OWNER/<repo>/rulesets/<id>" --jq '.bypass_actors'
   ```

   The last command must print an empty list.
4. **An audit note.** Add one line to `plans/controls-rollout/enforcement.tsv` notes, or to the repository's `docs/`: date (UTC), who, the pull request, the reason, the time the bypass entry was removed. Do not write secrets or personal data.
5. **A follow-up issue.** Open an issue that names the root cause and the fix that makes the bypass unneeded. Close the loop: check that the normal path works again, and run the probe that matches.

## 6. Record the result

Fill one row for each repository in `plans/controls-rollout/enforcement.tsv` (step 34 does it):

- `state`: `required` when the ruleset is active and every probe was blocked. `documented-gap` in all other cases.
- `required_check`: the exact check names.
- `probes`: the list of probe names that were blocked, and the list that were not.
- `date`: the UTC date.
- `notes`: for a gap, the reason, for example "private repository on a free plan: rulesets are not enforced" or "probe if-false not blocked".

Do not mark `required` for a repository whose plan does not enforce rulesets.

## 7. Order of work for step 34

1. Read the capability of all 14 repositories (section 1). Fill the table in the step record.
2. Pick one pilot (`ralph-looper`). Create `CODEOWNERS`, then the ruleset. Run all probes. Fix gaps.
3. Repeat for the other repositories, public ones first.
4. Mark private repositories on a free plan as `documented-gap`.
5. Record `enforcement.tsv`. Run `python3 scripts/check_context.py`.
