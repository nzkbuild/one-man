#!/usr/bin/env bash
# PreToolUse hook wrapper — anti-slop nudges (guide only, never blocks).
# Fail-safe: any error -> exit 0 silent.
set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/discipline-guard.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit 0
