---
gist: "Read me when: you run or change the plan that finishes the Spanish edition v4-es.1: the Jury, the humor review, the upstream package, the cookbook rehearsal, the translation pack and the release."
---

# Plan `v4-es-1`: finish the Spanish edition on the Ralph runner

This file is the high-level plan. The detail is in `steps/`. Every step is self-contained. Read this file for the shared facts.

## Approach

The old loop ran one task at a time. Here seven lanes run in parallel until the release lane joins them. Each step has its own executor (see `translation/routing.md`): a `script` for programs, an `operator` step for every action that needs Jim, the Batch API or an outside party, and a cloud agent for judgment and fixes. The gate of each step proves the result. Gates run in the driver, in a linked worktree that holds tracked files only.

## Before the operator starts this plan

1. Put a checkout of `deterministic-controls` at commit `d9a1a604fddb5b268a8dadeb693bcbe7fecbf6e5` (`v0.2.0`) on `PYTHONPATH`. Step x01 and the context gate need it.
2. Keep `loop/STOP` in the main checkout. Every release-lane gate checks it.
3. Add `/.probe/` to `.git/info/exclude` of the main checkout. Make sure that `review/packets/`, `review/repo-bundle.zip`, `review/canaries.key.json`, `review/units.index.jsonl` and `translation/work/` are untracked and ignored there.
4. The Batch API key is only in the operator shell as `ANTHROPIC_API_KEY`. Cost records and the applied ledger live outside the repository, in `$RALPH_WORK/aprende-a-programar-como-un-bicho-raro/v4-es-1/batch/`. Never use `--drafts` or `submit` in an agent step.

## Facts (from the repository, 2026-11-24)

- **Gate helper.** `plans/v4-es-1/gatelib.py` holds the shared checks (`python3 plans/v4-es-1/gatelib.py --help` lists them). No step may change it. It uses the repository `.venv` of the main checkout when it exists, so that `polib` and the other packages are found. Do not use `python3 -I` in a gate where a package must be found: call `gatelib.py verify` and `gatelib.py tests`.
- **Known test failures.** The tool tests have known failures (10 failures, 5 errors, 1 skip in a worktree). `plans/adopt-ralph/tools-test-baseline.txt` records them. `gatelib.py tests` means "no new failure and no fewer tests". A step may add tests. It must not break one.
- **Untracked private files.** `review/packets/`, `review/repo-bundle.zip`, `review/canaries.key.json`, `review/units.index.jsonl`, `loop/driver.out*` and `translation/work/` stay untracked (`repo.forbidden-artifacts` enforces it). A worktree does not have them. Steps and gates build what they need in `.probe/` and delete it.
- **Registry.** `tools/`, `translation/`, `review/`, `loop/` and `plans/` are edition-owned. New files there need no registry change. A new Markdown file in `scripts/` or `memory/` needs `python3 scripts/build_indexes.py`.
- **Linked worktree.** In a worktree `.git` is a file. A tool that reads `.git` as a folder fails there. Name such a tool in the step and put it in `touches`.
- **Batch API.** `tools/batch.py` (`build`, `submit`, `status`, `collect`, `reconcile`) is run by the operator. `submit` needs `ANTHROPIC_API_KEY` and `--max-usd`. The program cap is USD 100 in total for all submissions. Run `--dry-run` first and record the estimate. A batch step of this plan carries `usd-cap: SET-BY-JIM`. Its gate fails until Jim writes a number (0 to 100). Submit one batch at a time, so that the running total in the cost file is right.
- **Jury files.** Packets: `tools/jury_packet.py --build --bundle --code`. Replies: `review/inbox/<juror>-<lens>-<date>.md`, where `<juror>` starts with `batch-` for a Batch API juror and `outside-` for an outside juror. Ingest: `tools/jury_ingest.py` writes `review/report-<date>.md` and `review/findings-<date>.jsonl` (finding schema in `translation/schemas/finding.schema.json`, status `open`). Lenses: L1 to L13 in `review/ADVERSARIAL-REVIEW-PROMPT.md`.
- **Contracts between the new tools** (g01 and g02 write them, later steps use them):
  - Adjudication: the adjudicator sets `status` in `review/findings-<date>.jsonl` to `accepted`, `rejected`, `duplicate`, `needs-human` or `needs-source-issue`, and a one-line `reason`. Jim adds `human_decision` (`accepted`, `rejected` or `source-issue`) and `human_reason` to each `needs-human` row.
  - Juror table: `plans/v4-es-1/records/j04-outside-jurors.tsv` with columns `juror`, `vendor`, `model`, `lens`, `date`, `in_loop` (`no`).
  - Batch input rows for the Jury: `segment_id` is `<packet-id>.<lens>` (for example `P-critical-01.L1`), `english_masked` holds the lens text and the packet.
  - Humor: Jim's review is `translation/humor-review.jsonl`. The result is `translation/humor-decisions.jsonl` (one row for each register item: `kept`, `transcreated` or `flattened`, with a reason).
  - Fix steps: `plans/v4-es-1/steps/fix-*.md`, written by `tools/fix_steps.py`.
