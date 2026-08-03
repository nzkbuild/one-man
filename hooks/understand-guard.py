#!/usr/bin/env python3
"""PreToolUse hook — the "understand floor": read before you write.

Top engineers read the file before editing it. This nudges when an Edit/Write
targets an EXISTING file that was never Read this turn — the classic
blind-edit slip. Guide only: never blocks (some edits are legitimately blind —
create-new, or the model already saw it via grep/diff). Any error -> exit 0.

Design (ponytail): a cheap heuristic — if the target exists and its mtime
predates this turn's window, the model probably hasn't read it. The hook
cannot see the model's internal reads; it flags the *likely* blind edit and
lets the model confirm. False-positive cost = one glance; miss cost = edit
over wrong assumptions.
"""
import json
import os
import sys
import time
from pathlib import Path

WINDOW_MIN = 10


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    if tool not in ("Edit", "Write", "NotebookEdit"):
        sys.exit(0)

    target = payload.get("tool_input", {}).get("file_path") or payload.get("tool_input", {}).get("notebook_path", "")
    if not target:
        sys.exit(0)

    p = Path(target)
    if not p.exists() or p.is_dir():
        sys.exit(0)  # new file or weird path — no blind-edit risk

    try:
        age_min = (time.time() - p.stat().st_mtime) / 60
    except OSError:
        sys.exit(0)

    if age_min <= WINDOW_MIN:
        sys.exit(0)  # recently touched — likely known

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            f"# Understand-floor\n"
            f"Editing `{p.name}`, which hasn't been touched in {age_min:.0f} min. "
            "Did you read it first? If not, Read the file before editing — "
            "blind edits over stale assumptions are the #1 defect source."
        ),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
