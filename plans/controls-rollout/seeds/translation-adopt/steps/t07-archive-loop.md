---
id: t07-archive-loop
status: pending
depends_on: [t03-memory, t04-controls]
touches:
  - loop/STATE.md
  - loop/RUN.md
  - plans/adopt-ralph/steps/t07-archive-loop.md
lane: none
tier: light
gate: python3 -m unittest discover -s tools -p 'test_*.py' && python3 scripts/build_indexes.py --check && python3 scripts/check_context.py && python3 -I tools/verify.py --fast && grep -qi 'archived' loop/STATE.md && grep -qi 'archived' loop/RUN.md && grep -q 'plans/' loop/STATE.md && test -f loop/STOP && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Mark the old loop as archived

The private loop is replaced by `plans/` and the Ralph runner. Keep every old file. Only add a notice.

## Change

- `loop/STATE.md` and `loop/RUN.md`: add a short notice at the top, in Simplified Technical English. It says: this loop is archived at the queue state of today (write the output of `python3 tools/next_task.py --counts`); new work lives in `plans/` (see `GUIA-DEL-REPO.md` and `AGENTS.md`); `loop/STOP` stays (Part III checkpoint of the owner); do not run or resume `loop/ralph.sh`.
- `README.md` and `CONTRIBUTING.md` stay unchanged. They are English files with a PO translation, and neither has a section about the loop (checked on 2026-11-24). If you find a loop section now, write it under "Resume notes". Do not edit them.
- Do not delete or move any file of `loop/`. Do not touch the queue files, `loop/STOP` or the pre-push hook.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- t03-memory: the traps are in `memory/`. t04-controls: `scripts/check_context.py` and the controls.

## Done when

- The gate passes. `git diff --stat` shows only the two loop files and this step file.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
