# Lessons from the `translation-adopt` wave

Target: `aprende-a-programar-como-un-bicho-raro`. Child plan: `adopt-ralph`. Review date: 2026-11-23 (UTC).

| Target | Final plan commit |
| --- | --- |
| `aprende-a-programar-como-un-bicho-raro` | `f776cf00cc39fd81de763d25072597f838a39339` |

`python3 lib/fanout.py verify --plan-dir plans/controls-rollout --wave translation-adopt` printed `verified done` and `verify: 1/1 targets pass`. The record lists five operator amendments.

I read the child branch `plan/adopt-ralph` with Git plumbing only. I did not change the target repository. I did not run its tests again. The gates of the child steps ran them.

What I checked:

- Baseline. Step t08 compares with the t01 baseline: `verify.py --fast` is the same (`yes`). The tool tests are the same (`yes`): failures 10, errors 5, skips 1 as in the baseline. The 36 extra tests come from `tools/test_batch.py`, `tools/test_check_routing_map.py` and `tools/test_controls.py`. The queue counts are the same (`yes`): done 322, all other states 0.
- Scope. `git diff-tree -r --name-status loop/es-v4 plan/adopt-ralph` lists about 75 paths. Almost all are added files: layout, memory, controls, plan, scripts, batch tool and its fixtures, routing map. The modified files are `loop/RUN.md`, `loop/STATE.md`, `tools/inventory.py`, `tools/lock_code.py`, `tools/test_lock_code.py` and `translation/tooling-allowlist.txt`. No translated content, PO file or book build file is in the list. No file is deleted. The change of `tools/lock_code.py` comes from an operator amendment (the linked-worktree `.git` file defect). I did not read the content of the modified tool files. I only confirmed that they are tools and not content.
- Loop state. `loop/STOP` is still in the main checkout. The queue history is still there: the queue count is 322 done, and the diff has no deleted queue file.
- Batch tool. `tools/batch.py` uses only the standard library. The tests inject the HTTP function, so they run offline. `submit` refuses without `ANTHROPIC_API_KEY` and refuses without a positive `--max-usd`. It also refuses a total above the program cap of 100 USD, and it needs a cost file outside the repository. It never writes the key to a file.
- Routing map. `translation/routing.md` has rows for every task kind of the queue (meta, build-tool, gate, translate, localize-code, regen, audit, review-fix, packet), and `tools/check_routing_map.py` checks it. The measurement column is weak: almost every row says `no history`, because `loop/ledger/usage.jsonl` is untracked and absent from a worktree. Only one row quotes a measured fact (the local model made no edit in more than 70 minutes).

## Keep

- Keep the order of the child steps: secret guard (t00), baseline (t01), layout (t02), memory (t03), controls (t04), routing map (t05), batch tool (t06), archive of the old loop (t07), verify (t08). The baseline step makes t08 a real comparison.
- Keep the baseline comparison in t08 with the three `-same` lines and the history count. It proved that the move did not change results.
- Keep the rule that the old loop is archived and not deleted: `loop/STOP` and the queue history stay.
- Keep the batch tool design. The HTTP function is injected, so all tests are offline. `submit` needs a key, a cap and a cost file outside the repository. A running total stops a submission above the program cap. A ledger of applied custom IDs stops a second application.
- Keep the routing map check as a script (`tools/check_routing_map.py`), so the map cannot drift from the queue kinds.
- Keep the no-new-failures check against a recorded baseline (`no_new_failures.py`) for a repository whose tool tests have known failures.
- Keep `fanout.py amend` for operator changes. All five are in the audit log.

## Change

- Tell the agent that the tool tests have known failures. Give the baseline file and the count (15) in the seed. A gate of "all tests pass" is impossible there. Use a gate that compares with the recorded baseline.
- Tell the agent that `loop/STOP` is untracked, so a worktree does not have it. Write a gate that checks it in the main checkout, not in the worktree.
- Tell the agent to make any scratch clone inside the worktree in an excluded `.probe/` copy. The agent session cannot write outside the worktree or run `mktemp`. This rule already exists in the `pilot` lessons. Put it in the first draft of every verify step.
- Do not ask an agent to run the runner (`ralph-looper --status`) or to read the runner checkout. The agent session cannot reach it, and the view can create branches and worktrees. Use `check_context.py` (it runs `plans.schema` and `plans.graph`) and the parent `fanout.py verify`.
- Tell the agent in the seed to name each tool that must change (here `tools/lock_code.py`) and to put it in `touches`. A linked worktree has a `.git` file and not a folder. Any tool that reads `.git` as a folder fails there.
- Put the repository `.venv` on `PYTHONPATH` in the gate if the repository tools need a package (for example `polib`). The agent session has no virtual environment of its own.
- Write the routing map from the usage ledger. Make the seed say where the ledger is, or make an operator step copy the report into the map. A map with `no history` in most rows does not meet the check "quotes measurements".
- Tell the agent that a step that blocks three times on a denied command needs an operator amendment. Do not let it retry a fourth time. Drop the denied command from the step, as the operator did for t08.
- Keep the rules of the earlier lessons that are not listed here. They still apply.
- Count `attempts` against `steps` to judge a route. Do not use `first_pass_rate` alone.

## Library defects

none

The five amendments are defects of the seed text or of the repository tools, not of `deterministic-controls`. None of them shows a wrong or missing result of a library check.

## Route evidence

Output of `python3 lib/report.py --work "$RALPH_WORK" --by repo --format md`, row for this wave. The child plan has 9 steps (t00 to t08). The report has no `script` row for this repository, so t00 used the agent route too. The local and Codex routes were not used.

| repo | route | model | steps | attempts | first_pass_rate | seconds_total | seconds_median | tokens_in | tokens_out | usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aprende-a-programar-como-un-bicho-raro | claude | claude-sonnet-5-5 | 9 | 21 | 92% | 1962 | 78 | 10884544 | 129527 | 5.0281 |

Reading:

- The cloud agent (`claude-sonnet-5-5`) did all 9 steps. It used 21 attempts, which is 2.33 attempts for each step. The `pilot` wave had 3.25 for its agent steps and the `template` wave 1.5.
- The column `first_pass_rate` shows `92%`. This does not agree with 21 attempts for 9 steps. Do not use the column (see Change).
- Several steps needed more than one attempt (21 attempts for 9 steps). Step t08 was blocked after 3 attempts and needed an operator amendment. Five amendments in all changed the seed text during the wave.
- No executor used its fallback. The fallback was an operator change, not another executor.
- The wave cost 5.0281 USD for 1962 seconds of agent time.