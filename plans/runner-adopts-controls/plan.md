---
gist: "Read me when: you add or change the deterministic-controls adoption of ralph-looper itself (pin, controls.toml, the controls and runner-tests jobs), or archive the controls-rollout plans."
---

# Plan: ralph-looper adopts the deterministic controls

The source is item B1 of `plans/controls-rollout/final-audit.md`. The method is the one that the fleet used (`plans/controls-rollout/lessons/fleet.md`): apply, probe, publish.

| Step | Executor | What |
| --- | --- | --- |
| `r01-adopt` | agent | `adopt apply` with the pinned library, the `runner-tests` job, the rule in `AGENTS.md`, the adoption record. |
| `r02-probes` | agent | Planted defects in a `.probe/` copy fail with the expected rule IDs. |
| `r03-publish` | operator | Pull request, merge, required checks in the ruleset. |
| `r04-archive` | operator | Move the finished plans to `plans/archive/` in a separate pull request. |

## Limits

- Agents cannot install packages or reach the network. The operator puts the pinned library on `PYTHONPATH` (a checkout of the tag) before the driver starts. The shim then uses it. CI installs the pin from GitHub.
- `adopt apply` rewrites `scripts/install_hooks.sh` (library defect B6). Restore the file from the base commit after `adopt apply`.
- Step 09 of `controls-rollout` stays as it is. It is part of the history. This plan is the correction.
