---
id: r01-adopt
status: pending
depends_on: []
touches:
  - scripts/check_context.py
  - scripts/controls-requirements.txt
  - controls.toml
  - .github/workflows/context.yml
  - AGENTS.md
  - docs/controls-adoption.md
  - docs/README.md
  - scripts/AGENTS.md
  - plans/AGENTS.md
  - plans/runner-adopts-controls/steps/r01-adopt.md
lane: none
gate: python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && grep -q 'd9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5' scripts/controls-requirements.txt && test -s controls.toml && test -s docs/controls-adoption.md && grep -q 'controls-adoption.md' docs/README.md && grep -q '^  check:' .github/workflows/context.yml && grep -q '^  controls:' .github/workflows/context.yml && grep -q '^  runner-tests:' .github/workflows/context.yml && ! grep -qE 'continue-on-error|paths:|paths-ignore:|secrets\.' .github/workflows/context.yml && ! grep 'uses:' .github/workflows/context.yml | grep -vqE '@[0-9a-f]{40}' && grep -q 'controls.toml' AGENTS.md && git diff --quiet "$(git merge-base HEAD main)" -- scripts/install_hooks.sh && bash scripts/install_hooks.sh --self-test && bash tests/run.sh && python3 tests/test_fanout.py && python3 tests/test_report.py && python3 tests/test_check_records.py && python3 tests/test_secret_guard.py && git diff --check
evidence: ""
---

# Adopt the pinned controls

Goal: `ralph-looper` runs the deterministic controls in CI, pinned to v0.2.0 (`d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5`).

## Facts you cannot find alone

- The library is on `PYTHONPATH` already. Run it as `python3 -m deterministic_controls adopt plan --root .`, then `adopt apply --root . --commit <pin>`. Do not install anything.
- `adopt apply` rewrites `scripts/install_hooks.sh`. Restore it from the base commit. The gate checks it.
- The ruleset of this repository requires the check `check`. Keep that job and its steps. `adopt apply` adds the `controls` job.
- Add a job `runner-tests`. It runs `bash tests/run.sh`, `python3 tests/test_fanout.py`, `python3 tests/test_report.py`, `python3 tests/test_check_records.py` and `python3 tests/test_secret_guard.py`. Use `permissions: contents: read`.
- Pin `actions/checkout` to `11d5960a326750d5838078e36cf38b85af677262` with the comment `# v4.4.0` in every job.
- `AGENTS.md`: add the rule "CI runs the controls in all cases. Do not change the controls, the pin, `controls.toml` or the workflows to make an unrelated task pass." Keep the file in Simplified Technical English.
- `docs/controls-adoption.md`: the pin, what `adopt apply` changed, the receipt from `adopt receipt`, and the rollback (change the pin, or revert the merge commit). Add it to `docs/README.md`.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date. If you cannot finish, write "Resume notes" below and keep `status: in_progress`.

## Resume notes

(none)
