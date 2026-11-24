# Goal: finish the Spanish edition `v4-es.1` on the Ralph runner

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `v4-es-1` in this repository. Read `AGENTS.md`, then `plans/v4-es-1/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the `gate` command. If it fails, find the cause and fix it. Do not weaken or delete the gate. Before you commit, run the full tool suite as the gate does: `python3 plans/v4-es-1/gatelib.py tests`.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess. If one command is denied three times, stop and write it under "Resume notes". Do not retry a fourth time.
> Never push, publish, tag, change a remote or change a GitHub setting. Never run `ralph-pusher`. Never run `loop/ralph.sh`. Never remove `loop/STOP`. Never install packages, create a virtual environment or use the network. Never use a Batch API key.
> Make scratch copies only in `.probe/` inside the worktree, and delete `.probe/` before the gate.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

This repository is the Spanish edition of an English book. The old private loop (`loop/ralph.sh`) is archived and stopped. This plan finishes the edition on the Ralph runner. It does the Jury (phase 7), the release (phase 8), the retrospective and the cookbook rehearsal (phase 9) and the upstream package with the Spanish adoption (Part III). It also enables the translation pack of the controls library in advisory mode. The routing map is `translation/routing.md`.

Library for the controls: `deterministic-controls` `v0.2.0` (the translation pack is in this release). Install line (for the operator and for CI, never for an agent step):

`python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5"`

## Done when

- Gate 7 passes: no unresolved critical or major finding, canary reports filed, humor register decided, all `needs-human` items decided, Jury report committed.
- The upstream package is accepted by the English maintainer and its commit is pinned. The Spanish adoption is planned from the impact report.
- The cookbook rehearsal passes and the run file `translation/runs/v4-es.1.yaml` is written.
- The release gates pass. Jim publishes and tags `v4-es.1`. The release assets have the hashes of the build.
- Every step of this plan is `done` with evidence.

## Out of scope

- The old loop: `loop/ralph.sh` and `loop/STOP` stay as they are. Jim decides about the loop, not this plan.
- Pushing, publishing, tags, remotes and GitHub settings. Required checks and branch protection.
- Contact with the English maintainer and with outside jurors. Jim does that in the operator steps.
- Any real Batch API call by an agent. Only the operator submits a batch.
