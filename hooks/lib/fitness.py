"""Policy fitness telemetry (v1.6.0 M2 — layer 5).

Tracks meaningful engineering OUTCOMES per policy, not generic counters:
  applications  — times the policy was evaluated
  successes     — the policy produced a correct outcome (no override needed)
  regressions   — the policy's gate blocked something that later proved fine,
                  or a change to the policy caused a failure
  overrides     — the policy's output was overridden (friction signal)
  false_positives — the policy fired but the finding was wrong
  maintenance   — times the policy had to be edited to fix a problem

Fitness verdict (per policy):
  healthy   — low override/false-positive rate, recent activity
  watch     — rising friction (overrides/false-positives up)
  zombie    - no applications in N sessions - deprecation candidate

Constitution: engineering behaviour must never change silently. Fitness makes
policy health observable; a policy cannot silently rot.

Local-only + bounded. Never ships.
"""
import json
import os
import time
from pathlib import Path

from state import migrate, state_dir

ZOMBIE_SESSIONS = 10  # no applications for 10 sessions -> zombie
WATCH_RATE = 0.3      # override+false-positive rate above 30% -> watch


FITNESS_DIR = None  # test override; None -> per-project state dir


def _dir() -> Path:
    if FITNESS_DIR is not None:
        try:
            FITNESS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return FITNESS_DIR
    migrate("fitness", Path(os.path.expanduser("~")) / ".claude" / "fitness")
    d = state_dir("fitness")
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _path(policy: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in policy)[:60]
    return _dir() / f"{safe or 'policy'}.json"


def _read(policy: str):
    try:
        p = _path(policy)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"policy": policy, "applications": 0, "successes": 0,
            "regressions": 0, "overrides": 0, "false_positives": 0,
            "maintenance": 0, "last_seen": None}


def _write(policy: str, data: dict):
    try:
        _path(policy).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def record(policy: str, event: str):
    """Record one outcome event: applied|success|regression|override|false_positive|maintenance."""
    d = _read(policy)
    d["last_seen"] = time.time()
    if event == "applied":
        d["applications"] += 1
    elif event == "success":
        d["successes"] += 1
    elif event == "regression":
        d["regressions"] += 1
    elif event == "override":
        d["overrides"] += 1
    elif event == "false_positive":
        d["false_positives"] += 1
    elif event == "maintenance":
        d["maintenance"] += 1
    _write(policy, d)


def verdict(policy: str) -> str:
    """healthy | watch | zombie"""
    d = _read(policy)
    if d["applications"] == 0 and d["last_seen"] is None:
        return "zombie"
    if d["last_seen"] and (time.time() - d["last_seen"]) / 86400 > ZOMBIE_SESSIONS:
        return "zombie"
    total = d["applications"] or 1
    friction = (d["overrides"] + d["false_positives"]) / total
    if friction > WATCH_RATE:
        return "watch"
    return "healthy"


def report() -> list:
    """One-line per policy: name + verdict + friction rate.

    Includes policies that SHOULD have telemetry but never ran (zombies from
    the policy list) — an unrecorded policy is exactly the silent-rot signal
    fitness exists to surface, so it must appear even with no telemetry file.
    """
    out = []
    try:
        for p in sorted(_dir().glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                total = d.get("applications", 0) or 1
                friction = (d.get("overrides", 0) + d.get("false_positives", 0)) / total
                out.append(f"[{verdict(d['policy'])}] {d['policy']} "
                           f"(friction {friction:.0%}, apps {d.get('applications', 0)})")
            except Exception:
                continue
    except Exception:
        pass
    # policies that never produced telemetry are zombies by definition
    for pol in _known_policies():
        p = _path(pol)
        if not p.exists():
            out.append(f"[zombie] {pol} (no applications — deprecate or wire)")
    return out


def _known_policies() -> list:
    """The ACTUAL policy files that should have fitness telemetry — the
    versioned engineering policies only (policies/*.json + the root policy
    files). NOT every json in the repo (tsconfig, manifest are not policies)."""
    repo = Path(__file__).parent.parent.parent
    candidates = []
    try:
        candidates += [f.stem for f in (repo / "policies").glob("*.json")]
    except Exception:
        pass
    for name in ("one-man.controls", "skills.flow"):
        if (repo / f"{name}.json").exists():
            candidates.append(name)
    return candidates
