---
id: t03-memory
status: pending
depends_on: [t02-layout]
touches:
  - memory/*.md
  - memory/AGENTS.md
  - plans/adopt-ralph/steps/t03-memory.md
lane: none
tier: light
gate: python3 scripts/build_indexes.py --check && python3 -I tools/verify.py --fast && test "$(ls memory/*.md | wc -l)" -ge 3 && ! grep -rEq '/home/|/Users/|C:\\' memory/ && for f in memory/*.md; do [ "$f" = memory/AGENTS.md ] || head -5 "$f" | grep -q '^gist: "Read me when:' || exit 1; done && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write one memory file for each trap

`loop/SIGNS.md` and the section "Traps to remember" of `loop/STATE.md` hold facts that cost time to find. Move each one into its own memory file, so that an agent finds it from `memory/AGENTS.md`.

## Change

- One file in `memory/` for each trap, with a short kebab-case name. Each file starts with front matter `gist: "Read me when: <the situation in which an agent needs this file>"`. Then the fact, the cause and what to do, in Simplified Technical English.
- Replace each local path, host name and user name by a placeholder (for example `<english-clone>`). Write no secret.
- Keep one file for one topic. Do not edit `loop/SIGNS.md` or `loop/STATE.md` here (`t07` does that).
- Run `python3 scripts/build_indexes.py` to refresh `memory/AGENTS.md`.

## Do not change

- Files outside `touches`. The `gate` command. Do not use `check_context.py` here: it comes in `t04`.

## Already done by earlier steps

- t02-layout: `memory/AGENTS.md`, `scripts/build_indexes.py` and the rules.

## Done when

- The gate passes. The count of memory files is at least the count of traps that you found. Write that count in "Record".

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
