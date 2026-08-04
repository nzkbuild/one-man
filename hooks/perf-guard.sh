#!/usr/bin/env bash
# PostToolUse hook wrapper — perf-guard.py (perf anti-pattern nudges).
set +e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/perf-guard.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT"
fi

exit 0
