---
id: b07-forbidden-artifacts
status: pending
depends_on: [b03-self-ci]
touches:
  - src/deterministic_controls/checks/forbidden_artifacts.py
  - src/deterministic_controls/catalog/repo.forbidden-artifacts.toml
  - tests/test_forbidden_artifacts.py
  - tests/fixtures/forbidden_artifacts/**
  - plans/bootstrap/steps/b07-forbidden-artifacts.md
lane: none
agent: local
fallback: claude
gate: python3 -m unittest discover -s tests -p 'test_forbidden_artifacts.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/secret_guard.py --tracked && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the new check `repo.forbidden-artifacts`

Read `plans/bootstrap/plan.md` first. This check is new. It has no template script. It finds runtime files that Git tracks. Runtime output must live outside the repository.

## Change

- `checks/forbidden_artifacts.py`: a function `entry(context)`. List the tracked files with `git ls-files`. If the root is not a Git repository, use the file tree and skip the paths in `.git`. Report each tracked file that matches a pattern. Default patterns: `driver.out`, `ledger.jsonl`, `*.lock` under `plans/` folders, `.claude/settings.json`, `.claude/settings.local.json`, `.env`. The parameter `extra_patterns` (a list of globs in `controls.toml`) adds patterns. A pattern list is data. It is never a command. Rule ID: `repo.forbidden-artifacts.tracked`. Untracked files are not findings.
- `catalog/repo.forbidden-artifacts.toml`: id `repo.forbidden-artifacts`, status `advisory`, severity `error`, parameter `extra_patterns` (default empty), `module = "deterministic_controls.checks.forbidden_artifacts"`, `entry = "entry"`.
- Look at `checks/plans.py` and `catalog/plans.schema.toml` for the pattern. Use the `Finding` type of `core/`.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md`. Build each test repository at run time in a temporary directory with `git init` and `git add`. Do not store tracked runtime files in this repository.

- Good: a repository with no forbidden file, and a repository where `driver.out` exists but is untracked (in `.gitignore`). Both pass.
- Bad: one repository for each default pattern, one for a nested path (`plans/x/y.lock`), and one for an `extra_patterns` entry (for example `review/packets/**`). Each fails with the rule ID, the path and exit code `1`.
- A bad `extra_patterns` value (not a list of strings) is a configuration error (exit `2`).

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b01 to b03: the package, the CLI, the catalog loader, the plan checks and the CI job.

## Done when

- The gate passes. Each bad case fails for its own reason. The good cases pass.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
