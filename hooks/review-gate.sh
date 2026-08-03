#!/usr/bin/env bash
# Stop hook wrapper — runs review-gate.py (automated code review).
# Captures stdin (HOOK_INPUT payload), calls the brain, propagates exit code.
set +e

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/review-gate.py"
INPUT="$(cat)"

if [ -n "$INPUT" ]; then
  # stderr passes through (findings must reach the harness via stderr);
  # stdout is the JSON/context channel. Do NOT merge.
  HOOK_INPUT="$INPUT" python "$SCRIPT"
  EXIT=$?
  if [ "$EXIT" = "2" ]; then
    exit 2
  fi
fi

exit 0
