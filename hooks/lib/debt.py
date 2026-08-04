"""Technical debt register (v1.6.0 M4 — layer 8, policy output).

Debt is a POLICY OUTPUT, not a standalone feature: created automatically from
engineering findings (review-gate defects, ship-gate blocks, perf-guard hits),
classified, lifecycle-managed, expiring when stale.

Debt semantics:
  - auto-create on mechanical findings (bare except, TODO left, N+1)
  - advisory by default — never blocks alone
  - blocks ONLY at release when: acknowledged + unfixed + high-risk
  - expires after N releases with no action (stale debt auto-closes)

Lifecycle: open -> acknowledged -> fixed -> closed | expired
Stable ID: fingerprint of (file, finding-type) — dedupes repeat findings
  (recurrence detection: the same debt reappearing is a signal).

Local-only + bounded. Never ships.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
DEBT_DIR = HOME / ".claude" / "debt"
MAX_DEBT = 100
EXPIRE_RELEASES = 2  # releases without action -> expired

CLASSIFY = {
    "tech": ["bare except", "empty catch", "magic number"],
    "process": ["TODO left", "no tests", "commented-out"],
    "design": ["duplicated block", "N+1", "fetch-all"],
}


def _dir() -> Path:
    try:
        DEBT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return DEBT_DIR


def _stable_id(file: str, finding: str) -> str:
    norm = re.sub(r"[^a-z0-9]+", " ", f"{file} {finding}".lower()).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def classify(finding: str) -> str:
    f = finding.lower()
    for cls, keywords in CLASSIFY.items():
        if any(k.lower() in f for k in keywords):  # keywords may be mixed-case
            return cls
    return "tech"


def create(file: str, finding: str, severity: str = "medium",
           source: str = "review-gate") -> str:
    """Auto-create a debt entry from a finding. Returns the id or None."""
    try:
        did = _stable_id(file, finding)
        p = _dir() / f"{did}.json"
        if p.exists():  # recurrence: same debt reappearing — bump, don't dup
            d = json.loads(p.read_text(encoding="utf-8"))
            d["recurrences"] = d.get("recurrences", 1) + 1
            d["last_seen"] = time.time()
            p.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return did
        d = {
            "id": did, "status": "open", "file": file, "finding": finding,
            "classification": classify(finding), "severity": severity,
            "source": source, "created": time.time(), "last_seen": time.time(),
            "recurrences": 1, "releases_seen": 0, "acknowledged": False,
        }
        p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        _prune()
        return did
    except Exception:
        return None


def acknowledge(did: str) -> bool:
    return _update(did, {"acknowledged": True})


def fix(did: str) -> bool:
    return _update(did, {"status": "fixed", "fixed_at": time.time()})


def _update(did: str, changes: dict) -> bool:
    try:
        p = _dir() / f"{did}.json"
        if not p.exists():
            return False
        d = json.loads(p.read_text(encoding="utf-8"))
        d.update(changes)
        p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def expire_all(version: str):
    """Called at release: bump releases_seen; expire stale open debt."""
    try:
        for p in _dir().glob("*.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("status") == "open":
                d["releases_seen"] = d.get("releases_seen", 0) + 1
                if d["releases_seen"] >= EXPIRE_RELEASES:
                    d["status"] = "expired"
            p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass


def blocking_at_release() -> list:
    """Debt that blocks release: acknowledged + unfixed + high-risk."""
    out = []
    try:
        for p in _dir().glob("*.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            if (d.get("status") == "open" and d.get("acknowledged")
                    and d.get("severity") == "high"):
                out.append(d)
    except Exception:
        pass
    return out


def report() -> list:
    out = []
    try:
        for p in sorted(_dir().glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                out.append(f"[{d.get('status','?')}] {d.get('finding','?')} "
                           f"({d.get('file','?')}, {d.get('classification','?')}, "
                           f"x{d.get('recurrences',1)})")
            except Exception:
                continue
    except Exception:
        pass
    return out


def _prune():
    try:
        files = sorted(_dir().glob("*.json"), key=lambda p: p.stat().st_mtime)
        for old in files[:-MAX_DEBT]:
            old.unlink(missing_ok=True)
    except Exception:
        pass
