#!/usr/bin/env bash
# SessionEnd hook wrapper — records session stats to ~/.claude/self/stats.json.
# Fail-safe: any error -> exit 0, never blocks session end.
set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/retrospective.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit 0
