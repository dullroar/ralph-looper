---
id: 24-review-translation-adopt
status: pending
depends_on: [23-run-translation-adopt]
touches:
  - plans/controls-rollout/lessons/translation-adopt.md
  - plans/controls-rollout/steps/24-review-translation-adopt.md
lane: none
gate: python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave translation-adopt && for h in '## Keep' '## Change' '## Library defects' '## Route evidence'; do grep -qx "$h" plans/controls-rollout/lessons/translation-adopt.md || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Review the `translation-adopt` wave and write its lessons

The gate checks the recorded results with `lib/fanout.py verify`. This step adds the judgment that a script cannot make.

Check that t08 reproduced the t01 baseline. Check that no translated content, PO file, locked code or book build file changed (`git diff --stat <base>..plan/adopt-ralph` lists only the paths in the child's `touches`). Check that `loop/STOP` and the queue history are still there. Check that the batch tool tests run offline and that `submit` refuses without a key and a USD cap. Check that the routing map covers every task kind and quotes measurements.

Do not change any target repository. Read the child branches with Git plumbing only (`git -C "$REPOS_ROOT/<repo>" show plan/<child_plan>:<path>`).

Write `lessons/translation-adopt.md` with exactly these four headings, in this order:

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
