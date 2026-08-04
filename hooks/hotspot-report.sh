#!/usr/bin/env bash
# SessionStart hook wrapper — hotspot-report.py (behavioral feedback).
set +e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT="$SCRIPT_DIR/hotspot-report.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT"
fi

exit 0
