#!/usr/bin/env bash
# SubagentStop hook — flags subagent failures and trivial outputs.
#
# FAIL-SAFE: any error → exit 0.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

SCRIPT="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/subagent-guard.py"
[ -f "$SCRIPT" ] || exit 0

"$PY" "$SCRIPT"
exit $?
