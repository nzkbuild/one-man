#!/usr/bin/env bash
# SessionStart hook — injects the project-aware, priority-ordered, budgeted memory digest.
#
# READ-ONLY: reads ~/.claude/self/ and ~/.claude/projects/<slug>/memory/. Never writes.
# FAIL-SAFE: any error -> exit 0 with no output, so a session is never blocked.
#
# The real work is in session-context.py. This wrapper captures the hook payload from
# stdin into HOOK_INPUT (a heredoc can't be used to pass the .py because it would occupy
# stdin and the payload — which carries cwd/source — would never reach Python).

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/session-context.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT" 2>/dev/null
exit 0
