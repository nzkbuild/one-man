#!/usr/bin/env bash
# SessionStart hook — verifies hook scripts exist and are parseable.
# Runs after session-context.sh so the model sees findings on prompt one.
#
# FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/hook-health.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT" 2>/dev/null
exit 0
