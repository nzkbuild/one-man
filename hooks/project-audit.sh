#!/usr/bin/env bash
# SessionStart hook — audits the current project for missing safety nets (no git,
# tracked secrets, no tests, no design tokens) and surfaces them on the first prompt.
#
# READ-ONLY: never writes files, never mutates git state.
# FAIL-SAFE: any error -> exit 0 with no output, so a session is never blocked.
#
# Wrapper mirrors session-context.sh: stdin carries the payload, so it is captured
# into HOOK_INPUT rather than passed via heredoc (which would occupy stdin).

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/project-audit.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT" 2>/dev/null
exit 0
