# Agent adapters. Sourced by ralph-looper. Not run directly.
# Each command reads the prompt on stdin, works in the current directory, and prints its result.
# Environment: RALPH_MODEL, RALPH_EFFORT, RALPH_EFFORT_CFG are set by the driver.
# AGENT_CMD in the environment replaces the command (used by tests and for new agents).
# NOTE: allow-lists are guard rails, not a sandbox. Real protection is no credentials in the
# environment, no pushable remote, and a pre-push hook.

CLAUDE_ALLOW='Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python3:*),Bash(python:*),Bash(bash:*),Bash(pwsh:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(grep:*),Bash(find:*),Bash(sed:*),Bash(sort:*),Bash(diff:*),Bash(cp:*),Bash(mv:*),Bash(mkdir:*),Bash(touch:*),Bash(chmod:*),Bash(date:*),Bash(echo:*),Bash(printf:*),Bash(test:*),Bash(pwd:*),Bash(which:*),Bash(rm:*),Bash(cd:*),Bash(env:*),Bash(true:*),Bash(sleep:*),Bash(time:*)'
CLAUDE_DENY='"Bash(git push:*)" "Bash(gh:*)" "Bash(curl:*)" "Bash(wget:*)" "Bash(ssh:*)"'

agent_cmd() {  # agent_cmd NAME -> prints the shell command line
  case "$1" in
    claude)
      printf '%s' "claude -p --output-format json \${RALPH_MODEL:+--model \"\$RALPH_MODEL\"} --max-budget-usd ${MAX_STEP_USD:-6} --permission-mode dontAsk --allowedTools \"$CLAUDE_ALLOW\" --disallowedTools $CLAUDE_DENY" ;;
    copilot)
      printf '%s' 'copilot --no-auto-update --no-ask-user --assisted-approval --disable-builtin-mcps --output-format json ${RALPH_MODEL:+--model "$RALPH_MODEL"} ${RALPH_EFFORT:+--reasoning-effort "$RALPH_EFFORT"} --allow-tool="shell(python3)" --allow-tool="shell(git)" --allow-tool="shell(bash)" --allow-tool="write" --deny-tool="shell(git push)" --deny-tool="shell(gh)" --deny-tool="shell(curl)" --deny-tool="shell(wget)" --deny-tool="shell(ssh)" --prompt "$(cat)"' ;;
    codex)
      printf '%s' 'codex exec ${RALPH_MODEL:+-m "$RALPH_MODEL"} ${RALPH_EFFORT_CFG:+-c "$RALPH_EFFORT_CFG"} --approve-for-me --color never --json -' ;;
    local)
      echo "ralph-looper: the 'local' agent is not built yet. Set AGENT_CMD." >&2; return 1 ;;
    *) echo "ralph-looper: unknown agent '$1'" >&2; return 1 ;;
  esac
}
