#!/usr/bin/env bash
# Run me when: I test ralph-looper without a real agent. (A fake agent for tests.)
# It reads the prompt, waits FAKE_SLEEP seconds, writes <step>.out, and prints Claude-style JSON.
cat > /dev/null
sleep "${FAKE_SLEEP:-0}"
echo "done by fake agent" > "${RALPH_STEP}.out"
git add -A && git commit -q -m "fake: ${RALPH_STEP}"
printf '{"result":"STEP-RESULT: %s done","total_cost_usd":0.01,"num_turns":2,"usage":{"input_tokens":10,"output_tokens":5,"cache_read_input_tokens":100,"cache_creation_input_tokens":20},"modelUsage":{"fake-model":{"outputTokens":5}}}\n' "$RALPH_STEP"
