---
id: 05-docs
status: done
depends_on: [01-baseline-records, 02-fanout-tool, 04-route-report, 07-secret-guard]
touches:
  - README.md
  - AGENTS.md
  - docs/README.md
  - docs/routing.md
  - plans/runner-routing/steps/05-docs.md
lane: none
gate: python3 scripts/check_context.py && git diff --check && grep -q 'fanout.py' README.md && grep -q 'operator' docs/routing.md && grep -q 'report.py' AGENTS.md
claimed_by: claude cli-default
claimed_at: "2026-11-23T22:32:13Z"
evidence: gate passed 2026-11-23 (driver-verified)
---

# Write the routing policy and update the README and the agent contract

## Change

- `docs/routing.md`: step 03 wrote the front-matter reference. Add the routing policy for plan authors. Use the table in [plan.md](../plan.md#approach) as the base. For each route, give: when to use it, what the gate must prove, the cost and trust limits, and the fallback. Include these rules:
  - Prefer `script` when the work is deterministic. A model must not do what a script can do.
  - Use `local` only for bounded work with a strong gate. Always give a `fallback`. Use the route report to decide where `local` is good enough.
  - Batch API work is a plan-level tool in the repository that needs it. The operator submits and collects with an API key in the operator shell only. A `script` step imports the result. The normal gates validate it. No agent and no driver process holds the key.
  - `operator` steps hold approvals, publication, settings changes and work for named humans. The gate checks the result. Agents never get bypass rights.
  - The merge decision belongs to CI and the protected branch, not to the driver.
- `docs/README.md`: link `routing.md` and `fanout.md`.
- `README.md`: add a "Secrets" section (the guard, its modes, the hooks, the exception format, and `bash scripts/install_hooks.sh` for every clone). Document `agent`, `fallback`, `run`, operator steps, exit code 12, `--capabilities`, `lib/fanout.py`, `lib/report.py` and the local adapter. Remove the built items from "Not built yet". Keep the PowerShell warning unless step 03 ran the PowerShell test.
- `AGENTS.md`: add `lib/fanout.py`, `lib/report.py`, `scripts/check_records.py`, `scripts/secret_guard.py`, `scripts/install_hooks.sh` and `tests/run-pwsh.sh` to the file list. Add the rule: "Secrets are never tracked, committed or pushed. The guard runs in the pre-commit and pre-push hooks, in the driver before each merge, and in CI. Do not add an exception to make a step pass. An exception needs the owner's review." Add a rule: "The driver checks the gate and `touches` from the plan branch. Do not edit them in a step."

## Do not change

- Files outside `touches`. The gate command.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
