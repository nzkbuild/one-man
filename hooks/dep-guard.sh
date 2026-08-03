#!/usr/bin/env bash
# PostToolUse hook — detects new dependency installations and nudges the model.
#
# FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/dep-guard.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit $?
