---
id: 20-review-fleet
status: pending
depends_on: [19-run-fleet]
touches:
  - plans/controls-rollout/lessons/fleet.md
  - plans/controls-rollout/steps/20-review-fleet.md
lane: none
gate: python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave fleet && for h in '## Keep' '## Change' '## Library defects' '## Route evidence'; do grep -qx "$h" plans/controls-rollout/lessons/fleet.md || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Review the `fleet` wave and write its lessons

The gate checks the recorded results with `lib/fanout.py verify`. This step adds the judgment that a script cannot make.

Do the pilot review checks for each of the eight repositories. For `compliance_poc`, confirm that `claude.yml` and `claude-code-review.yml` did not change and that the controls job has no secrets.

Do not change any target repository. Read the child branches with Git plumbing only (`git -C "$REPOS_ROOT/<repo>" show plan/<child_plan>:<path>`).

Write `lessons/fleet.md` with exactly these four headings, in this order:

- `## Keep`: what worked and must stay in later seeds.
- `## Change`: rules that later seeds must apply. Write each as an instruction.
- `## Library defects`: defects in `deterministic-controls`, with the probe that shows each. Write `none` if there are none. A defect here blocks the next seed step until a patch release is pinned (the operator releases it and runs `pin.sh`).
- `## Route evidence`: run `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md` for this wave. Copy the rows (no paths). Say which executors passed on the first attempt and which needed their fallback.

## Results

Record for each target: the final plan commit, the gate results with counts, and the UTC date.

(fill in)

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
