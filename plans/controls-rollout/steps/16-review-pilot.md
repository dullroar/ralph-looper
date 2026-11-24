---
id: 16-review-pilot
status: done
depends_on: [15-run-pilot]
touches:
  - plans/controls-rollout/lessons/pilot.md
  - plans/controls-rollout/steps/16-review-pilot.md
lane: none
gate: python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave pilot && for h in '## Keep' '## Change' '## Library defects' '## Route evidence'; do grep -qx "$h" plans/controls-rollout/lessons/pilot.md || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate passed 2026-11-24: fanout verify 2/2, four headings present in lessons/pilot.md, check_context.py ok, git diff --check clean"
---

# Review the `pilot` wave and write its lessons

The gate checks the recorded results with `lib/fanout.py verify`. This step adds the judgment that a script cannot make.

For each pilot: compare the controls findings in the child's CI-equivalent run with the local run (same commit, same pin: they must be equal); check that every probe of a03 failed for the expected rule ID; check the rollback record; check that the Docker gate and the existing `context` job still pass. Separate true defects in the repository from library defects and from noisy checks. A noisy check stays advisory and is listed under `## Change`.

Do not change any target repository. Read the child branches with Git plumbing only (`git -C "$REPOS_ROOT/<repo>" show plan/<child_plan>:<path>`).

Write `lessons/pilot.md` with exactly these four headings, in this order:

- `## Keep`: what worked and must stay in later seeds.
- `## Change`: rules that later seeds must apply. Write each as an instruction.
- `## Library defects`: defects in `deterministic-controls`, with the probe that shows each. Write `none` if there are none. A defect here blocks the next seed step until a patch release is pinned (the operator releases it and runs `pin.sh`).
- `## Route evidence`: run `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md` for this wave. Copy the rows (no paths). Say which executors passed on the first attempt and which needed their fallback.

## Results

Record for each target: the final plan commit, the gate results with counts, and the UTC date.

- `metadata_driven_gx`: final plan commit `ff0ef1e7bfca4b61a92e9583f9329cf3d1ef7432`. `verify`: verified done. 2026-11-24 (UTC).
- `duckdb-fs`: final plan commit `bd785ee38c767fab5bfb871a5ad28a45669df5cd`. `verify`: verified done. 2026-11-24 (UTC).
- `verify: 2/2 targets pass`. Probe and rollback details are in `lessons/pilot.md`.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
