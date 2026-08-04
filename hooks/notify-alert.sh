#!/usr/bin/env bash
# Notification hook — alerts on background task completion.
#
# FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/notify-alert.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit $?
