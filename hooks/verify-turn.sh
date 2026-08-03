#!/usr/bin/env bash
# Stop hook — runs the project's existing test suite when a turn ends, so "done" is
# never claimed over a red suite. Mechanical enforcement of protocol rule #3.
#
# Only runs a suite the project ALREADY has, and only if source files changed in this
# session's recent window. Never installs anything, never writes to the project.
# FAIL-SAFE: no runner, no tests, or a timeout -> exit 0, silent.
#
# Feedback channel: exit 2 + stderr is what reaches the model (plain stdout does not).

set +e

# Guard against recursion: if a nested agent already ran this, don't run it again.
[ -n "$CLAUDE_VERIFY_TURN_RUNNING" ] && exit 0
export CLAUDE_VERIFY_TURN_RUNNING=1

# Nothing to verify if no source file was touched recently (cheap proxy for "code changed").
CHANGED=0
for f in $(find . -maxdepth 3 \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' \) \
            -newermt '-10 minutes' -not -path './node_modules/*' -not -path './venv/*' \
            -not -path './.git/*' 2>/dev/null | head -1); do
  CHANGED=1
done
[ "$CHANGED" = "1" ] || exit 0

OUT=""
FAILED=0

# Prefer the project's own interpreter.
PY_PROJ=""
for cand in "$VIRTUAL_ENV/Scripts/python.exe" "$VIRTUAL_ENV/bin/python" \
            "venv/Scripts/python.exe" "venv/bin/python" \
            ".venv/Scripts/python.exe" ".venv/bin/python"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then PY_PROJ="$cand"; break; fi
done
[ -n "$PY_PROJ" ] || PY_PROJ="$(command -v python || command -v python3 || true)"

if [ -d tests ] || ls test_*.py >/dev/null 2>&1; then
  if [ -n "$PY_PROJ" ] && "$PY_PROJ" -c 'import pytest' >/dev/null 2>&1; then
    OUT="$(timeout 120 "$PY_PROJ" -m pytest -q --no-header 2>&1 | tail -25)"
    case "$OUT" in
      *failed*|*error*|*Error*) FAILED=1 ;;
    esac
  fi
elif [ -f package.json ]; then
  if grep -q '"test"' package.json 2>/dev/null && \
     ! grep -q 'no test specified' package.json 2>/dev/null; then
    # pnpm first — pnpm-lock.yaml is authoritative on pnpm repos
    if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
      OUT="$(timeout 120 pnpm test --silent 2>&1 | tail -25)"
    elif command -v npm >/dev/null 2>&1; then
      OUT="$(timeout 120 npm test --silent 2>&1 | tail -25)"
    fi
    case "$OUT" in
      *failing*|*FAIL*|*failed*|*error*|*Error*) FAILED=1 ;;
    esac
  fi
fi

if [ "$FAILED" = "1" ]; then
  printf 'Tests are FAILING. Do not report this work as done — fix these first:\n%s\n' \
    "$OUT" >&2
  exit 2
fi

# Ship-gate (second half of the Verify-turn gate): scan changed source for
# TODO/FIXME, console.log/debugger, commented-out code, empty catches. Red test
# suite can't see these. Exit 2 if any are found. Fail-safe: any error -> exit 0.
SG="$( cd "${BASH_SOURCE[0]%/*}" && pwd )/ship-gate.py"
if [ -n "$PY" ] && [ -f "$SG" ]; then
  "$PY" "$SG" <<< "$HOOK_INPUT" 2>&1
  SHIP_EXIT=$?
  if [ "$SHIP_EXIT" = "2" ]; then
    exit 2
  fi
fi

exit 0
