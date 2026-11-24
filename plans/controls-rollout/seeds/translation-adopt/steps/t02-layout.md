---
id: t02-layout
status: pending
depends_on: [t01-baseline]
touches:
  - AGENTS.md
  - CLAUDE.md
  - GUIA-DEL-REPO.md
  - memory/AGENTS.md
  - plans/AGENTS.md
  - plans/for-each-plan/**
  - scripts/build_indexes.py
  - scripts/ctx_common.py
  - scripts/verify_fast.sh
  - scripts/AGENTS.md
  - plans/adopt-ralph/steps/t02-layout.md
lane: none
gate: python3 -m unittest discover -s tools -p 'test_*.py' && python3 scripts/build_indexes.py --check && python3 -I tools/verify.py --fast && grep -q 'repo-template' AGENTS.md && grep -q 'ralph-looper' AGENTS.md && grep -q 'Before changing this repository' AGENTS.md && grep -q 'Run me when:' scripts/verify_fast.sh && grep -q '^@AGENTS.md' CLAUDE.md && test -f plans/for-each-plan/steps/00-step-template.md && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the template layout and the agent contract

Make this repository follow the `repo-template` layout. `t00` registered all the paths. Do not edit `tools/inventory.py`.

## Change

- Copy `scripts/build_indexes.py` and `scripts/ctx_common.py` from the template (`$REPOS_ROOT/repo-template`, read only; use the version that has `scripts/secret_guard.py`). Copy `plans/for-each-plan/` from the template. Do not copy `scripts/check_context.py`: step `t04` adds it with the controls.
- `scripts/verify_fast.sh`: runs `python3 -I tools/verify.py --fast "$@"`. It has a comment block with a line `Run me when: I changed a file and want the fast check of the edition.`
- `AGENTS.md`: the template rules in Simplified Technical English (no private data in tracked files; start on a branch; do not push without authorization; secrets are never tracked; user instructions first). Add: the authorization limits of section 11.8 of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md` (summarize them, keep the same limits); the locked-code rule (`tools/lock_code.py`, never bypass the hook); the pinned-source rule (`translation/source.json`); `loop/STOP` stays; do not run `loop/ralph.sh`; the untracked files in `plan.md` of this plan; the rule "Do not weaken the controls": do not change the pin, `controls.toml` or the workflows to make a task pass; the routing sentence "Send each piece of work to the cheapest executor that can do it. The gate decides if the work is done."; and the rule "Before changing this repository's structure, read `repo-template` and `ralph-looper` (https://github.com/dullroar/repo-template and https://github.com/dullroar/ralph-looper) and account for their contracts." State that `docs/` is book content and that the human-docs index is `GUIA-DEL-REPO.md`. This is a deviation from the template, so record it in `AGENTS.md`.
- `CLAUDE.md` holds one line: `@AGENTS.md`.
- `GUIA-DEL-REPO.md`: the index for humans, in Simplified Technical English. Link `AGENTS.md`, `plans/`, `memory/`, `scripts/`, `translation/` and `loop/STATE.md` with one line each.
- Run `python3 scripts/build_indexes.py` to write `memory/AGENTS.md`, `plans/AGENTS.md` and `scripts/AGENTS.md`. Then run it with `--check`.

## Do not change

- Files outside `touches`. The `gate` command. `README.md`, `CONTRIBUTING.md` and `docs/`.
- Do not make `docs/README.md`.

## Already done by earlier steps

- t00-secret-guard: the guard, the hooks, the CI job and the registration of all paths.
- t01-baseline: the baseline numbers.

## Done when

- The gate passes. `verify.py --fast` accepts every new file.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
