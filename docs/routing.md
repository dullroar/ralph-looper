# Step routing

This document tells how the driver (`ralph-looper` and `ralph-looper.ps1`) selects the executor for each step, and how the driver checks the work of a step. The routing policy (which work goes to which executor) is added by step 05 of the `runner-routing` plan.

## Front matter keys

All keys are optional. Old plans work without changes.

| Key | Values | Meaning |
| --- | --- | --- |
| `agent` | `claude`, `codex`, `copilot`, `local`, `script`, `operator` | The executor for this step. Empty: use `--agent`. |
| `fallback` | an agent name | After one failed attempt with `agent`, the driver uses this agent. The driver also uses it when the `agent` command is not available. |
| `run` | a shell command | Only for `agent: script`. The driver runs it in the step worktree, with the step timeout. |
| `tier` | `standard`, `light` | The model tier. After a failed attempt, the driver uses `standard`. |

## Executor choice

1. The driver uses `agent`. If `agent` is empty, it uses `--agent`.
2. If `fallback` is set and the step had a failed attempt, the driver uses `fallback`.
3. If `fallback` is set and the command of the executor is not available, the driver uses `fallback`.
4. If the command is still not available, the driver does not start the step. It prints `waiting: agent <name> not available`.

The driver exports `RALPH_STEP_AGENT` with the selected executor.

## Executors

| Executor | What the driver does |
| --- | --- |
| `claude`, `codex`, `copilot` | Runs the agent command from `lib/agents.sh` with the prompt `lib/PROMPT.md`. |
| `local` | Runs `LOCAL_AGENT_CMD` if it is set. Else it runs `local-coder-agent` from `PATH`. The operator installs this wrapper. It runs Claude Code against the local model. It gets the same arguments as `claude`, with the same allow and deny lists. |
| `script` | Runs `run`, then the gate. There is no model call. Attempts count as for agents. The ledger line has `agent: script`, zero tokens and zero cost. |
| `operator` | Starts no agent. When the step is ready, the driver runs the gate in a fresh step worktree. If the gate passes, the step is done with the evidence `gate passed <date> (operator step, driver-verified)`. If the gate fails, the step stays `pending`, no attempt is counted, and the driver prints `waiting for operator: <step> (see plans/<plan>/steps/<step>.md)`. |

When no other step can run and an operator step waits, the driver stops with exit code `12`. Do the operator action, then start the driver again.

## Overrides (for tests and new agents)

- `AGENT_CMD` replaces the command of the `--agent` executor.
- `AGENT_CMD_<NAME>` (for example `AGENT_CMD_CODEX`) replaces the command of one named executor.
- `LOCAL_AGENT_CMD` is the command of the `local` executor.

Never put a local path in a tracked file. Set these values in the environment.

## Checks that the driver does itself

1. **Gate from the plan branch.** The driver reads `gate`, `touches`, `agent`, `fallback` and `run` from the step file at the plan commit from which the step worktree started. It never reads them from the step worktree after the agent ran.
2. **Front matter integrity.** After the agent ran, the driver compares these five keys in the step worktree with the plan-branch values. If one changed, the attempt fails with `result: <step> changed its own gate or scope`.
3. **Gate.** The driver runs the gate in the step worktree.
4. **Touches enforcement.** The driver lists all changed paths: commits since the start commit, staged and unstaged changes, and untracked files. Each path must match a `touches` entry (the glob rules of `scripts/check_plan.py`), or be the step file, or be a generated index file (`memory/AGENTS.md`, `plans/AGENTS.md`, `scripts/AGENTS.md`). Otherwise the attempt fails, and the driver lists the paths. The driver stages only the allowed paths. It does not use `git add -A` without paths.

A merged step can add new step files to its plan. Put the new files in `touches` (for example `plans/<plan>/steps/*.md`). The next loop picks them up.

## Capabilities

`ralph-looper --capabilities` (or `ralph-looper.ps1 -Capabilities`) prints one word on each line and exits 0:

```text
step-agent
operator-step
script-step
local-agent
gate-from-plan-branch
touches-enforced
```

Later plans check these words before they start.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | All steps are done. |
| 3 | Another loop runs for this plan. |
| 10 | Stopped early (pause, stop, iteration budget or cost cap). |
| 11 | Blocked, or no step can run. |
| 12 | Waiting for operator. |
| 75 | Usage limit (handoff). |
