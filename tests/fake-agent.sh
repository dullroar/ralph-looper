#!/usr/bin/env bash
# Run me when: I test ralph-looper without a real agent. (A fake agent for tests.)
# It reads the prompt, waits FAKE_SLEEP seconds, writes <step>.out, and prints Claude-style JSON.
# FAKE_LOG: append the step id to this file (to prove which steps called an agent).
# FAKE_MODE: ok (default) | nowrite (says done, writes nothing) | editgate (sets its own gate to `true`)
#            | outside (also writes outside.txt, not in touches) | newstep (also adds step zz-child).
cat > /dev/null
[ -n "${FAKE_LOG:-}" ] && echo "$RALPH_STEP" >> "$FAKE_LOG"
sleep "${FAKE_SLEEP:-0}"
sfile="plans/${RALPH_PLAN}/steps/${RALPH_STEP}.md"
case "${FAKE_MODE:-ok}" in
  nowrite) ;;
  editgate) sed -i 's/^gate: .*/gate: true/' "$sfile" ;;
  outside) echo "done by fake agent" > "${RALPH_STEP}.out"; echo "not in touches" > outside.txt ;;
  newstep)
    echo "done by fake agent" > "${RALPH_STEP}.out"
    if [ "$RALPH_STEP" != zz-child ]; then
      printf -- '---\nid: zz-child\nstatus: pending\ndepends_on: [%s]\ntouches:\n  - zz-child.out\nlane: none\ngate: test -f zz-child.out\n---\n# zz-child\n' \
        "$RALPH_STEP" > "plans/${RALPH_PLAN}/steps/zz-child.md"
    fi ;;
  *) echo "done by fake agent" > "${RALPH_STEP}.out" ;;
esac
git add -A && git commit -q -m "fake: ${RALPH_STEP}"
printf '{"result":"STEP-RESULT: %s done","total_cost_usd":0.01,"num_turns":2,"usage":{"input_tokens":10,"output_tokens":5,"cache_read_input_tokens":100,"cache_creation_input_tokens":20},"modelUsage":{"fake-model":{"outputTokens":5}}}\n' "$RALPH_STEP"
