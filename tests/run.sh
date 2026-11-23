#!/usr/bin/env bash
# Run me when: I changed ralph-looper and want to prove it works, including a kill -9 mid-step and restart.
# Uses a scratch repo and a fake agent. Costs no tokens. Needs git, flock, python3.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"; [ -n "${KEEP:-}" ] || trap 'rm -rf "$TMP"' EXIT; echo "tmp=$TMP"
export RALPH_WORK="$TMP/work" AGENT_CMD="bash $HERE/tests/fake-agent.sh" RALPH_AGENT=claude
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.com
R="$TMP/demo"; mkdir -p "$R/plans/p1/steps"; cd "$R"; git init -q -b main
echo "# goal" > plans/p1/goal.md; printf -- '---\ngist: "Read me when: test"\n---\n# plan\n' > plans/p1/plan.md
mk() { printf -- '---\nid: %s\nstatus: pending\ndepends_on: [%s]\ntouches:\n  - %s.out\nlane: none\ngate: test -f %s.out\n---\n# %s\n' "$1" "$2" "$1" "$1" "$1" > "plans/p1/steps/$1.md"; }
mk 01-a ""; mk 02-b ""; mk 03-c "01-a, 02-b"
# routing plans: one plan for each scenario. mk2 PLAN ID TOUCHES GATE [EXTRA FRONT MATTER LINES]
mk2() {
  mkdir -p "plans/$1/steps"; echo "# goal" > "plans/$1/goal.md"
  printf -- '---\ngist: "Read me when: test"\n---\n# plan\n' > "plans/$1/plan.md"
  printf -- '---\nid: %s\nstatus: pending\ndepends_on: []\ntouches:\n%s\nlane: none\ngate: %s\n%s---\n# %s\n' \
    "$2" "$(printf '  - %s\n' $3)" "$4" "${5:-}" "$2" > "plans/$1/steps/$2.md"
}
mk2 gatefail 01-x 01-x.out "test -f 01-x.out"
mk2 editgate 01-x 01-x.out "test -f 01-x.out"
mk2 outside 01-x 01-x.out "test -f 01-x.out"
mk2 script 01-s 01-s.out "test -f 01-s.out" $'agent: script\nrun: echo made by script > 01-s.out\n'
mk2 operator 01-op 01-op.out "test -f $TMP/operator-marker" $'agent: operator\n'
mk2 local 01-l 01-l.out "test -f 01-l.out" $'agent: local\nfallback: claude\n'
mk2 nolocal 01-n 01-n.out "test -f 01-n.out" $'agent: local\n'
mk2 secret 01-k 01-k.out "test -f 01-k.out"
mk2 newstep 01-p "01-p.out plans/newstep/steps/*.md" "test -f 01-p.out"
git add -A; git commit -q -m init
fail() { echo "FAIL: $*"; exit 1; }
LOOP="$HERE/ralph-looper --repo $R --plan p1"

echo "== 1. kill -9 mid-step =="
( FAKE_SLEEP=30 setsid $LOOP --jobs 2 > "$TMP/run1.out" 2>&1 & echo $! > "$TMP/pid" ) 
sleep 4; PGID="$(ps -o pgid= -p "$(cat "$TMP/pid")" | tr -d ' ')"; kill -9 -- "-$PGID"; sleep 1
[ -d "$RALPH_WORK/demo/p1/worktrees/01-a" ] || fail "no worktree left after kill"
flock -n "$RALPH_WORK/demo/p1/.lock" true || fail "lock still held after kill -9"

