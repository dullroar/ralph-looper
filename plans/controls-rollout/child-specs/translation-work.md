# Child spec: `v4-es-1` in aprende-a-programar-como-un-bicho-raro

Wave `translation-work`, `run=no`: `lib/fanout.py` provisions and publishes this plan, but Jim starts it. It replaces the queue of the old loop for the remaining work: phase 7 (the Jury), phase 8 (release), phase 9 (retrospective and cookbook rehearsal) and Part III (upstream package and Spanish adoption) of `SYNTHESIZED-TRANSLATION-PLAN-es-bicho-raro.md`, and the open items of `review/CHECKPOINT-part3.md`. Write the seed after the adoption (`lessons/translation-adopt.md`) and the translation pack (`lessons/translation-pack.md`) are reviewed, and after `v0.2.0` is pinned. Use the routing map `translation/routing.md` from the adoption. Where this spec and the routing map disagree, follow the routing map and record why.

## Shape

Five lanes run in parallel. The old loop ran one task at a time. Here each lane is independent until the release lane joins them. Inside the Jury lane, the fixes fan out as one step for each PO file or code family, with disjoint `touches`.

| Lane | Source | Steps | Executors |
| --- | --- | --- | --- |
| G: tooling | new | g01 | cloud agent |
| J: Jury | phase 7 | j01 to j10, plus generated `fix-*` steps | script, operator (batch and outside jurors), cloud agent (adjudication), local or cloud (fixes) |
| H: humor | phase 7 item 5, checkpoint item 4 | h01, h02 | operator, script |
| U: upstream | Part III, checkpoint items 1, 2, 5, 6 | u01 to u05 | operator, script, cloud agent |
| C: cookbook | phase 9 | c01 to c05 | cloud agent, script, operator (batch) |
| X: controls | translation pack | x01 | cloud agent |
| R: release | phase 8 | r01 to r03 | script, operator |

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| g01-lane-tools | cloud agent | `tools/fix_steps.py` (generate fix step files with disjoint `touches` from accepted findings), `tools/inbox_check.py` (juror count, vendors, lenses, format), `tools/jury_gate.py` (exit criteria of Gate 7). Tests with fixtures. | none |
| j01-packets | script | Rebuild packets, bundle and canaries for the current release candidate with `tools/jury_packet.py`. Keep them untracked. Record manifest digest and zero key hits. | none |
| j02-batch-requests | script | `tools/batch.py build` for the automated jurors, one request set for each lens (L1 to L13) and packet. | j01 |
| j03-batch-jurors | operator | Submit and collect the batch with a model that was not in the loop, under the USD cap. Gate: `tools/batch.py reconcile` passes and the replies are in `review/inbox/`. | j02 |
| j04-outside-jurors | operator | Jim sends packets to outside jurors (at least five jurors from at least three vendors, none in the loop; two on L11). Gate: `tools/inbox_check.py` passes. | j01, g01 |
| j05-ingest | script | `tools/jury_ingest.py` writes `review/report-<date>.md` with canary recall for each juror. | j03, j04 |
| j06-adjudicate | cloud agent | Fresh context, a model different from the translator. Decide each finding: accepted, rejected, duplicate, `needs-human`, `needs-source-issue`. Flag playfulness, guarantees, the 40-rule, safety and the acronym for Jim. | j05 |
| j07-human-decisions | operator | Jim decides the `needs-human` items. Gate: no undecided item. | j06 |
| j08-fanout-fixes | script | `tools/fix_steps.py` writes `steps/fix-*.md`. Mechanical fixes get `agent: local` with a cloud fallback. Fixes that change meaning get a cloud agent. Each gate: `verify.py --fast --files <po> <md>`, anchors, and the oracle for code families. | j07, g01 |
| j09-round-two | operator | After the fixes: delta packets for changed critical and major passages (script), a second round with new jurors (batch and outside). At most two rounds. | j08 and all `fix-*` |
| j10-gate-7 | script | `tools/jury_gate.py` and `verify.py --release`. | j09, h02 |
| h01-native-humor | operator | Native-speaker review of `translation/humor-register.jsonl`. | none |
| h02-humor-ingest | script | Record each humor item as kept, transcreated or deliberately flattened, with a reason. Items scored under 4 of 5 by two jurors become fix steps. | h01, j05 |
| u01-approve-guides | operator | Jim approves `TRANSLATING.md` and `TRADUCTORIO.md` and marks the source-issue rows to send. | none |
| u02-upstream-package | cloud agent | Refresh the upstream package with the approved source issues as separate commits, in a scratch clone of the English source. Run the English checks. | u01 |
| u03-upstream-pr | operator | Jim opens the upstream pull request through the maintainer process. Gate: the accepted English commit exists upstream. | u02 |
| u04-record-source | script | Record the accepted SHA in `translation/source.json` and run `tools/impact.py` to write the impact report. | u03 |
| u05-adopt-upstream | cloud agent | Turn the draft adoption plan (`translation/part3/spanish-adoption-plan-draft.md`, tasks A1 to A7) into steps from the impact report. Mark the draft final. | u04 |
| c01-synthetic-delta | cloud agent | Build the cookbook rehearsal fixture (section 12, item 12): a new paragraph, a changed code identifier, a moved heading, a new API symbol, a changed diagram, a change confined to generated output. | none |
| c02-impact | script | `tools/impact.py` and `msgmerge` on the fixture. Assert that only affected units are scheduled. | c01 |
| c03-delta-batch | operator | Minimal-edit drafts for the fuzzy entries through `tools/batch.py`. Import them with `translate.py --drafts` in a `script` substep. | c02 |
| c04-assert-reuse | script | Assert that untouched Spanish was reused with no model calls, and that every code, graph, book and link gate that the change reaches ran. | c03 |
| c05-retrospective | cloud agent | Update the cookbook with what broke, glossary changes, reviewer performance and the real spend for each phase and route (`tools/model_report.py`, batch cost records, the Ralph route report). Write `translation/runs/v4-es.1.yaml`. | c04, j10 |
| x01-translation-pack | cloud agent | Enable the `v0.2.0` translation pack in advisory mode. Triage each finding against the translation tools. A disagreement is a library defect or a translation defect; record which. | none |
| r01-release-gates | script | All gates, the double build and the link audit on the final candidate. | j10, h02, u01, x01 |
| r02-publish | operator | Jim says "publish": make the repository public, tag `v4-es.1`, attach the PDFs and EPUBs. | r01 |
| r03-verify-release | script | Download the release assets and verify their hashes against the build. | r02 |

## Rules for the seed

- The old loop stays stopped. `loop/STOP` stays. The first operator step that Jim does is u01 or h01, not a loop restart.
- `review/packets/`, `review/repo-bundle.zip`, `review/canaries.key.json` and `review/units.index.jsonl` stay untracked. `repo.forbidden-artifacts` enforces this.
- No step has the API key. Batch submission is always an operator step. Collection output is imported by `script` steps.
- Each `fix-*` step touches one PO file and its generated Markdown (or one code family), so the driver can run many at once with `--jobs`.
- The program has a total Batch API cap of USD 100. `tools/batch.py` enforces it from its cost records. Record the cap and the running total for each batch submission in the step. Use `tools/batch.py --dry-run` first and record the estimate.
- The seed gate must prove that the plan is valid in a snapshot of the target: `lib/fanout.py ready` and the target's `scripts/check_plan.py`.
