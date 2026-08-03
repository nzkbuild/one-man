#!/usr/bin/env bash
# UserPromptSubmit hook — detects milestone/shipping language and reminds me to run
# the drift audit. The user is a vibe coder: they should not have to know that a
# phase boundary is the right moment for a structural audit, so the harness spots it.
#
# READ-ONLY: reads the prompt, prints a nudge or nothing. Never runs the audit itself
# (too slow for a prompt hook, and the model should decide scope).
# FAIL-SAFE: any error -> exit 0, silent.

set +e

PY="$(command -v python || command -v python3 || true)"
[ -n "$PY" ] || exit 0

HOOK_INPUT="$(cat)"
export HOOK_INPUT

"$PY" - <<'PYEOF' 2>/dev/null
import json, os, re, sys

try:
    prompt = (json.loads(os.environ.get("HOOK_INPUT") or "{}").get("prompt") or "").lower()
except Exception:
    sys.exit(0)

if not prompt or len(prompt) > 2000:
    sys.exit(0)

# Phase/milestone completion, or a readiness question. Deliberately narrow: a false
# nudge on every prompt would be noise, and noise gets ignored.
PATTERNS = (
    r"\b(phase|milestone|sprint|version|v\d+\.\d+|m\d+|p\d+)\b.{0,24}\b(done|complete|finish|finished|ship|shipped|closed)\b",
    r"\b(done|complete|finished|wrapped)\b.{0,24}\b(phase|milestone|sprint|feature)\b",
    r"\b(ready to (ship|deploy|launch|release)|before (we )?(ship|deploy|launch|release))\b",
    r"\b(360|second (pass|audit)|2nd (pass|audit)|full audit|deep audit|final check)\b",
    # Apostrophes are frequently dropped in real typing ("whats missing"), so make
    # it optional rather than requiring the grammatical form.
    r"\bwhat'?s? (is )?(missing|broken|left|wrong)\b",
    r"\b(anything (missing|broken|wrong)|did we break|what did we break)\b",
    r"\bproduction ready\b",
)

if not any(re.search(p, prompt) for p in PATTERNS):
    sys.exit(0)

print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": (
        "This prompt marks a phase boundary or a readiness question — the moment the "
        "`audit` skill exists for. Invoke it (`python ~/.claude/skills/audit/audit.py`) "
        "to check for drift that per-file linters cannot see: unreachable code, "
        "duplicated concepts, infrastructure built but not wired, security settings "
        "declared in config but never enforced, and untested money/auth paths. "
        "Verify each finding against the real source before reporting it, and rank by "
        "consequence."
    ),
}}))
PYEOF

exit 0
