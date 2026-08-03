#!/usr/bin/env bash
# Stop hook wrapper — runs review-gate.py (automated code review).
# Captures stdin (HOOK_INPUT payload), calls the brain, propagates exit code.
set +e

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/review-gate.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  HOOK_INPUT="$INPUT" python "$SCRIPT" 2>&1
  EXIT=$?
  if [ "$EXIT" = "2" ]; then
    exit 2
  fi
fi

exit 0
