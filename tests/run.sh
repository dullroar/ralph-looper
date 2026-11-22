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
echo "PASS"
