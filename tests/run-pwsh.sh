#!/usr/bin/env bash
# Run me when: I changed ralph-looper.ps1 and want to prove the PowerShell driver routes steps
# (one agent step, one script step, one operator step). Uses a scratch repo and a fake agent.
# If pwsh is not on PATH, it prints "PowerShell test NOT RUN: pwsh not installed" and exits 0.
set -euo pipefail
if ! command -v pwsh >/dev/null 2>&1; then
  echo "PowerShell test NOT RUN: pwsh not installed"
  exit 0
fi
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"; [ -n "${KEEP:-}" ] || trap 'rm -rf "$TMP"' EXIT; echo "tmp=$TMP"
export RALPH_WORK="$TMP/work" AGENT_CMD="bash $HERE/tests/fake-agent.sh" RALPH_AGENT=claude
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.com
export FAKE_SLEEP=0 MAX_ATTEMPTS=1
fail() { echo "FAIL: $*"; exit 1; }
R="$TMP/demo"; mkdir -p "$R/plans/pw/steps"; cd "$R"; git init -q -b main
echo "# goal" > plans/pw/goal.md; printf -- '---\ngist: "Read me when: test"\n---\n# plan\n' > plans/pw/plan.md
printf 'gate_shell: bash\nmax_attempts: 1\n' > plans/pw/loop.yaml
step() {  # step ID GATE EXTRA
  printf -- '---\nid: %s\nstatus: pending\ndepends_on: []\ntouches:\n  - %s.out\nlane: none\ngate: %s\n%s---\n# %s\n' \
    "$1" "$1" "$2" "${3:-}" "$1" > "plans/pw/steps/$1.md"
}
step 01-agent "test -f 01-agent.out"
step 02-script "test -f 02-script.out" $'agent: script\nrun: echo made by script > 02-script.out\n'
step 03-op "test -f $TMP/marker" $'agent: operator\n'
git add -A; git commit -q -m init
LOOP=(pwsh -NoProfile -File "$HERE/ralph-looper.ps1" -Repo "$R" -Plan pw)

[ "$(pwsh -NoProfile -File "$HERE/ralph-looper.ps1" -Capabilities | paste -sd ' ' -)" = \
  "step-agent operator-step script-step local-agent gate-from-plan-branch touches-enforced" ] || fail "capabilities"

echo "== 1. agent and script steps done; operator step waits (exit 12) =="
rc=0; "${LOOP[@]}" > "$TMP/run1.out" 2>&1 || rc=$?
[ "$rc" = 12 ] || { cat "$TMP/run1.out"; fail "exit $rc, expected 12"; }
for s in 01-agent 02-script; do
  git show "plan/pw:plans/pw/steps/$s.md" | grep -q '^status: done' || { cat "$TMP/run1.out"; fail "$s not done"; }
done
git show plan/pw:02-script.out | grep -q 'made by script' || fail "script output not merged"
grep -q 'waiting for operator: 03-op' "$RALPH_WORK/demo/pw/driver.out" || fail "no waiting message"
grep -q '"agent":"script"' "$RALPH_WORK/demo/pw/ledger.jsonl" || fail "no script ledger line"
[ ! -e "$RALPH_WORK/demo/pw/attempts/03-op" ] || fail "operator wait counted an attempt"

echo "== 2. operator action done: the step passes =="
touch "$TMP/marker"
rc=0; "${LOOP[@]}" > "$TMP/run2.out" 2>&1 || rc=$?
[ "$rc" = 0 ] || { cat "$TMP/run2.out"; fail "exit $rc, expected 0"; }
git show plan/pw:plans/pw/steps/03-op.md | grep -q 'operator step, driver-verified' || fail "operator evidence wrong"
echo "PASS (PowerShell)"
