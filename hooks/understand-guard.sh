#!/usr/bin/env bash
# PreToolUse hook wrapper — understand-guard.py (read-before-write nudge).
set +e

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/understand-guard.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT" 2>&1
fi

exit 0
