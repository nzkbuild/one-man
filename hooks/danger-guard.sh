#!/usr/bin/env bash
# PreToolUse hook — blocks dangerous commands before they execute.
#
# READ-ONLY: never writes files, never runs commands it inspects.
# FAIL-SAFE: any error → exit 0, so a session is never blocked by a hook crash.
#
# The real work is in danger-guard.py. This wrapper captures the hook payload
# from stdin into HOOK_INPUT.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/danger-guard.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit $?