echo "== 2. restart (other agent name, fast) =="
FAKE_SLEEP=0 $LOOP --jobs 2 > "$TMP/run2.out" 2>&1 || { cat "$TMP/run2.out"; fail "restart exit $?"; }
git branch --list 'plan/p1' | grep -q . || fail "plan branch missing"
for s in 01-a 02-b 03-c; do git show plan/p1:plans/p1/steps/$s.md | grep -q '^status: done' || fail "$s not done"; git show "plan/p1:$s.out" >/dev/null || fail "$s.out not merged"; done
grep -q 'resuming step' "$RALPH_WORK/demo/p1/driver.out" || fail "no resume message"
grep -q -- '--- usage: step=' "$RALPH_WORK/demo/p1/driver.out" || fail "no usage block"
grep -q 'tokens: fresh_in=30' "$RALPH_WORK/demo/p1/driver.out" || fail "token line wrong"
[ -z "$(git status --porcelain)" ] || fail "repo working tree dirty"
git ls-files | grep -q 'driver.out\|ledger' && fail "runtime files tracked"
echo "== 3. pusher backs up plan and step branches =="
git init -q --bare "$TMP/remote.git"; git remote add backup "$TMP/remote.git"
git branch step/p1/99-x plan/p1
PUSH="$HERE/ralph-pusher --repo $R --plan p1 --remote backup --once"
$PUSH > "$TMP/push1.out" || fail "pusher failed"
[ "$(git --git-dir="$TMP/remote.git" rev-parse plan/p1)" = "$(git rev-parse plan/p1)" ] || fail "plan branch not on remote"
git --git-dir="$TMP/remote.git" rev-parse step/p1/99-x >/dev/null || fail "step branch not on remote"
git --git-dir="$TMP/remote.git" rev-parse main >/dev/null 2>&1 && fail "pusher pushed main"
$PUSH > "$TMP/push2.out" || fail "second pusher run failed"
[ -z "$(cat "$TMP/push2.out")" ] || fail "second run should be silent (nothing changed)"
echo "== 4. remote cleanup: merged step branch deleted, unmerged kept =="
git checkout -q -b step/p1/98-unmerged plan/p1; echo x > unmerged.txt; git add unmerged.txt; git commit -q -m unmerged; git checkout -q main
$PUSH > /dev/null || fail "pusher failed (push unmerged branch)"
git --git-dir="$TMP/remote.git" rev-parse step/p1/98-unmerged >/dev/null || fail "unmerged branch not pushed"
git branch -q -D step/p1/99-x step/p1/98-unmerged
$PUSH > "$TMP/push3.out" || fail "pusher failed (cleanup)"
grep -q 'deleted merged remote branch step/p1/99-x' "$TMP/push3.out" || fail "no delete message"
git --git-dir="$TMP/remote.git" rev-parse step/p1/99-x >/dev/null 2>&1 && fail "merged remote branch not deleted"
git --git-dir="$TMP/remote.git" rev-parse step/p1/98-unmerged >/dev/null 2>&1 || fail "UNMERGED remote branch was deleted"

W="$RALPH_WORK/demo"
on_plan() { git show "plan/$1:plans/$1/steps/$2.md" | grep -q "^$3"; }
run_plan() {  # run_plan PLAN [ENV...] -> exit code in $rc, output in $TMP/<plan>.out
  local pl="$1"; shift; rc=0
  env "$@" FAKE_SLEEP=0 SLEEP_SECS=0 MAX_ATTEMPTS=1 "$HERE/ralph-looper" --repo "$R" --plan "$pl" > "$TMP/$pl.out" 2>&1 || rc=$?
}
echo "== 5. agent says done, but the gate fails: not done =="
run_plan gatefail FAKE_MODE=nowrite
[ "$rc" = 11 ] || { cat "$TMP/gatefail.out"; fail "gatefail exit $rc, expected 11"; }
on_plan gatefail 01-x 'status: blocked' || fail "gatefail step not blocked"
grep -q 'result: 01-x gate FAILED' "$W/gatefail/driver.out" || fail "no gate FAILED message"

echo "== 6. agent edits its own gate: attempt fails =="
run_plan editgate FAKE_MODE=editgate
[ "$rc" = 11 ] || { cat "$TMP/editgate.out"; fail "editgate exit $rc, expected 11"; }
grep -q 'result: 01-x changed its own gate or scope' "$W/editgate/driver.out" || fail "no gate-change message"
on_plan editgate 01-x 'status: blocked' || fail "editgate step not blocked"
on_plan editgate 01-x 'gate: test -f 01-x.out' || fail "edited gate reached the plan branch"

echo "== 7. agent writes outside touches: attempt fails, file not merged =="
run_plan outside FAKE_MODE=outside
[ "$rc" = 11 ] || { cat "$TMP/outside.out"; fail "outside exit $rc, expected 11"; }
grep -q 'changed files outside touches: outside.txt' "$W/outside/driver.out" || fail "no outside-touches message"
git show plan/outside:outside.txt >/dev/null 2>&1 && fail "outside.txt merged"
git show plan/outside:01-x.out >/dev/null 2>&1 && fail "work of a failed step merged"

echo "== 8. script step: no agent call, ledger agent=script =="
run_plan script FAKE_LOG="$TMP/script.calls"
[ "$rc" = 0 ] || { cat "$TMP/script.out"; fail "script exit $rc"; }
[ ! -s "$TMP/script.calls" ] || fail "script step called the agent"
git show plan/script:01-s.out | grep -q 'made by script' || fail "script output not merged"
python3 -I -c 'import json,sys
r=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
s=[x for x in r if x["step"]=="01-s" and x.get("kind")!="gate"]
assert s and all(x["agent"]=="script" and x["cost_usd"]==0 and x["tok_out"]==0 for x in s), r' "$W/script/ledger.jsonl" || fail "ledger has no script line"

echo "== 9. operator step: waits (exit 12), then passes with no attempt =="
run_plan operator FAKE_LOG="$TMP/operator.calls"
[ "$rc" = 12 ] || { cat "$TMP/operator.out"; fail "operator exit $rc, expected 12"; }
grep -q 'waiting for operator: 01-op (see plans/operator/steps/01-op.md)' "$W/operator/driver.out" || fail "no waiting message"
on_plan operator 01-op 'status: pending' || fail "operator step not pending"
[ ! -e "$W/operator/attempts/01-op" ] || fail "operator wait counted an attempt"
[ ! -e "$W/operator/worktrees/01-op" ] || fail "operator worktree kept"
touch "$TMP/operator-marker"
run_plan operator FAKE_LOG="$TMP/operator.calls"
[ "$rc" = 0 ] || { cat "$TMP/operator.out"; fail "operator second run exit $rc"; }
on_plan operator 01-op 'status: done' || fail "operator step not done"
on_plan operator 01-op 'evidence: .*operator step, driver-verified' || fail "operator evidence wrong"
[ ! -s "$TMP/operator.calls" ] || fail "operator step called the agent"

