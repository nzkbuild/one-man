#!/usr/bin/env python3
"""Self-check for retrospective.py — stats append + bounded + fail-open."""
import importlib.util
import json
import os
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retro", Path(__file__).parent / "retrospective.py")
_retro = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_retro)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def run_with(tmp, payload=None, existing=None):
    """Run main() against a temp HOME with optional existing stats.json."""
    # Point the module at the temp dir
    _retro.SELF_DIR = Path(tmp) / ".claude" / "self"
    _retro.STATS_FILE = _retro.SELF_DIR / "stats.json"
    if existing:
        _retro.SELF_DIR.mkdir(parents=True, exist_ok=True)
        _retro.STATS_FILE.write_text(json.dumps(existing), encoding="utf-8")
    os.environ["HOOK_INPUT"] = json.dumps(payload or {})
    try:
        _retro.main()  # exits via sys.exit(0) by design — catch it
    except SystemExit:
        pass


# 1. appends an entry
with tempfile.TemporaryDirectory() as tmp:
    run_with(tmp, {"cwd": tmp})
    stats = json.loads(_retro.STATS_FILE.read_text(encoding="utf-8"))
    check("appends entry", len(stats) == 1)
    check("entry has required keys",
          all(k in stats[0] for k in ("session_id", "date", "duration_min", "commits", "corrections")))

# 2. bounded at MAX_ENTRIES
with tempfile.TemporaryDirectory() as tmp:
    existing = [{"session_id": f"s{i}"} for i in range(_retro.MAX_ENTRIES)]
    run_with(tmp, {"cwd": tmp, "session_id": "new"}, existing=existing)
    stats = json.loads(_retro.STATS_FILE.read_text(encoding="utf-8"))
    check("bounded at MAX_ENTRIES", len(stats) == _retro.MAX_ENTRIES)
    check("newest present", stats[-1]["session_id"] == "new")

# 3. empty HOOK_INPUT still works (fail-open)
with tempfile.TemporaryDirectory() as tmp:
    os.environ["HOOK_INPUT"] = ""
    _retro.SELF_DIR = Path(tmp) / ".claude" / "self"
    _retro.STATS_FILE = _retro.SELF_DIR / "stats.json"
    try:
        _retro.main()  # exits via sys.exit(0) by design — catch it
    except SystemExit:
        pass
    check("empty input fail-open", True)

print(f"OK: {PASS} assertions passed")
