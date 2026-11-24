---
id: 26-seed-translation-pack
status: done
depends_on: [24-review-translation-adopt]
touches:
  - plans/controls-rollout/seeds/translation-pack/**
  - plans/controls-rollout/steps/26-seed-translation-pack.md
lane: none
gate: python3 lib/fanout.py ready --plan-dir plans/controls-rollout --wave translation-pack && python3 scripts/check_context.py && git diff --check
claimed_by: ""
claimed_at: ""
evidence: "gate (fanout.py ready --wave translation-pack && check_context.py && git diff --check): passed, 'ready seed translation-pack on main {pending: 10}', 2026-11-23"
---

# Write the seed for the `translation-pack` wave

Read [the child plan contract](../child-specs/README.md) and [the child spec](../child-specs/translation-pack.md). Read every file in `lessons/` and apply each rule under `## Change` that fits this wave. Read [pins.tsv](../pins.tsv) and use the newest pinned commit.

Write the seed in `seeds/translation-pack/` as [waves/translation-pack.tsv](../waves/translation-pack.tsv) says. Do not change the wave manifest or the child spec. If the spec is wrong for a fact you find in the target, follow the fact, and record the difference and the reason under "Notes" below.

Read the translation tools listed in the spec at `plan/adopt-ralph` in the translation repository (read only, with `git show`). Copy the rules, edge cases and negative fixtures that the child needs into the seed. Apply `lessons/controls.md` and `lessons/translation-adopt.md`.

The gate runs `lib/fanout.py ready`. It checks each target and runs the target's plan checker on a snapshot with the seed in place. It does not change the target.

## Notes

Differences from the child spec. Each follows a fact of the target or of the translation repository.

- **No YAML.** The library uses the standard library only. The translation tools read YAML (`glossary.es.yaml`) and use `markdown-it-py` and `polib`. The pack glossary is TOML, and the pack has its own small Markdown scanner. The review step must check that a translation glossary converts to the pack format without loss.
- **Acceptance "same result as the local tool" moves to the review.** The child has no copy of the translation repository. The seed copies the rules and the planted defects of `invariants.py`, `mask.py`, `link_audit.py`, `mermaid.py`, `glossary_check.py`, `dnt.py`, `negative.py` and `part2_negative.py` (at `plan/adopt-ralph`, commit `f776cf0`). Step 28 compares each check with the matching tool. Each difference goes in its lessons file.
- **Source tree inside the root.** A check reads files only through `Context`, which refuses paths outside the repository. The source clone of the translation repository is outside it. The pack documents this limit. The chunk check needs no source tree.
- **Added checks.** The spec names no IDs for pack A. The seed uses `markdown.required-headings`, `markdown.front-matter` and `markdown.document-ids` (step p07).
- **History scan.** The spec has no verify step. Step p10 runs `secret_guard.py --history` and records the count.
- **Lessons applied.** `controls`: `touches` lists every earlier test file that step p09 may need to fix, and p10 lists both version sources; every step tells the agent to run the full suite; no `agent: local`; no wheel digest compare. `translation-adopt`: the seed tells the agent which commands it cannot run, and when to stop after a denied command. `pilot` and `template` lessons about adoption (shim, `adopt apply`, Docker, probes) do not apply: this child changes the library itself, whose secret guard exists already.
- **Pin.** The newest pin is `v0.1.2` (`3a2e9f3d95136958c54f73c831e84b971fc9a054`). The seed uses it for the install line of the current release.

## Do not change

- Files outside `touches`. The `gate`. Any repository other than this one, unless this is an operator step.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
