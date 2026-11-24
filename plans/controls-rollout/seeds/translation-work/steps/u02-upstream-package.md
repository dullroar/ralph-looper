---
id: u02-upstream-package
status: pending
depends_on: [u01-approve-guides]
touches:
  - translation/part3/upstream-package.patch
  - translation/part3/upstream-package.md
  - translation/part3/source-issues/**
  - plans/v4-es-1/steps/u02-upstream-package.md
lane: none
gate: python3 plans/v4-es-1/gatelib.py english-check && python3 plans/v4-es-1/gatelib.py approved-si plans/v4-es-1/records/u01-approve-guides.md translation/source-issues.md && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Refresh the upstream package for the English repository

## Change

- Read `translation/part3/upstream-package.md`, `plans/v4-es-1/records/u01-approve-guides.md` and the approved rows of `translation/source-issues.md`.
- Make a scratch clone of the English source in `.probe/english` (`git clone -q <english_clone_path of translation/source.json> .probe/english`, then check out the pinned commit). If this clone is denied, write "Resume notes" and stop.
- Refresh `translation/part3/upstream-package.patch` so that it applies to the pinned commit: the new `TRANSLATING.md` and one sentence in `CONTRIBUTING.md`, from the approved guides. For each approved source issue write one separate patch `translation/part3/source-issues/SI-NNN.patch`, one commit's change each. If no source issue is approved, write no patch.
- Run the English checks in the scratch clone (`python3 lessons/book/build.py --check` and the link and identity tests). Write the commands and results in `translation/part3/upstream-package.md`.
- Delete `.probe/` before the gate.

## Do not change

- Files outside `touches`. The `gate`. The English clone named in `source.json` (read only). Do not push, open a pull request or contact the maintainer.

## Done when

- The gate passes: the patches apply to a fresh clone at the pinned commit, and the English build check passes with them. The gate does the clean clone. You record only what you can run in `.probe/`.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
