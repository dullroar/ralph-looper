# Goal: shared deterministic controls, routed work, and a parallel translation plan

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `controls-rollout` in the `ralph-looper` repository. Read `AGENTS.md`, then `plans/controls-rollout/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`. The driver checks the gate and `touches` from the plan branch.
> Before a seed step, read every file in `plans/controls-rollout/lessons/` and apply what it says. Before a review step, read the wave manifest and the child spec.
> Run the `gate` command. If it fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, change a GitHub setting or run `lib/fanout.py run`. Operator steps do that.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

Build a small, versioned **deterministic-controls** library. Dogfood it in its own repository first. Then wire it into `repo-template` and `ralph-looper`, pilot it in two of the ten repositories of 2026-11-22, and roll it out to the other eight. In the same program, move the Spanish translation repository (`aprende-a-programar-como-un-bicho-raro`) from its own loop onto the template and Ralph. Give it a Batch API path and a routed, parallel plan for its remaining work. Promote the generic translation checks into the shared library.

Each wave must make the next wave faster or more reliable. Seeds for a wave are written only after the previous wave is reviewed. Each review writes a lessons file that the next seed step must apply.

Design rule: use AI to write and improve deterministic controls. Run those controls independently and unconditionally. Do not let an agent certify its own work.

## Done when

- `deterministic-controls` has releases `v0.1.0` (core checks and adoption tools) and `v0.2.0` (translation and Markdown pack). Its own CI runs its own checks at the pinned revision.
- `repo-template`, `ralph-looper`, the ten repositories and the translation repository pin a release, run the controls in CI and keep their existing commands, tests and Docker gates. Each has an adoption receipt.
- Each repository has a recorded enforcement state: `required` with passing bypass probes, or `documented-gap` with the reason.
- The translation repository follows the template layout, has a Batch API tool with offline tests, and has a committed plan `v4-es-1` for its remaining work, with routed and parallel lanes.
- `route-report.md` shows cost and first-pass rate by route for the program. The final audit lists the backlog.

## Out of scope

- Running the translation plan `v4-es-1`. This plan only writes, validates and publishes it. Jim starts it.
- Language and toolchain packs, the AI-generated control lifecycle and fleet operations (phases 12, 13 and 16 of the source plan). The final audit puts them in the backlog with the measurements that this program produces.
- A scheduler, a database, a service, a dashboard or a new policy language.
- Any repository that is not in a wave manifest.
