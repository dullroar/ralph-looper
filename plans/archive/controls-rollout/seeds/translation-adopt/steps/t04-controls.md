---
id: t04-controls
status: pending
depends_on: [t02-layout]
touches:
  - controls.toml
  - scripts/controls-requirements.txt
  - scripts/check_context.py
  - scripts/AGENTS.md
  - .github/workflows/context.yml
  - tools/test_controls.py
  - translation/controls-adoption.md
  - plans/adopt-ralph/steps/t04-controls.md
lane: none
gate: python3 -m unittest discover -s tools -p 'test_*.py' && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && python3 -I tools/verify.py --fast && grep -q '0323de273a158608f7280867e12994141bccd1e6' scripts/controls-requirements.txt && grep -q 'verify.py --fast' .github/workflows/context.yml && grep -q 'secret_guard.py --tracked' .github/workflows/context.yml && grep -q 'permissions' .github/workflows/context.yml && ! grep -q 'continue-on-error' .github/workflows/context.yml && ! grep 'uses:' .github/workflows/context.yml | grep -Evq '@[0-9a-f]{40}' && grep -q 'canaries.key.json' controls.toml && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Adopt the pinned controls in advisory CI

The secret guard is already blocking (`t00`). This step adds the other controls. They are advisory: the `controls` job reports, and it is not a required check yet.

## Change

- Use `adopt audit`, `adopt plan --commit 0323de273a158608f7280867e12994141bccd1e6` (a dry run) and `adopt apply` where they fit. Run `apply` first, before other edits, because it needs a clean tree. Then run `python3 scripts/build_indexes.py --check`. If `scripts/controls-requirements.txt` has no `Run me when:` line, add one by hand. Do not install anything: the pinned library is on `PYTHONPATH`.
- `scripts/check_context.py` is the shim of the library. Keep the old output lines and the exit codes. It exits `2` if the library cannot run. It never passes without a result.
- `controls.toml`: scope the checks so that a run on this repository is short (thousands of Markdown files). Select the checks that fit; explain each choice in `translation/controls-adoption.md`. Put these paths in the `repo.forbidden-artifacts` list: `review/canaries.key.json`, `review/packets/**`, `review/repo-bundle.zip`, `review/units.index.jsonl`, `loop/driver.out*`. Use `python3 -m deterministic_controls explain repo.forbidden-artifacts` for the syntax.
- `.github/workflows/context.yml`: keep the `secret-guard` job and its steps. Add a job `controls` that installs the library from `scripts/controls-requirements.txt`, runs `python3 -m deterministic_controls check --root . --profile ci`, and runs `python3 -I tools/verify.py --fast`. Triggers: `pull_request` and `push` to `loop/es-v4`. `permissions: contents: read`. Pin every action to a 40-character commit SHA. No secrets. The `controls` job is advisory: do not make it a required check. Keep `pdf-release-gate.yml` and `sandbox-gate.yml` unchanged.
- `tools/test_controls.py`: build a scratch Git repository at run time with a minimal `controls.toml` and a tracked `review/canaries.key.json`. Run the `repo.forbidden-artifacts` check there. Assert that it fails with that rule ID (known bad). Remove the file and assert that it passes (known good). Skip with the message `library not available` only if the library cannot be imported.
- `translation/controls-adoption.md`: the receipt of the adoption (`adopt receipt`), the scope decisions, "Where the tools did not fit", and the rollback steps (delete `controls.toml`, `scripts/check_context.py`, the `controls` job).
- Run `python3 scripts/secret_guard.py --history`. Write the finding count in `translation/controls-adoption.md`. The planning audit of 2026-11-23 found none. A different count is blocking: write "blocked".

## Do not change

- Files outside `touches`. The `gate` command. `tools/inventory.py`.
- Do not add an exception to `.secret-guard-allow`.

## Already done by earlier steps

- t00-secret-guard: the guard, the hooks, the `secret-guard` job, the registration.
- t02-layout: `build_indexes.py`, the rules and the indexes.

## Done when

- The gate passes. The probe test fails for the right reason on the bad copy and passes on the good copy.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
