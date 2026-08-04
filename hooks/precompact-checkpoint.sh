#!/usr/bin/env bash
# PreCompact hook — auto-saves compaction timestamp to STATE.md before context compaction.
# The post-compaction session sees this via session-context.py and knows where it left off.
#
# READ-ONLY (appends timestamp only). FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/precompact-checkpoint.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT" 2>/dev/null
exit 0