echo "== 10. agent: local with no local command runs with its fallback =="
NOLOCAL_PATH="$(printf '%s' "$PATH" | tr ':' '\n' | while IFS= read -r d; do [ -n "$d" ] && [ ! -e "$d/local-coder-agent" ] && printf '%s:' "$d"; done)"
run_plan local -u LOCAL_AGENT_CMD PATH="${NOLOCAL_PATH%:}"
[ "$rc" = 0 ] || { cat "$TMP/local.out"; fail "local fallback exit $rc"; }
grep -q 'step=01-l agent=claude' "$W/local/driver.out" || fail "fallback agent not used"
on_plan local 01-l 'status: done' || fail "local fallback step not done"
run_plan nolocal -u LOCAL_AGENT_CMD PATH="${NOLOCAL_PATH%:}"
[ "$rc" = 11 ] || { cat "$TMP/nolocal.out"; fail "nolocal exit $rc, expected 11"; }
grep -q 'waiting: agent local not available' "$W/nolocal/driver.out" || fail "no agent-not-available message"
[ ! -e "$W/nolocal/worktrees/01-n" ] || fail "unavailable step was started"
run_plan nolocal LOCAL_AGENT_CMD="bash $HERE/tests/fake-agent.sh"
[ "$rc" = 0 ] || { cat "$TMP/nolocal.out"; fail "LOCAL_AGENT_CMD run exit $rc"; }
grep -q 'step=01-n agent=local' "$W/nolocal/driver.out" || fail "local agent not used"

echo "== 11. a merged step adds a new step: the next loop runs it =="
run_plan newstep FAKE_MODE=newstep
[ "$rc" = 0 ] || { cat "$TMP/newstep.out"; fail "newstep exit $rc"; }
on_plan newstep zz-child 'status: done' || fail "new step not run"
git show plan/newstep:zz-child.out >/dev/null || fail "new step output not merged"

echo "== 11b. secret guard: a synthetic key fails the step and is not merged =="
cat > "$TMP/secret-agent.sh" <<'AGENT'
#!/usr/bin/env bash
cat > /dev/null
{ printf '%s\n' "-----BEGIN ""PRIVATE KEY-----"; echo "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo="; printf '%s\n' "-----END ""PRIVATE KEY-----"; } > "${RALPH_STEP}.out"
git add -A && git commit -q -m "fake: ${RALPH_STEP}"
printf '{"result":"STEP-RESULT: %s done","total_cost_usd":0.01,"num_turns":1,"usage":{"input_tokens":1,"output_tokens":1},"modelUsage":{"fake-model":{"outputTokens":1}}}\n' "$RALPH_STEP"
AGENT
run_plan secret AGENT_CMD="bash $TMP/secret-agent.sh"
[ "$rc" = 11 ] || { cat "$TMP/secret.out"; fail "secret exit $rc, expected 11"; }
grep -q 'result: 01-k secret guard FAILED' "$W/secret/driver.out" || fail "no secret guard FAILED message"
git show plan/secret:01-k.out >/dev/null 2>&1 && fail "secret file merged"
git grep -q 'PRIVATE KEY' plan/secret 2>/dev/null && fail "key on the plan branch"

echo "== 11c. ledger has route, attempt and a gate line =="
python3 -I -c 'import json,sys
r=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
run=[x for x in r if x.get("step")=="01-s" and x.get("kind")!="gate"]
gl=[x for x in r if x.get("kind")=="gate" and x.get("step")=="01-s"]
assert run and run[0]["route"]=="script" and run[0]["attempt"]==1, r
assert gl and gl[0]["gate"]=="pass" and gl[0]["attempt"]==1, r' "$W/script/ledger.jsonl" || fail "ledger lacks route/attempt/gate line"
python3 -I -c 'import json,sys
r=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
assert any(x.get("kind")=="gate" and x["gate"]=="fail" for x in r), r' "$W/gatefail/ledger.jsonl" || fail "no failing gate line"
python3 -I "$HERE/lib/report.py" --work "$W" > "$TMP/report.out" || fail "report failed on test ledgers"

echo "== 12. --capabilities =="
[ "$("$HERE/ralph-looper" --capabilities | paste -sd ' ' -)" = "step-agent operator-step script-step local-agent gate-from-plan-branch touches-enforced" ] || fail "capabilities"
[ -z "$(git status --porcelain)" ] || fail "repo working tree dirty at the end"
echo "PASS"