- **English clone.** `translation/source.json` names the clone (`english_clone_path`) and the pinned commit. Tools read the commit with `git ls-tree`, so the clone only has to contain the object. Do not move its HEAD.
- **Routing.** `translation/routing.md` maps the task kinds. In this plan: `packet` and `gate` are `script`; `audit` is `script`, `batch` or `operator`; `review-fix` is an agent (a different model from the translator) or `batch`; `meta` is a light agent or `operator`.
- **Models.** The translator and the in-loop reviewer were `claude-sonnet-5-5`. The adjudicator (j06) uses another vendor (`agent: codex`). A Batch API juror must not be a model of the loop.
- **Local model.** Not used (owner decision 2026-11-23: too slow on this host).

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| [g01-lane-tools](./steps/g01-lane-tools.md) | cloud agent | `fix_steps.py`, `inbox_check.py`, `jury_gate.py` with tests. | none |
| [g02-lane-requests](./steps/g02-lane-requests.md) | cloud agent | `jury_requests.py` and `humor_ingest.py` with tests. | none |
| [j01-packets](./steps/j01-packets.md) | script | Build the packets twice, record the digest, check for leaks. | none |
| [j02-batch-requests](./steps/j02-batch-requests.md) | script | Build the Jury batch input for L1 to L13 and dry-run it. | j01, g02 |
| [j03-batch-jurors](./steps/j03-batch-jurors.md) | operator | Submit and collect the Jury batch under the USD cap. | j02 |
| [j04-outside-jurors](./steps/j04-outside-jurors.md) | operator | Outside jurors review the packets. | j01, g01 |
| [j05-ingest](./steps/j05-ingest.md) | script | Ingest the replies, write the report and the findings. | j03, j04 |
| [j06-adjudicate](./steps/j06-adjudicate.md) | agent (other vendor) | Decide every finding. | j05 |
| [j07-human-decisions](./steps/j07-human-decisions.md) | operator | Jim decides the `needs-human` findings. | j06 |
| [j08-fanout-fixes](./steps/j08-fanout-fixes.md) | script | Write one fix step for each PO file or code family. | j07, g01 |
| [j09-round-two](./steps/j09-round-two.md) | operator | Second round on the changed passages, or a recorded reason for none. | j08, h02 and all `fix-*` (by its gate) |
| [j10-gate-7](./steps/j10-gate-7.md) | script | Gate 7 and `verify.py --release --no-gates`. | j09, h02 |
| [h01-native-humor](./steps/h01-native-humor.md) | operator | Native-speaker review of the humor register. | g02 (its gate uses the tool) |
| [h02-humor-ingest](./steps/h02-humor-ingest.md) | script | Decide each humor item. Low scores become fix steps. | h01, j05, g02 |
| [u01-approve-guides](./steps/u01-approve-guides.md) | operator | Jim approves both guides and the source issues to send. | none |
| [u02-upstream-package](./steps/u02-upstream-package.md) | cloud agent | Refresh the upstream package. | u01 |
| [u03-upstream-pr](./steps/u03-upstream-pr.md) | operator | Jim opens the upstream pull request. | u02 |
| [u04-record-source](./steps/u04-record-source.md) | script | Pin the accepted commit, write the impact report. | u03 |
| [u05-adopt-upstream](./steps/u05-adopt-upstream.md) | cloud agent | Turn the draft adoption plan into steps. | u04 |
| [c01-synthetic-delta](./steps/c01-synthetic-delta.md) | cloud agent | Rehearsal fixture and tool. | none |
| [c02-impact](./steps/c02-impact.md) | script | Impact map and `msgmerge` on the fixture. | c01 |
| [c03-delta-batch](./steps/c03-delta-batch.md) | operator | Minimal-edit drafts through the Batch API. | c02 |
| [c04-assert-reuse](./steps/c04-assert-reuse.md) | script | Import the drafts. Prove reuse and the gates. | c03 |
| [c05-retrospective](./steps/c05-retrospective.md) | cloud agent | Cookbook update and run file. | c04, j10 |
| [x01-translation-pack](./steps/x01-translation-pack.md) | cloud agent | Enable the `v0.2.0` pack (advisory). Triage each finding. | none |
| [r01-release-gates](./steps/r01-release-gates.md) | script | All release gates, double build, asset hashes. | j10, h02, u01, x01 |
| [r02-publish](./steps/r02-publish.md) | operator | Jim publishes and tags `v4-es.1`. | r01 |
| [r03-verify-release](./steps/r03-verify-release.md) | script | Check the downloaded assets against the build. | r02 |

