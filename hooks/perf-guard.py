#!/usr/bin/env python3
"""PostToolUse hook — perf anti-pattern nudges on changed code.

Catches the obvious inefficiencies top engineers never ship: N+1 (query in a
loop), O(n²) nested scans, unbounded pagination, sync I/O in hot paths.

Guide only (exit 0 + context) — perf is contextual; a nudge beats a block.
Scans files changed in the last 10 min. Any error -> exit 0.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

WINDOW_MIN = 10
SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build", ".next"}

# N+1: a DB/ORM call inside a loop — ONLY DB-ish signals, so regex loops,
# finditer, .get() on dicts, etc. do NOT false-fire. The lookahead must be a
# clear data-access primitive: .objects., .query, .execute, SELECT, findOne,
# findByPk, SELECT * — not generic get/find/all.
N_PLUS_1_PY = re.compile(
    r"(for\s+\w+\s+in\s+[\w.]+:.*?\n)(?=.*\b(?:objects\.|\.query|\.execute|SELECT\s|findByPk|findOne)\b)",
    re.DOTALL,
)
N_PLUS_1_JS = re.compile(
    r"(for\s+(?:const|let)\s+\w+\s+of\s+[\w.]+:?.*?\n)(?=.*\b(?:findByPk|findOne|SELECT\s|\.query|\.execute)\b)",
    re.DOTALL,
)
# O(n²): nested loop over the same collection
NESTED_SAME = re.compile(
    r"(for\s+(\w+)\s+in\s+(\w+):.*?for\s+\w+\s+in\s+\3:)", re.DOTALL
)
# Unbounded pagination / fetch-all
FETCH_ALL = re.compile(r"\b(findall|query_all|all\(\)|fetchall|objects\.all)\b")


def changed_files(cwd: Path):
    out = []
    now = time.time()
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            # Skip test files + this hook's own source: both legitimately
            # contain pattern strings as fixtures/declarations — scanning them
            # is guaranteed self-referential noise.
            if name.startswith("test_") or "_test." in name or name.endswith("_test.py"):
                continue
            if name.startswith(("perf-guard", "review-gate")):
                continue
            p = Path(root) / name
            if p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".rs"):
                try:
                    if now - p.stat().st_mtime < (WINDOW_MIN + 1) * 60:
                        out.append((p, p.relative_to(cwd)))
                except OSError:
                    pass
    return out


def review(p: Path, rel: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    notes = []
    if p.suffix == ".py" and N_PLUS_1_PY.search(text):
        notes.append(f"{rel}: N+1 pattern — DB call inside a loop. Batch with one query.")
    elif p.suffix in (".js", ".ts", ".tsx", ".jsx") and N_PLUS_1_JS.search(text):
        notes.append(f"{rel}: N+1 pattern — DB call inside a loop. Batch with one query.")
    if NESTED_SAME.search(text):
        notes.append(f"{rel}: nested loop over the same collection (O(n²)) — use a set/dict.")
    if FETCH_ALL.search(text):
        notes.append(f"{rel}: unbounded fetch-all — paginate or limit.")
    return notes


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    cwd = Path.cwd()
    if raw.strip():
        try:
            data = json.loads(raw)
            if data.get("cwd"):
                cwd = Path(data["cwd"])
        except Exception:
            pass

    notes = []
    for p, rel in changed_files(cwd):
        notes.extend(review(p, rel))

    if not notes:
        sys.exit(0)

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "# Perf guard\n" + "\n".join(f"- {n}" for n in notes[:6]),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
