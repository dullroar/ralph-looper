---
id: 14-seed-pilot
status: done
depends_on: [09-runner-adopts-controls, 13-publish-template]
touches:
  - plans/controls-rollout/seeds/pilot/**
  - plans/controls-rollout/steps/14-seed-pilot.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave pilot && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave pilot && python3 scripts/check_context.py && git diff --check; result: both targets ready (5 pending steps each), all checks ok, no diff errors; 2026-11-24 (UTC)"
---

# Write the seed for the `pilot` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/adopt-controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/pilot/` as [waves/pilot.tsv](../waves/pilot.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Write one seed for each pilot repository. Copy each repository brief from the archived ralphify `targets.md`. Use a cloud agent for a02 (no `local`) in the pilot.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

The seeds are in `seeds/pilot/metadata_driven_gx/` and `seeds/pilot/duckdb-fs/`. They pin `v0.1.1` (commit `0323de27...`). Both seeds use a cloud agent for a00, a02, a03 and a04. a01 is a `script` step. No step uses `local`.

Differences from the child spec, and the reason for each:

- **Added step `a00-secret-guard`.** The child contract and the owner decision `secret_guard` need the guard in the first adoption commit. The spec had only a01 to a04. `a01` now depends on `a00`. The guard files come from `reference/` in each seed (a copy of the template seed).
- **Added `spec.md` and the `requirements` key.** Both targets have the older plan checker (`scripts/check_plan.py`). It needs `spec.md`, headings `### R1` and so on, and `requirements` in each step. The checker failed without them.
- **a01 uses `PYTHONPATH`, not a virtual environment.** The contract and the `template` lessons forbid installs in agent sessions. The operator must put the pinned release on `PYTHONPATH` and run the shim once for the pinned commit before the wave (`fanout.py run --child-env PYTHONPATH`).
- **a02 touches more files.** It adds `plans/AGENTS.md` (the new plan changes the generated index), `docs/README.md` and `Dockerfile`. The Docker runs use `--network none` and call `scripts/check_context.py` (now the shim). The shim needs the network once. So the image build must prepare the cache. The images also lack `git` (needed by the guard test and the shim) and, for `duckdb-fs`, `python3-venv`. The a02 gate runs `bash scripts/test_docker.sh`.
- **The Docker gate in `targets.md` is older than the repository.** For `metadata_driven_gx` the brief says `python end_to_end.py ...`. The repository gate is `scripts/test_docker.sh`, which runs `python3 scripts/check_context.py && python tests/check_demo_weather.py`. The seed copies the brief and states the real command. For `duckdb-fs` the brief matches the script. Both seeds say to keep the command unchanged.
- **a04 gate** clones `HEAD` and runs the checks and the Docker gate in the clone. It needs the token `history-findings=<count>` in the step file. The a04 `touches` is the step file only, as in the spec.
- **Lessons applied.** `--commit` is in the `adopt plan` text. The agent writes `docs/controls-adoption.md` by hand. The `Run me when:` line is added to the requirements file if missing. The old `check` job (and `docker` job) stay. The routing sentence is in `AGENTS.md`. The `touches` lists include files that earlier steps change. The agent runs the full tests. The `first_pass_rate` column is not used.

Operator notes for step 15: run the shim once on the host before the wave, so that the cache for the pinned commit exists. Put the pinned release on `PYTHONPATH` and pass `--child-env PYTHONPATH`. The `duckdb-fs` gates need Docker and `/dev/fuse`. Both children need Docker.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
