---
id: p10-release-prep
status: pending
depends_on: [p09-fixtures-and-matrix]
touches:
  - README.md
  - docs/**
  - CHANGELOG.md
  - pyproject.toml
  - src/deterministic_controls/__init__.py
  - plans/translation-pack/steps/p10-release-prep.md
lane: none
gate: rm -rf "${TMPDIR:-/tmp}/controls-p10" && git clone -q . "${TMPDIR:-/tmp}/controls-p10" && cd "${TMPDIR:-/tmp}/controls-p10" && bash scripts/release_check.sh && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && python3 -c "import sys; sys.path.insert(0, 'src'); import deterministic_controls as d; assert d.__version__ == '0.2.0'" && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prepare release `v0.2.0`: docs, catalog, changelog, version, history scan

Read `plans/translation-pack/plan.md` first. Do not tag and do not publish. The operator does that. The gate builds a clean clone and runs `scripts/release_check.sh` there (unit tests, self check, wheel build). You cannot run a clean clone or a wheel build in this session, so run the unit tests and the self check on your tree, and let the gate do the rest.

## Change

- `pyproject.toml` and `src/deterministic_controls/__init__.py`: set the version to `0.2.0`. These are the two version sources. No other file may hold a literal version that a test reads. If a test fails on the version, fix the test to read `__version__` and write it under "Resume notes" (its file is not in `touches`: stop and write it).
- `docs/catalog.md`: add every pack check (ID, status, severity, parameters, rules, and the "generic" sentence). Generate the rule list by hand from `python3 -m deterministic_controls list` and `explain`. Mark `translation.untranslated-heuristic` as advisory only.
- `docs/translation-pack.md`: complete the table (no row may say "added in step pN"). Add a short "adopt the pack" section: enable the checks, write the mapping file, write the exception file, how to run one check, and the limits (source tree inside the root; the heuristic is advisory; Spanish-specific rules stay in the translation repository). Add a "what stays out" list of the project-specific parts.
- `docs/upgrade.md` and `docs/install.md`: the release is `0.2.0`; use the placeholder `<commit>` for the install line of this release. Do not write local paths, host names or user names.
- `CHANGELOG.md`: a `0.2.0` entry. List the added checks and the pack contract. No check is renamed or retired. Core and the first seven checks are unchanged.
- `README.md`: one paragraph and a link for the pack.
- Run `python3 scripts/secret_guard.py --history`. Record the finding count under "Results". If it is not zero, list the rule IDs and paths, never the secret, and do not add an exception. List each exception in `.secret-guard-allow` and each inline `secret-guard: allow` for the owner.
- Record under "Results" the unit test count and the result of `PYTHONPATH=src python3 -m deterministic_controls check --root . --profile full`.

## Do not change

- Files outside `touches`. The `gate` command. `docs/fault-matrix.md`. `scripts/release_check.sh`.
- Do not record a wheel digest. A rebuild gives another digest. The operator records the digest of the wheel that is published.

## Already done by earlier steps

- p01 to p09: the pack, its checks, tests, fixtures and the fault matrix.

## Done when

- The gate passes. "Results" holds the numbers above.

## Results

(none)

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.
If the wheel build needs a network and none is available, write that under "Resume notes". Do not change the gate.

## Resume notes

(none)
