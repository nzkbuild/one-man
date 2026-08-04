#!/usr/bin/env python3
"""Claude Code statusLine — One Man live harness state in the status bar.

Purpose: the discipline system must be VISIBLE, not assumed. Shows, for the
CURRENT project (scoped via state.py):
  debt N        — open technical-debt entries (0 = clean)
  fit X/Y       — policy fitness: healthy/watch (friction rising)
  gate RES      — last gate outcome (passed/blocked/none yet)
  ● ◐ ○         — overall state glyph: clean / watch / stalled

Branded with the One Man name + version (from one-man.controls.json — the
single source of truth; package.json mirrors it, readiness enforces parity).

Cheap: reads a few small JSON files, no subprocesses.
Wire-up (settings.json):
  "statusLine": {"type": "command", "command": "python C:/Users/<you>/.claude/hooks/statusline.py"}
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _version():
    """Version from the single source of truth, wherever it lives:
    repo controls -> installed controls -> package.json -> '?'."""
    cands = [
        Path(__file__).parent.parent / "one-man.controls.json",   # repo (dev)
        Path.home() / ".claude" / "one-man.controls.json",        # installed
        Path(__file__).parent.parent / "package.json",            # fallback
    ]
    for c in cands:
        try:
            if not c.exists():
                continue
            d = json.loads(c.read_text(encoding="utf-8"))
            v = d.get("version")
            if v:
                return v
        except Exception:
            continue
    return "?"


def main():
    try:
        sys.path.insert(0, str(Path(__file__).parent / "lib"))
        from state import state_dir
    except Exception:
        return

    state = "OK"
    parts = [f"ONE-MAN v{_version()}"]

    # debt (open only — closed/expired are history)
    try:
        debt = 0
        for p in state_dir("debt").glob("*.json"):
            try:
                if json.loads(p.read_text(encoding="utf-8")).get("status") == "open":
                    debt += 1
            except Exception:
                continue
    except Exception:
        debt = 0
    if debt:
        state = "DEBT"
    parts.append(f"debt {debt}")

    # fitness: healthy/watch counts (zombies are dead weight, surfaced separately)
    try:
        healthy = watch = 0
        for p in state_dir("fitness").glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            total = d.get("applications", 0) or 1
            friction = (d.get("overrides", 0) + d.get("false_positives", 0)) / total
            if friction > 0.3:
                watch += 1
            elif d.get("applications", 0) or d.get("last_seen"):
                healthy += 1
        if watch:
            state = "WATCH"
        parts.append(f"fit {healthy}H/{watch}W")
    except Exception:
        pass

    # last gate outcome
    try:
        newest = None
        for p in state_dir("evidence").glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                for e in d.get("evidence", []):
                    ts = e.get("ts", 0)
                    if ts and (newest is None or ts > newest[0]):
                        newest = (ts, e.get("kind", "?"), e.get("result", "?"))
            except Exception:
                continue
        if newest and newest[2] == "failed":
            state = "BLOCKED"
        parts.append(f"gate {newest[2] if newest else '—'}")
    except Exception:
        pass

    print(f"[{state}] {' · '.join(parts)}")


if __name__ == "__main__":
    main()
