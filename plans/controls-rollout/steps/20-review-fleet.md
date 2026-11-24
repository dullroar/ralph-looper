---
id: 20-review-fleet
status: done
depends_on: [19-run-fleet]
touches:
  - plans/controls-rollout/lessons/fleet.md
  - plans/controls-rollout/steps/20-review-fleet.md
lane: none
gate: python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave fleet && for h in '## Keep' '## Change' '## Library defects' '## Route evidence'; do grep -qx "$h" plans/controls-rollout/lessons/fleet.md || exit 1; done && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-24T15:18:45Z"
evidence: gate passed 2026-11-24 (driver-verified)
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

Date (UTC): 2026-11-24. `fanout.py verify --wave fleet`: `verify: 8/8 targets pass`. The final plan commits and the review notes are in `lessons/fleet.md`.

| Target | Final plan commit | Gate result |
| --- | --- | --- |
| `compliance_poc` | `c733c6a59f4a5993a17760a15c8746a83c15648b` | verified done (5 steps) |
| `ffmpeg_mcp` | `2552b7c22e3eedbc08a7c60fa8c3ebdd7ab2b75a` | verified done (5 steps) |
| `gpx_parser` | `b65c1bb1180f35dfe1cd0606472fa04c236b04ea` | verified done (5 steps) |
| `lmdb-fs` | `0004e414f71017823879f70c5e73e2d46dbba641` | verified done (5 steps) |
| `metadata_mcp` | `8d9b048f4557af4988bc17b0124898798c69eb11` | verified done (5 steps) |
| `pandoc_mcp` | `1180a94dadf6efdd0d7660efaa532b8b92e75a66` | verified done (5 steps) |
| `sample_parse` | `ba322dd2c27b103094db13725e6cc110a0d047f6` | verified done (5 steps) |
| `vips_mcp` | `0993374021f7d57b586fbe1f76f9630c07dc56d7` | verified done (5 steps) |

`compliance_poc`: `claude.yml` and `claude-code-review.yml` are unchanged (same blob IDs as `master`). The `controls` job has no secrets.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
