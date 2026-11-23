---
id: b10-release-prep
status: pending
depends_on: [b08-adoption-tools, b09-test-the-tests]
touches:
  - README.md
  - docs/**
  - CHANGELOG.md
  - scripts/release_check.sh
  - scripts/AGENTS.md
  - pyproject.toml
  - plans/bootstrap/steps/b10-release-prep.md
lane: none
gate: bash scripts/release_check.sh && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prepare release `v0.1.0`: docs, catalog page, changelog, release check

Read `plans/bootstrap/plan.md` first. Do not tag and do not publish. The operator does that.

## Change

- `scripts/release_check.sh`: a Bash script with a `Run me when:` line in its first 25 lines. It runs the unit tests, then the self check (`PYTHONPATH=src python3 -m deterministic_controls check --root . --profile full`), then a wheel build (`python3 -m pip wheel . --no-deps -w "$tmp"` with `tmp` from `mktemp -d`), and prints the SHA-256 of the wheel. It stops at the first failure. It leaves no file in the repository. Run `python3 scripts/build_indexes.py` to refresh `scripts/AGENTS.md`.
- `pyproject.toml`: change the version only, to `0.1.0`. Also make `python3 -m deterministic_controls version` print `0.1.0` (it reads the package metadata or one constant that `b01` created: do not edit `src/`; if the version has a second source in `src/`, stop and write that under "Resume notes").
- `README.md`: what the library is, the install line, a short example.
- `docs/` (all files except `docs/fault-matrix.md`): install, run, read a failure, upgrade with a pull request, roll back to the previous pin, the security limits (the secret scan is best effort; what CI can and cannot enforce; the public-repository and private-repository limits of branch protection), and the release policy (SemVer, immutable tags, release notes with added, changed, renamed and retired checks). A catalog page that lists each check: ID, status, severity, parameters and the rules (generate it by hand from `python3 -m deterministic_controls list`). Add each new document to `docs/README.md`. Write in Simplified Technical English. Do not write local paths, host names or user names.
- `CHANGELOG.md`: a `0.1.0` entry. List the added checks and the adoption tools. No check is renamed or retired.

## Do not change

- Files outside `touches`. The `gate` command. `docs/fault-matrix.md`.

## Already done by earlier steps

- b00 to b09: the guard, the package, all checks, the adoption tools, the tests of the tests and the fault matrix.

## Done when

- The gate passes. `release_check.sh` prints a wheel digest.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.
If the wheel build needs a network and none is available, write that under "Resume notes". Do not change the gate.

## Resume notes

(none)
