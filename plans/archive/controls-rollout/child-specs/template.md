# Child spec: `adopt-controls` in repo-template

Wave `template`. Source phases: 5 and the plan-format part of 14. Every new repository gets the pinned controls and the routing fields from here. Use `adopt plan` and `adopt apply` from the pinned library where they fit. That is the first real use of the adoption tools. Record each place where they did not fit, for the lessons file.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| m01-shim | cloud agent | Adopt the pinned library with `adopt apply`. Keep `scripts/check_context.py` and `build_indexes.py` working. | none |
| m02-agent-rules | cloud agent | Agent rules for controls and routing. Plan template fields. | none |
| m03-ci | cloud agent | Pinned, read-only CI job with a stable name. | m01 |
| m04-smoke | cloud agent | Fresh-copy and old-copy smoke tests with a known-bad plan. | m01, m02, m03 |
| m05-verify | cloud agent, light | Clean-clone verification and receipt. | m04 |

## Step details

- **m01.** Touches `scripts/check_context.py`, `scripts/controls-requirements.txt`, `controls.toml`, `scripts/AGENTS.md`, `docs/controls-adoption.md`. Keep `scripts/build_indexes.py` (it writes indexes). Keep the old checker scripts until m04 proves equivalence. Then the shim calls the library. The shim keeps the current output lines and exit codes. It uses the pinned cache environment of the library (see the library README). It never falls back to a silent pass. Gate: `python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && git diff --check`.
- **m02.** Touches `AGENTS.md`, `plans/for-each-plan/**`, `docs/routing.md`. Add to `AGENTS.md`: the agent may run local checks; CI runs them in all cases; the agent must not change or disable the controls, the pin, `controls.toml` or the workflows to make an unrelated task pass; the driver checks each step's gate and `touches`. Copy the routing policy from the ralph-looper `docs/routing.md` (public URL) into `docs/routing.md` in short form, with a link to the source. In `plans/for-each-plan/steps/00-step-template.md`, add optional `agent`, `fallback`, `run`, `tier` and `acceptance_controls` (check IDs from the catalog) keys, as comments or empty values that `check_plan.py` accepts. Add an operator-step example. Old plans must still pass.
- **m03.** Touches `.github/workflows/context.yml`. Keep the job name `context`. Triggers: `pull_request`, `push` to `main`, `workflow_dispatch`. No path filters. `permissions: contents: read`. Actions pinned to full SHAs. Install from `scripts/controls-requirements.txt`. Run the `ci` profile with a JSON report and upload it. No `continue-on-error`.
- **m04.** Touches `tests/test_template_smoke.py` (or `scripts/smoke_template.sh`), `docs/controls-adoption.md`. Copy the template tree into a temporary directory as a new repository and run the check. It passes. Add a plan step without `gate`. It fails with the `plans.schema` rule ID. Do the same with a copy of the template at its previous pinned revision (the "old copy") after `adopt apply`: the result and exit codes match. Then delete the old checker scripts that the library replaced, only if the equivalence test passed.
- **m05.** Touches its step file and `docs/controls-adoption.md`. Run all gates from a clean clone. Write the receipt with `python3 -m deterministic_controls adopt receipt`. Record the rollback: set the previous pin in `scripts/controls-requirements.txt` and run the check.
