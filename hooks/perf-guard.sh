#!/usr/bin/env bash
# PostToolUse hook wrapper — perf-guard.py (perf anti-pattern nudges).
set +e

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/perf-guard.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT" 2>&1
fi

exit 0