Generated steps: `j08` writes `fix-po-*` and `fix-code-*`, and `h02` writes `fix-humor-*`. They depend on their generator. Step `j09` and step `r01` do not list them in `depends_on`: the gate of `j09` runs `python3 tools/fix_steps.py --all-done plans/v4-es-1`, and the driver runs ready agent steps before it waits for an operator step.

## Parallelism

- Seven lanes start together: g (g01, g02), j (j01), h (h01), u (u01), c (c01), x (x01). Operator steps wait for Jim while the others run.
- Inside the Jury lane, the fix steps touch one PO file and its generated Markdown (or one code family) each. The driver runs them together with `--jobs 4`.
- No two steps that can run together touch the same file. Each step writes its own step file, its own record in `plans/v4-es-1/records/` and its own outputs. The batch jurors write `review/inbox/batch-*`, the outside jurors write `review/inbox/outside-*`.
- Docker, FUSE and agent quota are shared host limits. Lower `--jobs` if they are not enough.

## Risks

- **Private data leaves the machine.** The packets hold canaries and go to vendors by design. The bundle never holds the key (`jury_packet.py` checks it). The secret guard runs before each merge. Do not add an exception.
- **A batch costs too much.** The gate of each batch step fails while the cap is a placeholder. `batch.py` refuses a total above USD 100. Run `--dry-run` first.
- **The pin moves under other lanes.** Step u04 changes `translation/source.json`. The English clone needs only the new object, not a new HEAD (see Facts). If a gate of another lane starts to fail after u04, check this first.
- **The full release gate cannot pass on the host.** `verify.py --release` runs every tool test and needs Docker and the Mermaid CLI. If r01 fails only for host reasons that the baseline records, the operator fixes the host or uses `fanout.py amend`. Nobody weakens the gate.
- **The operator starts the old loop by mistake.** `loop/STOP` stays. Gates `g01`, `r01` and the `guard` check it.
- **Late or duplicate batch results.** `batch.py` uses stable `custom_id` values and an applied ledger. Reconcile before every import.
