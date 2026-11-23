# ralph-looper

Runs the steps of a plan with a coding agent. It stops and restarts safely, and it works with more than one agent.

- **Restartable.** Kill it at any time (crash, no token budget). Run it again. It continues. You can change the agent between runs.
- **Parallel.** Each step runs in its own Git worktree and branch. `--jobs N` runs steps at the same time when `depends_on` and `touches` allow it.
- **Agent agnostic.** `claude`, `codex`, `copilot` and `local` work. Set `AGENT_CMD` to use any other command.
- **Honest verification.** The driver runs the `gate` command of each step. It does not trust the agent.
- **Usage report.** After each step, `driver.out` has a usage block: model (requested and reported), effort, time, tokens, cost. It never has the prompt. The same data goes to `ledger.jsonl`.
- **Nothing extra in your repository.** Logs, ledger, locks and worktrees are in `~/repo-work/<repo>/<plan>/` (`%USERPROFILE%\repo-work\...` on Windows). Set `RALPH_WORK` to change the base directory.

## Use

```bash
ralph-looper --repo ~/repos/my-repo --plan my-plan --agent claude --jobs 2
ralph-looper --repo ~/repos/my-repo --plan my-plan --status
ralph-looper --repo ~/repos/my-repo --plan my-plan --pause    # and --resume
```

A plan follows [repo-template](https://github.com/dullroar/repo-template): `plans/<plan>/goal.md`, `plan.md`, `steps/*.md`. The plan must be committed on the branch you run from. The loop makes the branch `plan/<plan>` and merges finished steps into it. You merge that branch yourself.

Optional `plans/<plan>/loop.yaml` (flat `key: value` lines): `jobs`, `max_attempts`, `step_timeout_minutes`, `gate_timeout_minutes`, `max_usd`, `max_step_usd`, and `<agent>_model_<standard|light>`, `<agent>_effort_<standard|light>`. A step can set `tier: light` in its front matter.

Exit codes: 0 all done, 3 already running, 10 stopped early, 11 blocked, 12 waiting for an operator step, 75 usage limit (with `--on-limit handoff`; run again with another agent).

## Step routing

A step can choose its executor in its front matter. All keys are optional.

- `agent`: `claude`, `codex`, `copilot`, `local`, `script` or `operator`. Empty means the `--agent` value.
- `fallback`: an agent that the driver uses after one failed attempt, or when the `agent` command is not available.
- `run`: the command of a `script` step. The driver runs it in the step worktree, with no model, and then runs the gate.
- `agent: operator`: a human action. The driver starts no agent. It runs the gate. If the gate fails, the step stays `pending` and the driver stops with exit code 12 when nothing else can run. Do the action, then start the driver again.
- `agent: local`: runs `LOCAL_AGENT_CMD`, or `local-coder-agent` from `PATH`. The operator installs this wrapper.

The driver reads `gate`, `touches`, `agent`, `fallback` and `run` from the plan branch. It rejects a step that changes them, and a step that changes files outside `touches`.

`ralph-looper --capabilities` prints the features of the driver, one on each line: `step-agent`, `operator-step`, `script-step`, `local-agent`, `gate-from-plan-branch`, `touches-enforced`. See [docs/routing.md](docs/routing.md) for the details and the routing policy.

## Tools

- `lib/fanout.py`: runs a wave of child plans in other repositories (`ready`, `provision`, `run`, `status`, `verify`, `published`). The operator runs it. See [docs/fanout.md](docs/fanout.md).
- `lib/report.py`: summarizes `ledger.jsonl` by agent, route and model (cost, time, tokens, first-attempt gate pass rate). Run `python3 lib/report.py`. Use it to decide which work a `local` model can do.

## Secrets

No secret may be tracked, committed or pushed. `scripts/secret_guard.py` finds tokens, passwords, private keys and forbidden files. It uses no model and no network. Its output never shows a full secret.

Modes: `--staged` (pre-commit), `--range A..B` and `--new-ref SHA` (pre-push), `--tracked` (all tracked files), `--history` (all history), `--paths FILE...`. Exit code 0 is clean, 1 is findings, 2 is an error.

The guard runs in four places: the pre-commit and pre-push hooks, the driver before each merge, and CI.

Run this in every clone. Hooks are local and Git does not clone them:

```bash
bash scripts/install_hooks.sh
```

Exceptions are rare. An exception needs the owner's review. Do not add one to make a step pass.

- Inline: put `secret-guard: allow <reason>` on the line. The reason is required.
- File: `.secret-guard-allow` has one line for each exception: `<fingerprint>  <path>  <reason>`. Each finding prints its fingerprint.

## Windows (PowerShell 7)

`ralph-looper.ps1` and `ralph-pusher.ps1` have the same behavior and the same work directory layout (`%USERPROFILE%\repo-work`). Parameters are PowerShell style: `-Repo`, `-Plan`, `-Agent`, `-Jobs`, `-Status`, `-Pause`, `-Resume`.
Step gates run with PowerShell by default. For bash gates, set `gate_shell: bash` in `loop.yaml`.
**The PowerShell scripts are not tested yet.** `tests/run-pwsh.sh` runs only when `pwsh` is installed, and it has not run. The test below covers only the bash scripts. Report problems.

## Off-machine backup

Agents and the driver have no credentials and cannot push. Run the pusher yourself, in a second terminal:

```bash
ralph-pusher --repo ~/repos/my-repo --plan my-plan --remote origin   # push every 45 s when branches change
ralph-pusher --repo ~/repos/my-repo --plan my-plan --once            # push now and exit
```

It pushes only `plan/<plan>` and `step/<plan>/*`. It never forces a push and never pushes `main`. After a step merges, it deletes the remote step branch. It does this only when the local branch is gone and the branch tip is already inside `plan/<plan>`, so unmerged work is never deleted. Create `PUSHER-STOP` in the work directory to stop it. The ledger and logs are not pushed (they stay in `~/repo-work`).

## Test

```bash
bash tests/run.sh
```

## Not built yet

A run of the PowerShell test. `tests/run-pwsh.sh` exists, but it runs only where `pwsh` is installed. It has not run yet.

## License

MIT.
