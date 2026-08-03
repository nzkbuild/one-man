#!/usr/bin/env bash
# Stop hook wrapper — design-review.py (a11y + slop check for design turns).
set +e

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/design-review.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT"
  EXIT=$?
  if [ "$EXIT" = "2" ]; then
    exit 2
  fi
fi

exit 0
