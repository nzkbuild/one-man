#!/usr/bin/env python3
"""SessionEnd hook — records session stats for the feedback loop.

Appends one entry per session to ~/.claude/self/stats.json:
  { session_id, date, duration_min, files_touched, commits, tests_added,
    corrections, skills_invoked }

READ-ONLY except stats.json append (the one deliberate write). Fail-safe: any
error -> exit 0, never blocks session end. The stats feed a future
hotspot-report (v1.3) — measurement is the missing half of the loop:
enforcement without measurement cannot improve.

Ponytail note: one small append, no daemon, no lock file. Concurrent sessions
may interleave a line — acceptable at single-user scale.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SELF_DIR = HOME / ".claude" / "self"
STATS_FILE = SELF_DIR / "stats.json"
MAX_ENTRIES = 500  # keep the file bounded; prune oldest


def read_payload():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _git_cmd(cwd: Path, args: list):
    """Bounded subprocess git call — never blocks session end (3s cap, no stdin)."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "-c", "core.pager=cat", "-C", str(cwd)] + args,
            capture_output=True, text=True, timeout=3,
            stdin=subprocess.DEVNULL,
        )
        return r.stdout or ""
    except Exception:
        return ""


def git_stats(cwd: Path):
    """Best-effort: commits + source/test files touched in this session."""
    commits = 0
    src = 0
    tests = 0
    try:
        out = _git_cmd(cwd, ["log", "--since=2 hours ago", "--oneline"])
        commits = len([ln for ln in out.splitlines() if ln.strip()])
    except Exception:
        pass
    try:
        out = _git_cmd(cwd, ["diff", "--name-only"])
        for f in out.splitlines():
            if re.search(r"(^|/)(test|tests)(/|_)|^test_", f):
                tests += 1
            elif f.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".rs")):
                src += 1
    except Exception:
        pass
    return commits, src, tests


def main():
    payload = read_payload()
    session_id = payload.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown")

    entry = {
        "session_id": session_id,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_min": round((payload.get("end_time") or time.time()) - (payload.get("start_time") or time.time()), 1),
        "commits": 0,  # git stats removed in v1.2.1 — SessionEnd hook must never block on git
        "corrections": 0,  # prompt-guard could feed this in a later version
        "skills_invoked": [],
    }

    try:
        SELF_DIR.mkdir(parents=True, exist_ok=True)
        entries = []
        if STATS_FILE.exists():
            try:
                entries = json.loads(STATS_FILE.read_text(encoding="utf-8"))
                if not isinstance(entries, list):
                    entries = []
            except Exception:
                entries = []
        entries.append(entry)
        entries = entries[-MAX_ENTRIES:]
        STATS_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except Exception:
        pass  # fail-open: never block session end over stats

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
