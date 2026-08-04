#!/usr/bin/env bash
# PostToolUse hook — detects new dependency installations and nudges the model.
#
# FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/dep-guard.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit $?
