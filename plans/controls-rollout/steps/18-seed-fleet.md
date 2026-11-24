---
id: 18-seed-fleet
status: done
depends_on: [17-publish-pilot]
touches:
  - plans/controls-rollout/seeds/fleet/**
  - plans/controls-rollout/steps/18-seed-fleet.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave fleet && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate (fanout.py ready --wave fleet, check_context.py, git diff --check): 8/8 targets ready, each seed passes the target plan checker, context checks ok, 2026-11-23 (UTC)"
---

# Write the seed for the `fleet` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/adopt-controls.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/fleet/` as [waves/fleet.tsv](../waves/fleet.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Write one seed for each of the eight fleet repositories. Apply `lessons/pilot.md`. Use a cloud agent for a02 (no `agent: local`). If `## Library defects` in any lessons file is not `none` and no newer pin fixes it, set this step `blocked` with the reason.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

- Seeds are in `seeds/fleet/<repo>/` for the eight repositories. Each has `goal.md`, `plan.md`, `spec.md`, `loop.yaml`, `reference/` (secret guard files) and the steps a00 to a04. They follow the pilot seeds.
- Pin: `v0.1.2` (`3a2e9f3d95136958c54f73c831e84b971fc9a054`), the newest in `pins.tsv`. The `## Library defects` of every lessons file have no open defect that blocks this wave.
- Lessons applied from `lessons/pilot.md`: pin `v0.1.2`; probes and clones in `.probe/`; a04 agent records only `history-findings` and host checks (the gate does the clean clone and Docker); the probe commits the synthetic token before the check; each Dockerfile builds the shim cache as the image user and has `git` (lmdb-fs also makes a local Git commit before `uv sync`); re-run of `adopt apply` can rewrite `scripts/install_hooks.sh` (revert it); the `controls` job repeats the guard steps (accepted); all checks stay advisory. Lessons from `template.md` still apply (`--commit`, `docs/controls-adoption.md` by hand, no installs in agent sessions, one-sentence routing rule in `AGENTS.md`).
- Differences from the child spec, by fact of the target: the spec steps a01 to a04 gain the a00 secret guard step (decision `secret_guard` and the pilot). All steps use a cloud agent or `script`; no `agent: local`.
- Facts per repository come from its `Dockerfile`, `scripts/test_docker.sh` and `.github/workflows/context.yml`. Two repositories (`lmdb-fs`, `metadata_mcp`) have a separate `docker` CI job. `ffmpeg_mcp` passes `/app` to `check_context.py` in its Docker run. `compliance_poc` keeps its two secret-using workflows unchanged. Base branch is `master` for `compliance_poc`, `gpx_parser` and `sample_parse`.
- Not checked in this step: the Docker gates of the targets (the gate does not run Docker). The seeds say that the baseline Docker gate must pass before the change, and that the agent stops if it does not.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
