# Step routing

This document tells how the driver (`ralph-looper` and `ralph-looper.ps1`) selects the executor for each step, and how the driver checks the work of a step. The routing policy (which work goes to which executor) is in the last part of this document, for plan authors.

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

## Routing policy for plan authors

Send each piece of work to the cheapest executor that can do it. The gate decides if the work is done. The route does not change what the gate must prove.

| Work | Route |
| --- | --- |
| Checks, builds, index generation, imports, measurements | `script` step or CI job. No model. |
| Bounded, well-specified edits with a strong gate (ports, fixtures, doc moves) | `local`, with `fallback` to a cloud agent |
| Design, tricky parsers, migrations, adjudication, review | `claude` or `codex` (standard tier) |
| Small checks of recorded results | cloud agent, `tier: light` |
| Many independent text transformations | Batch API tool, run by the operator |
| Approvals, publication, settings, credentials, native-speaker review | `operator` step |
| Merge decision | CI required checks and the protected branch |

### Rules

- Prefer `script` when the work is deterministic. A model must not do what a script can do.
- Use `local` only for bounded work with a strong gate. Always give a `fallback`. Use the route report (`python3 lib/report.py`) to decide where `local` is good enough.
- The merge decision belongs to CI and the protected branch, not to the driver.

### `script`

- **Use it when:** a command gives the same result each time (checks, builds, index generation, imports, measurements).
- **The gate must prove:** the output is correct, not only that the command exited with 0. Check the files or records that the command wrote.
- **Cost and trust:** zero tokens and zero cost. The command is part of the plan, so review it like code. It runs with the step timeout and cannot change files outside `touches`.
- **Fallback:** none. A failed script is a fault in the script or the input. Fix it. A model does not replace it.

### `local`

- **Use it when:** the work is bounded and well specified, and a strong gate can find a wrong result (ports, fixtures, doc moves).
- **The gate must prove:** the full intended result. A local model can write work that looks right and is wrong. Do not use `local` where the gate is weak.
- **Cost and trust:** no cloud cost. Quality is lower than for cloud agents. The operator installs and maintains the adapter.
- **Fallback:** always set `fallback` to a cloud agent. After one failed attempt, the driver uses it.

### `claude`, `codex`, `copilot` (standard tier)

- **Use it when:** the work needs design, tricky parsing, migration, adjudication or review.
- **The gate must prove:** the behavior, with tests. A review step needs a recorded result that the gate can check.
- **Cost and trust:** the highest cost. Set `max_step_usd` and `max_usd` in `loop.yaml`. Agents have no credentials and cannot push.
- **Fallback:** another cloud agent, if the first has no budget. Use `--on-limit handoff`.

### Cloud agent with `tier: light`

- **Use it when:** the work is a small check of recorded results.
- **The gate must prove:** the same as for the standard tier.
- **Cost and trust:** lower cost. After a failed attempt, the driver uses the standard tier.
- **Fallback:** the standard tier, automatically.

### Batch API work

Batch API work is a plan-level tool in the repository that needs it. It is not a driver feature.

- **Use it when:** there are many independent text transformations (translation drafts, reviewer passes).
- **Who runs it:** the operator submits and collects the batch with an API key in the operator shell only. No agent and no driver process holds the key.
- **Import:** a `script` step imports the result into the repository. The normal gates validate it.
- **The gate must prove:** each result has the right format, is complete, and has no secret.
- **Fallback:** run the work again as agent steps, or ask the operator to submit the batch again.

### `operator`

- **Use it for:** approvals, publication, settings changes, credentials and work for named humans (for example native-speaker review).
- **The gate must prove:** the result of the human action, in a file or record that the gate can check. The driver runs the gate. It does not take the word of anyone.
- **Cost and trust:** no model cost. The loop stops with exit code `12` until the operator acts. Agents never get bypass rights. An agent must not do the action for the operator.
- **Fallback:** none. Wait for the operator.
