#!/usr/bin/env bash
# PostToolUse hook — mechanical anti-slop gate. After any file write/edit, lint the
# file that was just touched and report problems back to the model as feedback.
#
# Why: catching a broken edit mechanically beats hoping the model notices. The model
# sees this output as tool feedback and fixes it in the same turn, before the user
# ever sees the breakage.
#
# READ-ONLY on your project: only ever runs linters. Never writes or fixes files.
# FAIL-SAFE: missing tool, unknown extension, or any error -> exit 0, silent.
#
# Input  (stdin): JSON hook payload with .tool_input.file_path
# Output (stdout): plain text findings, or nothing when clean.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

FILE="$("$PY" -c '
import json, os, sys
try:
    d = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    print((d.get("tool_input") or {}).get("file_path") or "")
except Exception:
    pass
' 2>/dev/null)"

[ -n "$FILE" ] || exit 0

# The harness hands us native Windows paths (C:\Users\...), which this shell's
# `test -f` and the linters cannot resolve. Convert to a POSIX path before use.
case "$FILE" in
  [A-Za-z]:\\*|[A-Za-z]:/*)
    if command -v cygpath >/dev/null 2>&1; then
      FILE="$(cygpath -u "$FILE" 2>/dev/null)"
    else
      # Fallback: C:\a\b -> /c/a/b
      FILE="$(printf '%s' "$FILE" | sed 's|\\|/|g; s|^\([A-Za-z]\):|/\L\1|')"
    fi
    ;;
esac

[ -f "$FILE" ] || exit 0

OUT=""
case "$FILE" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      OUT="$(ruff check --quiet "$FILE" 2>&1)"
    fi
    # Type checking catches the class of bug linting and green tests both miss:
    # "this value can be None here". Only report errors, and only when the project
    # opts in via a mypy config — otherwise an unannotated codebase floods us.
    if command -v mypy >/dev/null 2>&1 && \
       { [ -f pyproject.toml ] && grep -q '\[tool.mypy\]' pyproject.toml 2>/dev/null; } || \
       [ -f mypy.ini ] 2>/dev/null; then
      TY="$(timeout 60 mypy "$FILE" --no-error-summary --no-pretty 2>/dev/null \
            | grep ': error:' | head -10)"
      [ -n "$TY" ] && OUT="$(printf '%s\n%s' "$OUT" "$TY")"
    fi
    ;;
  *.ts|*.tsx|*.js|*.jsx)
    # Only when the project actually has eslint wired up; never installs anything.
    if [ -f package.json ] && command -v npx >/dev/null 2>&1; then
      OUT="$(npx --no-install eslint "$FILE" 2>/dev/null)"
    fi
    ;;
  *.rs)
    # Cheap syntax-only parse; a full `cargo check` is too slow for a per-edit hook.
    command -v rustfmt >/dev/null 2>&1 && OUT="$(rustfmt --check --edition 2021 "$FILE" 2>&1 | head -20)"
    ;;
esac

# Feedback channel: for PostToolUse, stdout on exit 0 lands in the transcript but is
# NOT shown to the model. Exit code 2 sends stderr back to the model as actionable
# feedback, which is the whole point of this hook. Silence + exit 0 when clean.
# Trimmed so hook feedback never becomes its own context tax.
if [ -n "$OUT" ]; then
  printf 'Lint findings in %s — fix these before reporting done:\n%s\n' \
    "$FILE" "$(printf '%s' "$OUT" | head -30)" >&2
  exit 2
fi

exit 0
