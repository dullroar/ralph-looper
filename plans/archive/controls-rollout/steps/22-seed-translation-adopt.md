---
id: 22-seed-translation-adopt
status: done
depends_on: [09-runner-adopts-controls, 13-publish-template]
touches:
  - plans/controls-rollout/seeds/translation-adopt/**
  - plans/controls-rollout/steps/22-seed-translation-adopt.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-adopt && python3 scripts/check_context.py && git diff --check
claimed_by: claude cli-default
claimed_at: "2026-11-24T02:05:43Z"
evidence: gate passed 2026-11-24 (driver-verified)
---

# Write the seed for the `translation-adopt` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-adopt.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-adopt/` as [waves/translation-adopt.tsv](../waves/translation-adopt.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Read the translation repository under `$REPOS_ROOT` (read only) to confirm the facts in the spec: the edition-owned registry that `tools/verify.py` reads, how `README.md` and `CONTRIBUTING.md` are generated, and the task kinds in `loop/queue`. Put the confirmed facts in the seed. Apply `lessons/controls.md` and `lessons/template.md`.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

Differences between the spec and the facts in the target (read on 2026-11-24). The seed follows the facts.

- **Registry.** The spec says "the inventory or allowlist that `tools/verify.py` reads". The edition-owned rules are `OWNED_PREFIXES`, `OWNED_FILES` and `OWNED_GLOBS` in `tools/inventory.py`. `translation/tooling-allowlist.txt` covers only tooling files (workflows, `lessons/**` scripts). New `.github/workflows/context.yml` needs a row there. `tools/`, `translation/`, `loop/` and `review/` are owned already.
- **New step `t00-secret-guard`.** The child plan contract needs the secret guard in the first adoption commit. The spec puts it inside t04, after t02. So the seed adds t00 (guard, hooks, blocking CI job). t00 also does all the registration, because the guard files in `scripts/` need it at once. This moves the registry edit from t02 to t00, so only one step edits it. t04 keeps the controls, the history scan record and the probe. The reference copies of the guard are in `reference/`.
- **`scripts/check_context.py` moves from t02 to t04.** The pinned shim needs `controls.toml`, which t04 writes. So the gates of t02, t03, t05 and t06 use `build_indexes.py --check` and `verify.py --fast`, not `check_context.py`. t07 and t08 use it.
- **README.md and CONTRIBUTING.md.** They are PO translations of English files. They have no section about the loop. t07 does not touch them.
- **Hooks.** The repository already has a lock hook (`tools/lock_code.py --install-hook`). The guard installer keeps it as `pre-commit.local`. The seed gives the order.
- **Extra files.** `tools/test_registry.py` (t00), `tools/test_controls.py` and `translation/controls-adoption.md` (t04), `tools/test_check_routing_map.py` (t05). The guard test lives in `tools/`, not `tests/`.
- **Pin.** `v0.1.1`, commit `0323de27...` (newest row of `pins.tsv`).
- **Operator note.** Run the shim or the library once with network access before the wave, so that the cache for the pinned commit exists (lesson of the `template` wave).

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

The seed is complete in `seeds/translation-adopt/` (goal, plan, loop.yaml, reference copies of the secret guard, steps t00 to t08). I did not set `status: done`, because the gate part `lib/fanout.py ready` fails for an outside reason:

- `python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-adopt` prints `checkout has uncommitted changes`. The canonical translation checkout has untracked files: `loop/driver.out.claude`, `review/ADVERSARIAL-REVIEW-PROMPT.md`, `review/canaries.key.json`, `review/packets/`, `review/repo-bundle.zip`, `review/units.index.jsonl`. `fanout.py` counts untracked files (`--untracked-files=all`). This step may not change another repository, so I did not touch them.
- Operator action: hide these untracked files from Git status (for example in that clone's `.git/info/exclude`), or move them out. Do not track them. Then run the gate again.
- What I checked by hand: `pick_step.py summary` on the seed gives `{"pending": 9}`, and `pick_step.py ready` gives `t00-secret-guard`. `python3 scripts/check_context.py` and `git diff --check` pass. The target has no `scripts/check_plan.py`, so the snapshot check runs only the picker.
- Remaining: run the full gate. If it passes, set `status: done` and write `evidence`.
