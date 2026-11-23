---
id: 01-baseline-records
status: pending
depends_on: []
touches:
  - scripts/check_records.py
  - scripts/AGENTS.md
  - tests/test_check_records.py
  - plans/runner-routing/baseline.tsv
  - plans/runner-routing/baseline.md
  - plans/runner-routing/steps/01-baseline-records.md
lane: none
gate: python3 tests/test_check_records.py && python3 scripts/check_records.py plans/runner-routing/baseline.tsv --min-rows 13 --columns repo,base,commit,context_check,test_command,test_result,ci_workflows,seconds --match 'commit=[0-9a-f]{40}' --match 'context_check=pass|fail|absent' && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Build a TSV record checker and record the baseline of 13 repositories

Later gates check recorded results (decisions, pins, receipts, baselines). They need one small deterministic checker, not ad-hoc code in each gate. Then record what works now, before the controls rollout changes anything (phase 0 of the controls plan).

## Change

- `scripts/check_records.py`: standard-library Python. Start with a comment block that has a `Run me when:` line. Interface:

  ```text
  check_records.py FILE [--min-rows N] [--columns a,b,c] [--match COL=REGEX]... [--require COL=VALUE]...
  ```

  FILE is UTF-8 TSV with a header row. Lines that start with `#` are comments. `--columns`: each named column exists and every cell in it is not empty. `--match`: every cell in COL matches REGEX with `re.fullmatch`. `--require`: every cell in COL equals VALUE. Print one line for each failure with the row number. Exit 0 if all pass, 1 if a record fails, 2 for a bad invocation or a missing or unreadable file. Never exit 0 on an exception.
- `tests/test_check_records.py`: `unittest` tests for each option. Cover a pass, each failure type, a missing file (exit 2), an empty file, comment lines and a bad regex (exit 2).
- `scripts/AGENTS.md`: regenerate with `python3 scripts/build_indexes.py`.
- `plans/runner-routing/baseline.tsv`: one row for each repository below. Columns: `repo`, `base` (default branch), `commit` (full SHA of the local default branch), `context_check` (`pass`, `fail` or `absent`, from `python3 scripts/check_context.py`), `test_command` (the repository's documented main test command, or `none`), `test_result` (`pass`, `fail`, `not-run` with the reason in `baseline.md`), `ci_workflows` (comma-separated workflow file names), `seconds` (wall time of the context check).
- `plans/runner-routing/baseline.md`: a short report. Per repository, give the notes that the TSV cannot hold: warnings, known failures, layout differences from `repo-template`, and checks that exist only in that repository. Also measure `bash tests/run.sh` in this repository (time and result).

Repositories (find them under `$REPOS_ROOT`): `ralph-looper`, `repo-template`, `aprende-a-programar-como-un-bicho-raro`, `compliance_poc`, `duckdb-fs`, `ffmpeg_mcp`, `gpx_parser`, `lmdb-fs`, `metadata_driven_gx`, `metadata_mcp`, `pandoc_mcp`, `sample_parse`, `vips_mcp`.

## Rules for the baseline

- Read only. Do not change, commit, fetch into or check out anything in another repository. Run each context check in a temporary `git worktree add --detach` of the default branch outside all repositories, or in `git archive` output. Remove the temporary tree after.
- Do not run Docker tests in this step. Record `test_result=not-run` and the reason "Docker gate, recorded by the 2026-11-22 rollout". The archived [rollout record](../../archive/ralphify-repositories/steps/02-verify-rollout.md) has those results.
- The translation repository has no `scripts/check_context.py`. Record `absent`. Its fast check is `python3 -I tools/verify.py --fast`. Record that result in `baseline.md`. Its working branch is the default branch.
- Do not write local paths, host names or user names in the records. Use repository names only.

## Do not change

- Files outside `touches`. The `gate` command.

## Done when

- The gate passes. The baseline has 13 rows.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
