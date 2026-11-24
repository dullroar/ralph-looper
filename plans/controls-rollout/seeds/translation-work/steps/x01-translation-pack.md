---
id: x01-translation-pack
status: pending
depends_on: []
touches:
  - controls.toml
  - scripts/controls-requirements.txt
  - translation/controls-adoption.md
  - translation/controls-pack-triage.md
  - plans/v4-es-1/steps/x01-translation-pack.md
lane: none
gate: python3 plans/v4-es-1/gatelib.py controls && grep -q 'd9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5' scripts/controls-requirements.txt && python3 plans/v4-es-1/gatelib.py triage translation/controls-pack-triage.md translation.fences translation.links translation.structure translation.glossary translation.chunks translation.untranslated-heuristic markdown.required-headings markdown.front-matter markdown.document-ids && python3 plans/v4-es-1/gatelib.py guard && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Enable the `v0.2.0` translation pack in advisory mode and triage each finding

## Change

- Pin: in `scripts/controls-requirements.txt` change the commit to `d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5` (`v0.2.0`). Keep the first line (`Run me when:`). The install line is `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5"`. Do not install anything: the operator puts the `v0.2.0` library on `PYTHONPATH`.
- `controls.toml`: enable the nine pack checks (`translation.fences`, `translation.links`, `translation.structure`, `translation.glossary`, `translation.chunks`, `translation.untranslated-heuristic`, `markdown.required-headings`, `markdown.front-matter`, `markdown.document-ids`). Read each parameter with `python3 -m deterministic_controls explain <id>`. The runner rejects a manifest parameter that the catalog does not declare, and `""` means "not configured". Scope the checks to the English/Spanish pairs (`translation/path-map.yaml`, `translation/glossary.es.yaml`). Keep every pack check advisory, as the existing checks are (see `translation/controls-adoption.md`). Do not touch the required job or the secret guard.
- Run the checks on this repository (`python3 -m deterministic_controls check --root . --profile ci --format json`). For each of the nine checks, write a row in `translation/controls-pack-triage.md` with: the check ID, the number of findings, the matching local tool of this repository (for example `tools/link_audit.py`, `tools/glossary_check.py`, `tools/invariants.py`, `tools/verify.py`) and its result on the same files, and a verdict. The verdict is one word: `agree` (same result, or each difference explained), `library-defect` (the library check is wrong), `translation-defect` (the check is right and the translation is wrong) or `no-local-tool`. For a `library-defect` write a probe that another person can run. Do not fix the translation here: list each `translation-defect` for the Jury lane.
- Add the pin, the scope and the result to `translation/controls-adoption.md`.

## Do not change

- Files outside `touches`. The `gate`. Translated content, PO files and locked code.

## Done when

- The checks run (exit `0` or `1`, never `2` or `3`) and all nine rows have a verdict. The gate does the run with the library on `PYTHONPATH`. If it exits `2`, the operator has not put `v0.2.0` there: write "Resume notes" and stop.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
