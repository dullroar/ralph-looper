---
id: t05-routing-map
status: pending
depends_on: [t02-layout]
touches:
  - translation/routing.md
  - tools/check_routing_map.py
  - tools/test_check_routing_map.py
  - plans/adopt-ralph/steps/t05-routing-map.md
lane: none
gate: python3 tools/check_routing_map.py && python3 -m unittest tools/test_check_routing_map.py && python3 scripts/build_indexes.py --check && python3 -I tools/verify.py --fast && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Write the measured routing map and its checker

Decide which executor does each kind of task, from the measured history of the 549 iterations.

## Change

- Measure with `python3 tools/model_report.py` and `loop/ledger/usage.jsonl` (untracked; read only). Get cost, wall time and retry rate by task kind and model. If the ledger is missing, write `no history` as the measurement, and say so under "Resume notes".
- `translation/routing.md`: one table with the columns `kind | route | reason | measurement | expected cost change`. One row for every `kind` that occurs in `loop/queue/**/*.jsonl` (today: `meta`, `build-tool`, `gate`, `translate`, `regen`, `audit`, `review-fix`, `localize-code`; read the files for the full set). Allowed routes, exactly:
  - `script` or `ci`: segmenting, masking, invariants, oracle runs, link and anchor audits, packet building, `msgmerge`, impact maps, builds, imports, reports.
  - `batch`: bulk drafts of new and fuzzy segments, minimal-edit deltas, automated reviewer passes, back-translation, canary scoring input. The operator submits through `tools/batch.py`. A `script` step imports the result.
  - `agent-light`: bounded tool fixes, fixture additions, doc moves. A cloud agent with `tier: light`. The local model is not used (owner decision of 2026-11-23). Give its measured cost from the bootstrap wave as the reason: three parallel local steps on an 8 GB GPU made no file edit in more than 70 minutes.
  - `agent-standard`: adjudication, review-fix with judgment, new tooling, prompt changes. A cloud agent with a model different from the one that produced the work under review.
  - `operator`: jury with outside vendors, native-speaker humor review, approvals, upstream pull requests, publication.
  A kind can map to more than one route only with one row for each route and a reason in each row. Write the expected cost change for each move from the measured history.
- `tools/check_routing_map.py` (standard library only; exit `0` pass, `1` defects): every `kind` in `loop/queue/**/*.jsonl` has a row with an allowed route; every row has a non-empty reason and a measurement or the words `no history`; a row for a kind that is not in the queue is allowed.
- `tools/test_check_routing_map.py`: build a scratch queue and a scratch map at run time. A map with a missing kind, an unknown route or an empty reason fails for that reason (known bad). A complete map passes (known good). Do not assert the number of kinds.

## Do not change

- Files outside `touches`. The `gate` command. Do not use `check_context.py` here: it comes in `t04`.

## Already done by earlier steps

- t02-layout: the registration (`translation/` and `tools/` are owned), `build_indexes.py` and the rules.

## Done when

- The gate passes. The checker fails on each bad sample for the expected reason.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
