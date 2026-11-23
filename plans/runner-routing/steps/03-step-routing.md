---
id: 03-step-routing
status: done
depends_on: []
touches:
  - ralph-looper
  - ralph-looper.ps1
  - lib/pick_step.py
  - lib/agents.sh
  - lib/PROMPT.md
  - tests/run.sh
  - tests/run-pwsh.sh
  - tests/fake-agent.sh
  - docs/routing.md
  - plans/runner-routing/steps/03-step-routing.md
lane: none
gate: bash tests/run.sh && bash tests/run-pwsh.sh && for c in step-agent operator-step script-step local-agent gate-from-plan-branch touches-enforced; do ./ralph-looper --capabilities | grep -qx "$c" || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "2026-11-23: gate (tests/run.sh, tests/run-pwsh.sh, --capabilities words, scripts/check_context.py, git diff --check) passed. tests/run.sh PASS with 12 scenarios. PowerShell test NOT RUN: pwsh not installed. ralph-looper.ps1 is reviewed by reading only; parity is not proven by execution."
---

# Add per-step executors and close the gate and touches gaps

Today the whole plan runs with one `--agent`. Operator actions are rows in a table, not steps, so a parent plan must burn agent attempts on gates that wait for a human. The driver also reads the gate from the step file after the agent ran (`run_step` reads `$sfile` in the step worktree), and it commits every change with `git add -A`. An agent can weaken its own gate or change files outside `touches`. Fix all of this in both drivers.

## Front matter (all optional; old plans work unchanged)

| Key | Values | Meaning |
| --- | --- | --- |
| `agent` | `claude`, `codex`, `copilot`, `local`, `script`, `operator` | Executor for this step. Empty: use `--agent`. |
| `fallback` | an agent name | After one failed attempt with `agent`, use this agent. Also use it when the `agent` command is not available. |
| `run` | shell command | Only for `agent: script`. The driver runs it in the step worktree with the step timeout. |
| `tier` | `standard`, `light` | Already exists. Keep it. |

## Driver behavior

- **Executor choice.** Resolve the executor for each step: `agent` if set, `fallback` after a failed attempt, else `--agent`. If the resolved agent command is not on `PATH` and there is no fallback, do not start the step. Report it as "waiting: agent X not available".
- **`operator` steps.** Never start an agent. When the step is ready, run its gate in a fresh step worktree. If the gate passes, set `done` with evidence `gate passed <date> (operator step, driver-verified)`, commit, merge and continue. If it fails, leave the step `pending`, do not count an attempt, and print `waiting for operator: <step> (see plans/<plan>/steps/<step>.md)`. When no other step can run and at least one operator step waits, exit with the new code `12`.
- **`script` steps.** Run `run`, then the gate. No model call. Count attempts as for agents. Write a ledger line with `agent=script`, zero tokens and zero cost.
- **`local` agent.** Add an adapter in `lib/agents.sh` (and the PowerShell equivalent). Use `$LOCAL_AGENT_CMD` if set. Else use `local-coder-agent` from `PATH` (a wrapper that the operator installs; it runs Claude Code against the local model). Use the same allow and deny lists as `claude`. Print a clear error if neither exists. Never put a local path in the repository.
- **Gate from the plan branch.** Read `gate`, `touches`, `agent`, `fallback` and `run` from the step file in the plan worktree (`$PWT`), at the plan commit from which the step worktree started. Never read them from the step worktree after the agent ran.
- **Front matter integrity.** After the agent ran, compare those five keys in the step worktree with the plan-branch values. If one changed, fail the attempt with `result: <step> changed its own gate or scope`.
- **Touches enforcement.** Before the commit, list the changed paths (`git status --porcelain`, including untracked files, and the diff since the start commit). Each path must match a `touches` entry, with the same glob rules as `scripts/check_plan.py`, or be the step's own file, or be one of the generated index files (`memory/AGENTS.md`, `plans/AGENTS.md`, `scripts/AGENTS.md`). Otherwise fail the attempt and list the paths. Stage only the allowed paths. Do not use `git add -A`.
- **`--capabilities`.** Print one word for each line and exit 0: `step-agent`, `operator-step`, `script-step`, `local-agent`, `gate-from-plan-branch`, `touches-enforced`. Later plans check these words before they start.
- **Environment.** Export `RALPH_STEP_AGENT` (the resolved executor) for `lib/usage.py`. Step 04 records it.
- **New steps.** A merged step can add new step files to its plan. The next loop must pick them up. Test this.
- **`lib/PROMPT.md`.** Add one sentence: the driver checks the gate and the scope itself, so changes to them fail the step.
- **`lib/pick_step.py`.** Add what the drivers need: read the new keys, list waiting operator steps and the summary code for "waiting for operator".
- **PowerShell.** Make the same changes in `ralph-looper.ps1`. Add `tests/run-pwsh.sh`: if `pwsh` is on `PATH`, run a small PowerShell scenario (one agent step, one script step, one operator step). If not, print `PowerShell test NOT RUN: pwsh not installed` and exit 0. Record the result in this step file honestly.

## Tests in tests/run.sh (keep all current tests)

1. A fake agent says it is done, but the gate fails. The step is not done.
2. A fake agent edits its own `gate` to `true`. The attempt fails.
3. A fake agent writes a file outside `touches`. The attempt fails, and the file is not merged.
4. A `script` step runs with no agent call and appears in the ledger as `script`.
5. An `operator` step waits (exit 12) until a marker file exists, then passes on the next run with no attempt counted.
6. A step with `agent: local` and no local command runs with its `fallback`.
7. A merged step adds a new step file. The next loop runs it.
8. `kill -9` and restart still resume (the current test).

## Do not change

- Files outside `touches`. `lib/usage.py` (step 04 owns it). The gate command.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date. Write whether the PowerShell test ran.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

- Done on 2026-11-23. All work is committed on this step branch.
- `tests/run.sh` covers the 8 required tests (scenarios 1, 2 and 5 to 11) and `--capabilities` (scenario 12).
- `tests/run-pwsh.sh` printed `PowerShell test NOT RUN: pwsh not installed`. The PowerShell driver was not executed. Run `bash tests/run-pwsh.sh` on a host with `pwsh` before you claim parity.
- The driver writes two new runtime folders: `<work>/base/` (the start commit of each step worktree) and `<work>/spec/` (the step file at that commit).
- For a script step, the driver writes the ledger line itself, because step 04 owns `lib/usage.py`.
