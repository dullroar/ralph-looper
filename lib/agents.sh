# Agent adapters. Sourced by ralph-looper. Not run directly.
# Each command reads the prompt on stdin, works in the current directory, and prints its result.
# Environment: RALPH_MODEL, RALPH_EFFORT, RALPH_EFFORT_CFG are set by the driver.
# AGENT_CMD in the environment replaces the command of the --agent executor (used by tests).
# AGENT_CMD_<NAME> (for example AGENT_CMD_CODEX) replaces the command of one named agent.
# The local agent: LOCAL_AGENT_CMD if set, else `local-coder-agent` on PATH. The operator installs that
# wrapper; it runs Claude Code against the local model. It gets the same flags (and the same allow and
# deny lists) as claude. The repository never names a local path.
# `script` and `operator` are executors with no command: the driver runs them itself.
# NOTE: allow-lists are guard rails, not a sandbox. Real protection is no credentials in the
# environment, no pushable remote, and a pre-push hook.

CLAUDE_ALLOW='Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python3:*),Bash(python:*),Bash(bash:*),Bash(pwsh:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(grep:*),Bash(find:*),Bash(sed:*),Bash(sort:*),Bash(diff:*),Bash(cp:*),Bash(mv:*),Bash(mkdir:*),Bash(touch:*),Bash(chmod:*),Bash(date:*),Bash(echo:*),Bash(printf:*),Bash(test:*),Bash(pwd:*),Bash(which:*),Bash(rm:*),Bash(cd:*),Bash(env:*),Bash(true:*),Bash(sleep:*),Bash(time:*),Bash(npm:*),Bash(npx:*),Bash(node:*)'
CLAUDE_DENY='"Bash(git push:*)" "Bash(gh:*)" "Bash(curl:*)" "Bash(wget:*)" "Bash(ssh:*)"'

claude_flags() {
  printf '%s' "-p --output-format json \${RALPH_MODEL:+--model \"\$RALPH_MODEL\"} --max-budget-usd ${MAX_STEP_USD:-6} --permission-mode dontAsk --allowedTools \"$CLAUDE_ALLOW\" --disallowedTools $CLAUDE_DENY"
}

agent_known() {  # agent_known NAME -> exit 0 if NAME is an executor that the driver knows
  case "$1" in claude|codex|copilot|local|script|operator) return 0 ;; *) return 1 ;; esac
}

agent_available() {  # agent_available NAME -> exit 0 if the default command of NAME can run here
  case "$1" in
    script|operator) return 0 ;;
    local) [ -n "${LOCAL_AGENT_CMD:-}" ] || command -v local-coder-agent >/dev/null 2>&1 ;;
    claude|codex|copilot) command -v "$1" >/dev/null 2>&1 ;;
    *) return 1 ;;
  esac
}

agent_cmd() {  # agent_cmd NAME -> prints the shell command line
  case "$1" in
    claude)
      printf '%s' "claude $(claude_flags)" ;;
    copilot)
      printf '%s' 'copilot --no-auto-update --no-ask-user --assisted-approval --disable-builtin-mcps --output-format json ${RALPH_MODEL:+--model "$RALPH_MODEL"} ${RALPH_EFFORT:+--reasoning-effort "$RALPH_EFFORT"} --allow-tool="shell(python3)" --allow-tool="shell(git)" --allow-tool="shell(bash)" --allow-tool="write" --deny-tool="shell(git push)" --deny-tool="shell(gh)" --deny-tool="shell(curl)" --deny-tool="shell(wget)" --deny-tool="shell(ssh)" --prompt "$(cat)"' ;;
    codex)
      printf '%s' 'codex exec ${RALPH_MODEL:+-m "$RALPH_MODEL"} ${RALPH_EFFORT_CFG:+-c "$RALPH_EFFORT_CFG"} --approve-for-me --color never --json -' ;;
    local)
      if [ -n "${LOCAL_AGENT_CMD:-}" ]; then printf '%s' "$LOCAL_AGENT_CMD $(claude_flags)"
      elif command -v local-coder-agent >/dev/null 2>&1; then printf '%s' "local-coder-agent $(claude_flags)"
      else echo "ralph-looper: the 'local' agent needs LOCAL_AGENT_CMD or 'local-coder-agent' on PATH" >&2; return 1
      fi ;;
    script|operator)
      echo "ralph-looper: '$1' steps have no agent command (the driver runs them)" >&2; return 1 ;;
    *) echo "ralph-looper: unknown agent '$1'" >&2; return 1 ;;
  esac
}
