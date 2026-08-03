#!/usr/bin/env python
"""UserPromptSubmit guard: detect corrections in the submitted prompt and, if found,
emit an additionalContext nudge telling Claude to capture the lesson via /self-evolve.

Reads the hook payload JSON from the HOOK_INPUT env var (the wrapper shell script
captures stdin into it, because a heredoc would otherwise occupy stdin). Prints
nothing on normal prompts. Never writes anything. Any error exits 0 silently.
"""
import json
import os
import re
import sys

raw = os.environ.get("HOOK_INPUT", "")
if not raw.strip():
    sys.exit(0)

try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

prompt = (data.get("prompt") or "").lower()
if not prompt.strip():
    sys.exit(0)

# Correction / frustration signals. Word-boundary matched to avoid false hits.
signals = [
    r"\bno,? (you|that|don'?t|stop|it'?s|again)\b",
    r"\bdon'?t do that\b",
    r"\byou forgot\b",
    r"\byou (keep|always|again)\b",
    r"\bthat'?s (wrong|not right|incorrect)\b",
    r"\bwrong\b",
    r"\bstop doing\b",
    r"\bi (told|already told) you\b",
    r"\bwhy did you\b",
    r"\bnot what i (asked|wanted|meant)\b",
    r"\bshould(n'?t| not) have\b",
]

if not any(re.search(p, prompt) for p in signals):
    sys.exit(0)

msg = (
    "The user's message looks like a correction. Before continuing: (1) fix the immediate "
    "issue, and (2) if there is a durable, generalizable lesson here, invoke /self-evolve "
    "to record it in ~/.claude/self/LESSONS.md so it persists to future sessions. "
    "Skip capture only if this is a one-off with no reusable rule."
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": msg,
    }
}))
