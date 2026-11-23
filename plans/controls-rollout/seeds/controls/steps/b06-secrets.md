---
id: b06-secrets
status: pending
depends_on: [b03-self-ci]
touches:
  - src/deterministic_controls/checks/secrets.py
  - src/deterministic_controls/checks/personal_data.py
  - src/deterministic_controls/catalog/security.secrets.toml
  - src/deterministic_controls/catalog/security.personal-data.toml
  - tests/test_secrets.py
  - tests/test_personal_data.py
  - tests/fixtures/secrets/**
  - tests/fixtures/personal_data/**
  - plans/bootstrap/steps/b06-secrets.md
lane: none
gate: python3 -m unittest discover -s tests -p 'test_secrets.py' -v && python3 -m unittest discover -s tests -p 'test_personal_data.py' -v && python3 -m unittest discover -s tests -v && python3 scripts/secret_guard.py --tracked && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Port `security.secrets` and `security.personal-data`

Read `plans/bootstrap/plan.md` first. A weak secret rule is the most expensive defect in the library. Do this step with care.

Step `b00` installed `scripts/secret_guard.py` (the runner copy) and `tests/test_secret_guard.py`. Keep both. They stay as the compatibility reference.

## Change

- `checks/secrets.py`: port the guard with all its modes (`--staged`, `--range`, `--tracked`, `--history`, and the others that the guard has), its rules, placeholders, exception format (`secret-guard: allow <reason>` inline and `.secret-guard-allow` fingerprints) and redaction. A finding never prints a secret: only the first four characters and the length. The library entry checks the tracked files by default. It also exposes functions for the other modes, for use by the adoption tools and by the hooks.
- The library version must find everything that `scripts/secret_guard.py` finds on the same fixtures. A compatibility test runs both and compares the findings (rule, path, line).
- `catalog/security.secrets.toml`: status `required`, severity `error`, `mandatory = true`. Step `b01` built the key `mandatory`: `core/` runs a mandatory check in every profile, including `quick`, and treats an attempt to disable it in `controls.toml` as a configuration error (exit `2`). `core/` is outside `touches`: do not change it. If `core/` does not honor `mandatory`, stop. Set `status: blocked` and write the blocker under "Resume notes".
- `checks/personal_data.py` and `catalog/security.personal-data.toml`: port `scripts/scan_secrets.py` (personal paths and e-mail addresses in Markdown of the context folders). Status `advisory`, severity `error`.
- Use the `Finding` type of `core/`. Look at `checks/plans.py` for the pattern.

## Fixtures and tests

Follow the fixture rule in `plans/bootstrap/plan.md`. Build every synthetic secret, personal path and e-mail address at run time from parts, in a temporary directory. A tracked file must never hold one. Keep the test that builds every synthetic secret at run time. The guard must find nothing in `tests/` and `src/`.

- Good case: a repository with placeholders such as `example`, `changeme` and `****`, and an allowed line. It passes.
- Bad cases: one for each token rule and each assignment rule of the guard, a private key header, a forbidden file name, a secret in an earlier commit of a range, and a secret in history only. Each fails with the expected rule ID, path, line and exit code `1`.
- The report never contains the secret. A test searches the whole text and JSON output for the full synthetic value.
- Personal data: a personal path and an e-mail address fail. A placeholder path (`/home/<user>/...`) passes.
- `security.secrets` cannot be disabled (exit `2`) and runs in the `quick` profile.

## Do not change

- Files outside `touches`. The `gate` command. `scripts/secret_guard.py` and `tests/test_secret_guard.py`.
- Never add an exception to `.secret-guard-allow` to make a test pass.

## Already done by earlier steps

- b00-secret-guard: the guard, the hooks and the CI job. b01 to b03: the package, the CLI, the catalog loader, the plan checks and the CI job.

## Done when

- The gate passes. The library finds all that the runner copy finds. The secret check is mandatory.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
