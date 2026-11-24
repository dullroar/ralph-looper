---
id: 31-seed-translation-work
status: done
depends_on: [25-publish-translation-adopt, 30-record-pack-pin]
touches:
  - plans/controls-rollout/seeds/translation-work/**
  - plans/controls-rollout/steps/31-seed-translation-work.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-work && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-24T03:39:10Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Write the seed for the `translation-work` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-work.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-work/` as [waves/translation-work.tsv](../waves/translation-work.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

This is the most important seed of the program. Read `translation/routing.md`, `review/CHECKPOINT-part3.md`, `translation/part3/spanish-adoption-plan-draft.md` and sections 7 to 9, 11.9 and 12 of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md` in the translation repository at its working branch (read only). Apply all lessons files. Use the `v0.2.0` pin for step x01.

Give every step its executor from the spec and the routing map. Give each operator step exact instructions and a gate that checks the outside result. Give each batch step a USD cap placeholder that Jim must set, and make the gate fail while the placeholder is there. Make the lanes independent as the spec says, so that `--jobs 4` runs them together.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

Differences from the child spec, and why. The seed has 28 steps (spec: 27 plus the generated `fix-*`).

- **Added step `g02-lane-requests`** (cloud agent). `tools/batch.py build` takes only rows with `segment_id` and `english_masked`. It has no input for reviewer requests, and the spec names none. `g02` writes `tools/jury_requests.py` (one request for each lens and packet, and the reply-to-inbox conversion) and `tools/humor_ingest.py`. `g01` keeps the three tools of the spec. `j02` depends on `g02`. `h01` and `h02` depend on `g02` because their gates use `humor_ingest.py`.
- **Packets are built in `.probe/`, not in `review/`.** The packets and the canary key are untracked, and a step worktree has only tracked files. `gatelib.py packets build` builds twice, checks that both digests are equal and that there is no `LEAK:` line, and records the digest. Later steps rebuild and compare. Outside jurors and the operator build the same packets in the main checkout and run `packets verify`.
- **Inbox files are tracked.** `j03` and `j04` commit the replies (`review/inbox/batch-*`, `outside-*`), so that gates can read them.
- **`j09` depends also on `h02`, and waits for the `fix-*` steps through its gate** (`fix_steps.py --all-done`). Generated steps cannot be listed in `depends_on`, and no second step may edit `j09` (the generators `j08` and `h02` could run together).
- **`j06` uses `agent: codex`.** The routing map says the adjudicator uses a model different from the translator (`claude-sonnet-5-5`). The cloud-agent default is the same model. If Codex is not available, the operator amends the step. A fallback to the default agent would break the rule.
- **`j10` uses `verify.py --release --no-gates`; `r01` runs the full `--release`.** `verify.py --release` runs every tool test. The baseline has 15 known failures in a worktree, so `r01` can fail for host reasons. The step text says what to do. No gate is weakened.
- **The cookbook file is `translation/cookbook.md`** (new). The repository has no cookbook file. The text is section 12 of the synthesized plan.
- **`u04` changes only `translation/source.json`.** `loop/CONFIG.yaml` also holds `english_commit`. The tools read the commit with `git ls-tree`, so the clone needs the object, not a new HEAD. The pin bump of `CONFIG.yaml`, `loop/STATE.md` and the manifest is task A6, planned in `u05`.
- **Gate helper.** `plans/v4-es-1/gatelib.py` (in the seed, in no `touches`) holds the shared checks: the USD cap (fails while the placeholder is there, and above 100), required record keys, `loop/STOP` in the main checkout, no tracked private file, the baseline-aware tool tests, and the use of the repository `.venv` (the `-I` flag hides it, which made `verify.py --fast` fail in `t06`). I could not run `gatelib.py` here (the shell denied it). Only `py_compile` and `fanout.py ready` ran. The first child step that calls a command must show that it works.
- **Lessons applied.** Baseline gate (`translation-adopt`), `.probe/` for scratch (`pilot`, `translation-adopt`), `loop/STOP` and private files checked in the main checkout, no runner calls from agents, three-denial rule in the goal, `touches` names every tool that must change, the pack comparison with the local tools is step `x01` (`translation-pack`), tests named in the step run with the full suite (`controls`), the `v0.2.0` pin in `goal.md` and `x01`.
- **Not done:** I did not read the whole of sections 7 to 9 for details that only a tool step needs. `g01` and `g02` read the sources themselves. I did not test the generated steps: the plan has no step `fix-*` until `j08` runs.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
