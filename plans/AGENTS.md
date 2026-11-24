# Plans index

<!-- IMMUTABLE HEADER: do not edit the text above the BEGIN marker. -->

This folder holds the plans for agents. Humans read `docs/` instead.

- One plan is one folder: `plans/<plan-name>/`. Copy `for-each-plan/` to start a plan.
- `goal.md` holds the goal and the Ralph loop prompt. `plan.md` holds the high-level plan. `steps/` holds one file for each step.
- A step is small. A small model or agent can implement, test and verify it alone.
- Run a plan in its own Git worktree, on its own branch. Never work on `main`.
- Steps that run at the same time must not touch the same files (see `touches` in the step front matter).
- A plan must survive a stop at any time. Another agent must be able to continue from the files in the repository. Record status and evidence in the step files.
- Runtime output goes outside the repository, in `~/repo-work/<repo>/<plan>/`. Never track it.
- Never put PII, secrets or personal paths in a plan.
- Write in Simplified Technical English (ASD-STE100).
- This file is generated. Run `python3 scripts/build_indexes.py` after any change. Do not edit the list below by hand.

Read the list. Open only the plans whose "Read me when" line matches your task.

<!-- BEGIN GENERATED INDEX -->

* [controls-rollout/plan.md](./controls-rollout/plan.md)
  Read me when: you want to build, release or adopt the deterministic-controls library, roll it out to the template, the runner and the ten repositories, or move the Spanish translation repository onto Ralph with routed and batch work.
* [runner-adopts-controls/plan.md](./runner-adopts-controls/plan.md)
  Read me when: you add or change the deterministic-controls adoption of ralph-looper itself (pin, controls.toml, the controls and runner-tests jobs), or archive the controls-rollout plans.
* [runner-routing/plan.md](./runner-routing/plan.md)
  Read me when: you want to add per-step executor routing, operator and script steps, gate and touches enforcement, the fan-out tool or the route report to ralph-looper.

<!-- END GENERATED INDEX -->
