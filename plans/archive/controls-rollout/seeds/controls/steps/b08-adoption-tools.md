---
id: b08-adoption-tools
status: pending
depends_on: [b03-self-ci]
touches:
  - src/deterministic_controls/adopt/**
  - tests/test_adopt.py
  - tests/fixtures/adopt/**
  - adoption/repos.example.toml
  - plans/bootstrap/steps/b08-adoption-tools.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_adopt.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/secret_guard.py --tracked && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Build the adoption tools: `adopt audit`, `plan`, `apply` and `receipt`

Read `plans/bootstrap/plan.md` first. These tools put the library into other repositories. The operator runs them on real repositories later. In this step, run them only on fixtures that tests build at run time.

`b01` made `cli.py` call `deterministic_controls.adopt.main(argv)` when that module exists. `cli.py` is outside `touches`. Put the code in `src/deterministic_controls/adopt/` with `main(argv)` in `adopt/__init__.py`. If `cli.py` does not call it, stop. Set `status: blocked` and write the blocker under "Resume notes".

## Change

- `adopt audit --root DIR`: read only. Classify the repository as `compliant`, `partial`, `needs-shims`, `not-suitable` or `blocked`. Report: template-derived or not (the `scripts/` and `plans/` layout), languages, CI files, test commands, current checks, and case-sensitive path issues (two paths that differ only by case). Output text or JSON.
- `adopt plan --root DIR --commit SHA`: print the diff that `apply` would make. It changes nothing.
- `adopt apply --root DIR --commit SHA`: works only on a clean tree and on the current branch. It never pushes, never changes a Git remote or a GitHub setting, and never commits. A second run changes nothing (idempotent). It keeps project-specific scripts and CI. It writes:
  - `scripts/check_context.py`, a shim that keeps the old output lines and exit codes of the template script. The shim runs the library from a cached virtual environment for the pinned commit, under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` (default `~/.cache/deterministic-controls/<commit>/`). It creates the environment on first use (it needs the network once) and fails with exit `2` and a clear message if it cannot. It never falls back to the old scripts or to a pass.
  - `scripts/controls-requirements.txt` with the pinned install line: `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@<commit>"` (the real commit replaces `<commit>`).
  - `controls.toml` with `schema_version = 1`, the profile and the enabled checks.
  - `scripts/secret_guard.py` and `scripts/install_hooks.sh`, copied from the library, so that the hooks work offline. The library keeps the reference copies inside the package as data files under `src/deterministic_controls/adopt/templates/`. Copy them from `scripts/secret_guard.py` and `scripts/install_hooks.sh` of this repository when you build the templates.
  - a `controls` job in `.github/workflows/context.yml` that keeps the names of the existing jobs. Permissions `contents: read`. Actions pinned to full SHAs. The job runs the shim, `secret_guard.py --tracked`, and on pull requests `secret_guard.py --range`.
  - Template files live under `adopt/templates/` and use the placeholder `<commit>`.
- `adopt receipt --root DIR --commit SHA`: write the adoption receipt as JSON. Fields: `schema_version`, `repository` (the directory name), `base_revision`, `control_pin` (the commit), `date`, `profile`, `enabled_checks`, `files_added`, `files_changed`, `commands_kept` (existing entry points, tests and Docker gates that stayed), `checks_run` with each status, `enforcement_state` (`advisory` until the owner changes it), and `rollback` (the exact steps to restore the previous pin or remove the adoption). It holds no secret and no local path.
- `adoption/repos.example.toml`: an example list with placeholder names only. No real target.
- The check catalog and `core/` are outside `touches`. Do not change them.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md`. Build repositories at run time in a temporary directory with `git init`. Cases:

- Classification: one fixture for each of the five classes, with the expected class.
- `plan` prints the diff and changes no file.
- `apply` on a dirty tree, on a detached HEAD, and with a bad commit value fails with a clear message and changes nothing.
- `apply` twice: the second run changes nothing. A project script and a project CI job stay.
- The shim keeps the old output lines and exit codes. With no network and no cached environment it exits `2`. It never prints a pass in that case.
- `receipt` has all fields, holds no local path, and its `rollback` field is not empty.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- b00 to b03: the guard, the package, the CLI, the catalog loader, the plan checks and the CI job.

## Done when

- The gate passes. Each failure case fails for its expected reason. `apply` is idempotent.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
