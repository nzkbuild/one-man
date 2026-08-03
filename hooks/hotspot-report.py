#!/usr/bin/env python3
"""SessionStart hook — behavioral feedback from session stats.

Reads ~/.claude/self/stats.json (written by retrospective) and surfaces the
signals that mean "the system should change", not just "here's what happened":

  - corrections clustering on one skill -> that skill misleads
  - long sessions, low output          -> scope drift
  - zero test files across sessions    -> test discipline slipping
  - repeated perf-guard hits on a file -> hotspot, refactor not patch
  - guard fired N+ times, no correction -> possibly noisy, consider tuning

Guide only (exit 0 + context). The human decides; this never auto-weaks.
READ-ONLY except nothing — never writes. Any error -> exit 0 silent.
"""
import json
import os
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
STATS_FILE = HOME / ".claude" / "self" / "stats.json"
LOOKBACK = 10  # last N sessions


def load_stats():
    try:
        if not STATS_FILE.exists():
            return []
        entries = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        return entries if isinstance(entries, list) else []
    except Exception:
        return []


def main():
    stats = load_stats()
    if not stats:
        sys.exit(0)

    recent = stats[-LOOKBACK:]
    lines = []

    # 1. Corrections cluster on one skill (future: prompt-guard feeds corrections)
    corr = [e for e in recent if e.get("corrections", 0) > 0]
    if len(corr) >= 3:
        lines.append(
            f"{len(corr)}/{len(recent)} sessions had corrections — if they cluster "
            "on one skill or rule, review it: a repeated correction is a process gap."
        )

    # 2. Long sessions, low output
    slow = [e for e in recent if e.get("duration_min", 0) > 90 and e.get("commits", 0) == 0]
    if len(slow) >= 2:
        lines.append(
            f"{len(slow)} sessions ran 90+ min with 0 commits — scope drift? "
            "Tighten task sizes; long sessions without output usually mean ambiguity."
        )

    # 3. Zero test files
    no_tests = [e for e in recent if e.get("files_touched_test", 0) == 0 and e.get("files_touched_src", 0) > 0]
    if len(no_tests) >= 3:
        lines.append(
            f"{len(no_tests)} sessions changed source with no test files — "
            "ship-gate will block 'done' over untested changes. Write tests with the code."
        )

    # 4. Guard noise signal (perf-guard hits without correction — placeholder
    #    until guards report their fire-count; the report structure is ready)
    if not lines:
        sys.exit(0)

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "# Hotspot report (from your last sessions)\n"
                             + "\n".join(f"- {ln}" for ln in lines),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
