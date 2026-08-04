#!/usr/bin/env bash
# UserPromptSubmit hook — detects when the user is correcting me and nudges me to
# capture the lesson via /self-evolve.
#
# READ-ONLY: reads the prompt from stdin, prints JSON or nothing. Never writes.
# FAIL-SAFE: any error -> exit 0 with no output. Silent on normal prompts (zero noise).
#
# Input (stdin): JSON with a "prompt" field (the submitted user message).
# Output when a correction signal is found:
#   {"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

# Capture stdin into a variable FIRST. We cannot use a `python - <<HEREDOC` here
# because the heredoc would occupy stdin and the piped JSON would never reach
# Python. Instead we pass the hook payload through an env var.
HOOK_INPUT="$(cat)"
export HOOK_INPUT

CLAUDE_HOOK_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/prompt-guard.py"
[ -f "$CLAUDE_HOOK_SCRIPT" ] || exit 0

"$PY" "$CLAUDE_HOOK_SCRIPT" 2>/dev/null
exit 0
