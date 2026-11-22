# ralph-looper

Runs the steps of a plan with a coding agent. It stops and restarts safely, and it works with more than one agent.

- **Restartable.** Kill it at any time (crash, no token budget). Run it again. It continues. You can change the agent between runs.
- **Parallel.** Each step runs in its own Git worktree and branch. `--jobs N` runs steps at the same time when `depends_on` and `touches` allow it.
- **Agent agnostic.** `claude`, `codex` and `copilot` work now. `local` models are a later project. Set `AGENT_CMD` to use any other command.
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

Exit codes: 0 all done, 3 already running, 10 stopped early, 11 blocked, 75 usage limit (with `--on-limit handoff`; run again with another agent).

## Windows (PowerShell 7)

`ralph-looper.ps1` and `ralph-pusher.ps1` have the same behavior and the same work directory layout (`%USERPROFILE%\repo-work`). Parameters are PowerShell style: `-Repo`, `-Plan`, `-Agent`, `-Jobs`, `-Status`, `-Pause`, `-Resume`.
Step gates run with PowerShell by default. For bash gates, set `gate_shell: bash` in `loop.yaml`.
**The PowerShell scripts are not tested yet.** The test below covers only the bash scripts. Report problems.

## Off-machine backup

Agents and the driver have no credentials and cannot push. Run the pusher yourself, in a second terminal:

```bash
ralph-pusher --repo ~/repos/my-repo --plan my-plan --remote origin   # push every 45 s when branches change
ralph-pusher --repo ~/repos/my-repo --plan my-plan --once            # push now and exit
```

It pushes only `plan/<plan>` and `step/<plan>/*`. It never forces a push and never pushes `main`. Create `PUSHER-STOP` in the work directory to stop it. The ledger and logs are not pushed (they stay in `~/repo-work`). Remote step branches are not deleted after the merge; delete them yourself.

## Test

```bash
bash tests/run.sh
```

## Not built yet

Local-model agent adapter, a model/cost report from `ledger.jsonl`, a test for the PowerShell scripts.

## License

MIT.
