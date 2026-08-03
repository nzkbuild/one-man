#!/usr/bin/env python3
"""check-lessons.py — recurrence detection for the lesson ledger (v1.5.1 M2).

Scans ~/.claude/lessons/ for:
  1. recurrence_risk=high lessons whose prevention isn't tested -> they WILL
     recur silently; surface them.
  2. tested=true lessons whose test/check is missing or broken -> the
     prevention no longer holds.

Exit 2 when at-risk lessons exist (CI + SessionStart surface it); exit 0
silent when clean. Any error -> exit 0 (fail-open; a broken ledger must not
block a session).

Verification of "tested": the test_ref must resolve to an existing file.
Deep verification (does the test pass) is CI's job — this checks presence.
"""
import json
import os
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LESSONS_DIR = HOME / ".claude" / "lessons"


def _find(rel: str) -> bool:
    """Resolve a test_ref relative to common roots (repo, hooks, lib)."""
    if not rel:
        return False
    for root in (Path.cwd(), HOME / ".claude" / "hooks",
                 HOME / ".claude" / "hooks" / "lib",
                 HOME / "Coding" / "one-man"):
        if (root / rel).exists():
            return True
    return False


def check():
    if not LESSONS_DIR.exists():
        return []
    # Lifecycle: a lesson is "learned" only at enforced/tested/closed.
    # observed/confirmed/generalized = recorded but NOT yet prevented.
    LEARNED = {"enforced", "tested", "closed"}
    problems = []
    for p in sorted(LESSONS_DIR.glob("*.json")):
        try:
            les = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = les.get("status", "observed")
        if les.get("recurrence_risk") == "high" and status not in LEARNED:
            problems.append(f"at-risk NOT learned: {les.get('violation','?')} "
                            f"(status={status}, layer={les.get('layer','?')}) — it will recur silently")
        if status in LEARNED and les.get("test_ref") and not _find(les["test_ref"]):
            problems.append(f"prevention broken: {les.get('violation','?')} — "
                            f"test_ref {les['test_ref']} not found")
    return problems


def main():
    problems = check()
    if not problems:
        sys.exit(0)
    print("## Lesson ledger — recurrence risk:\n" +
          "\n".join(f"- {p}" for p in problems[:8]), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
