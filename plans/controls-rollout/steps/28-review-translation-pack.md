---
id: 28-review-translation-pack
status: done
depends_on: [27-run-translation-pack]
touches:
  - plans/controls-rollout/lessons/translation-pack.md
  - plans/controls-rollout/steps/28-review-translation-pack.md
lane: none
gate: python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave translation-pack && for h in '## Keep' '## Change' '## Library defects' '## Route evidence'; do grep -qx "$h" plans/controls-rollout/lessons/translation-pack.md || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate command of this step passed 2026-11-23 (verify 1/1, four headings, check_context, diff --check)"
---

# Review the `translation-pack` wave and write its lessons

The gate checks the recorded results with `lib/fanout.py verify`. This step adds the judgment that a script cannot make.

Check that each check agrees with the matching translation tool on the translation repository, or that each difference is explained. Check that the pack is opt-in: a repository without a translation manifest passes. Run `bash scripts/release_check.sh` in a temporary clone of `plan/translation-pack`.

Do not change any target repository. Read the child branches with Git plumbing only (`git -C "$REPOS_ROOT/<repo>" show plan/<child_plan>:<path>`).

Write `lessons/translation-pack.md` with exactly these four headings, in this order:

- `## Keep`: what worked and must stay in later seeds.
- `## Change`: rules that later seeds must apply. Write each as an instruction.
- `## Library defects`: defects in `deterministic-controls`, with the probe that shows each. Write `none` if there are none. A defect here blocks the next seed step until a patch release is pinned (the operator releases it and runs `pin.sh`).
- `## Route evidence`: run `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md` for this wave. Copy the rows (no paths). Say which executors passed on the first attempt and which needed their fallback.

## Results

Record for each target: the final plan commit, the gate results with counts, and the UTC date.

- Target `deterministic-controls`, final plan commit `0620d2c8f59de75ae21b87677f9046183f383657`.
- `fanout.py verify`: `verified done`, 1/1 targets pass.
- `release_check.sh` in a clone of `plan/translation-pack`: 369 tests passed, self check passed (7 checks), wheel `0.2.0` built.
- Date: 2026-11-23 (UTC).
- Open: the comparison with the local translation tools was not done. See the lessons file.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
