---
gist: "Read me when: you want to add per-step executor routing, operator and script steps, gate and touches enforcement, the fan-out tool or the route report to ralph-looper."
---

# Plan: upgrade the runner for routed, multi-repository plans

This file is the high-level plan. The detail is in `steps/`.

## Approach

The source is the attached deterministic-controls plan of 2026-11-23, phases 0, 6, 14 and 15. This plan does only the runner part. The [controls rollout](../controls-rollout/plan.md) does the rest and depends on this plan.

Each step makes the next work faster or more reliable:

1. **Baseline first.** Record what works now in the 13 repositories before anything changes. Build `scripts/check_records.py` so that later gates can check TSV records without ad-hoc code.
2. **One fan-out tool.** The [ralphify launcher](../archive/ralphify-repositories/rollout.py) and the [MCP fan-out](../archive/sharpen-mcp-suite/fanout.py) solved the same problem twice. Combine them into `lib/fanout.py` with tests. Every wave in the controls rollout uses it.
3. **Per-step routing.** A step names its executor in front matter (`agent:`). The value `operator` means a human action whose gate the driver checks. The value `script` means a deterministic `run:` command with no model. The value `local` means the local model adapter. With this, a plan sends each piece of work to the cheapest executor that can do it. The gate still decides.
4. **Close two trust gaps.** Now the driver reads the gate from the step file after the agent ran, so an agent can edit its own gate. The driver also commits all changes with `git add -A`. Make the driver read `gate`, `touches`, `agent` and `run` from the plan branch, and reject changes outside `touches`.
5. **Guard secrets everywhere.** No secret may be tracked, committed or pushed. The current scanner reads only context Markdown. Build `scripts/secret_guard.py` (all files, staged blobs, push ranges, history) with hooks, a CI job and a driver check before each merge. No model, no network.
6. **Measure the routes.** Add the route to the ledger and build `lib/report.py`. Later routing decisions use these measurements, not guesses.

The routing policy (which work goes where) is in `docs/routing.md` (written by `runner-routing`) after step 05. In summary:

| Work | Route |
| --- | --- |
| Checks, builds, index generation, imports, measurements | `script` step or CI job. No model. |
| Bounded, well-specified edits with a strong gate (ports, fixtures, doc moves) | `local`, with `fallback` to a cloud agent |
| Design, tricky parsers, migrations, adjudication, review | `claude` (standard tier). `codex` only by explicit owner choice. |
| Small checks of recorded results | cloud agent, `tier: light` |
| Many independent text transformations (translation drafts, reviewer passes) | Batch API tool, submitted by the operator. Its output goes through a `script` import and the normal gates. |
| Approvals, publication, settings, credentials, native-speaker review | `operator` step |
| Merge decision | CI required checks and the protected branch |

## Steps

| Step | Goal | Depends on |
| --- | --- | --- |
| [01-baseline-records](./steps/01-baseline-records.md) | Build `check_records.py` and record the 13-repository baseline. | none |
| [02-fanout-tool](./steps/02-fanout-tool.md) | Combine the two launchers into a tested `lib/fanout.py`. | none |
| [03-step-routing](./steps/03-step-routing.md) | Add per-step executors and close the gate and touches gaps, in bash and PowerShell. | none |
| [07-secret-guard](./steps/07-secret-guard.md) | Build the secret guard, its hooks and its CI job. Audit all history. | 01 |
| [04-route-report](./steps/04-route-report.md) | Record the route in the ledger, build `lib/report.py`, and run the secret guard before each merge. | 03, 07 |
| [05-docs](./steps/05-docs.md) | Write the routing policy and update the README and the agent contract. | 01, 02, 04, 07 |
| [06-verify](./steps/06-verify.md) | Run all tests from a clean clone and record the evidence. | 05 |

## Run it

Use the current driver from a checkout of `main` that contains this plan. Export `RALPH_WORK` (outside all repositories) and `REPOS_ROOT` (the parent directory of the repository checkouts). Step 01 reads the other repositories under `REPOS_ROOT`.

```bash
export RALPH_WORK REPOS_ROOT
"$RALPH_REPO/ralph-looper" --repo "$RALPH_REPO" --plan runner-routing \
  --agent "$RALPH_AGENT" --jobs 3 --on-limit handoff
```

The current driver does not know `agent:` in front matter. No step in this plan uses it. When the plan is done, review `plan/runner-routing` and merge it into `main` through a pull request. Then run `bash scripts/install_hooks.sh` in every clone under `REPOS_ROOT` (hooks are local and are not cloned). Then start the controls rollout from `main`.

## Parallelism

Steps 01, 02 and 03 run at the same time. Their `touches` do not overlap. Step 07 starts when 01 is done, because both change `scripts/AGENTS.md`. It runs while 02 and 03 run. Step 03 is the largest. It owns the driver files. Step 04 waits for 03 because it changes the same driver call to `lib/usage.py`. Step 05 owns `README.md`, `docs/README.md` and `AGENTS.md`, so no earlier step changes them.

## Risks

- **The PowerShell driver is not tested.** `pwsh` is not installed on the planning host. Step 03 changes both drivers. It adds a PowerShell test that runs only when `pwsh` is present. Record "PowerShell not executed" when it is absent. Do not claim parity from reading the code.
- **The driver changes the driver.** Steps run on the old driver, and their gates test the new driver in the step worktree. The old driver merges them. The new behavior applies only from the next driver start.
- **Touches enforcement can block a valid step.** The driver itself writes the step file and the generated indexes. Step 03 allows the step's own file always and lists the generated index files. Other files need to be in `touches`.
- **A local model can produce plausible but wrong work.** The gate decides. After one failed attempt, `fallback` sends the step to a cloud agent.
