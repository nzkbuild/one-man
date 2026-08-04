#!/usr/bin/env bash
# PreToolUse hook wrapper — understand-guard.py (read-before-write nudge).
set +e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/understand-guard.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT"
fi

exit 0
