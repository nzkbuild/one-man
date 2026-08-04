#!/usr/bin/env bash
# UserPromptSubmit hook wrapper — classifies prompt, injects skill routing.
# Fail-safe: any error -> exit 0 silent.
set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/task-triage.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit 0
