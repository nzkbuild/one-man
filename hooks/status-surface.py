#!/usr/bin/env python3
"""SessionStart hook — One Man status banner (the visible feedback surface).

The discipline harness is otherwise invisible: all guards inject hidden
additionalContext the model may ignore, and the user sees nothing. This hook
prints ONE compact branded banner at session start so the system's presence
and state are always visible.

Deliberately SMALL (the irony of a status hook bloating context is not lost):
a few lines, only the numbers that mean something. State is per-project
(scoped via state.py).

READ-ONLY. Fail-safe: any error -> exit 0 silent.
"""
import json
import sys
from pathlib import Path


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
        sys.exit(0)

    # hooks wired (count from settings wiring)
    n_guards = 0
    try:
        settings = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for _event, groups in settings.get("hooks", {}).items():
            for g in groups:
                n_guards += len(g.get("hooks", []))
    except Exception:
        pass

    # per-project state (open debt only)
    n_debt = 0
    try:
        for p in state_dir("debt").glob("*.json"):
            try:
                if json.loads(p.read_text(encoding="utf-8")).get("status") == "open":
                    n_debt += 1
            except Exception:
                continue
    except Exception:
        pass

    # fitness zombies (dead-weight policies)
    zombies = 0
    try:
        for p in state_dir("fitness").glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("applications", 0) == 0 and d.get("last_seen") is None:
                    zombies += 1
            except Exception:
                continue
    except Exception:
        pass

    # last gate outcome
    last_gate = "none"
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
        if newest:
            last_gate = f"{newest[1]}={newest[2]}"
    except Exception:
        pass

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": (
            f"## ⚔ One Man v{_version()} — engineering discipline active\n"
            f"- guards wired: {n_guards} | open debt: {n_debt} | "
            f"fitness zombies: {zombies} | last gate: {last_gate}\n"
            f"- statusline (bottom bar) shows live state; "
            f"a guard firing = a finding, not noise.\n"
        ),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
