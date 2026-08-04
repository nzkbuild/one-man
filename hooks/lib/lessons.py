"""Lesson ledger — the closed-loop learning memory (v1.5.1 M1).

A structured record of violations, failures, root causes, corrections, and
recurrence risk. Written by self-evolve; read by check-lessons (recurrence
detection) and session-context (filtered relevance digest).

The core rule: a lesson counts only when it is retrievable, applied at the
right time, and its recurrence prevention is tested where practical. Writing
a note is not learning.

Entry shape:
  {id, status, date, category, violation, root_cause, correction, layer,
   recurrence_risk: high|medium|low, tested: bool, test_ref: str|None,
   source: "local"|"seed"}

Lesson LIFECYCLE (req 1 — a recorded note alone is NOT learned):
  observed   -> the violation happened (default on add)
  confirmed  -> root cause verified, not just hypothesized
  generalized-> the reusable rule is extracted (the correction)
  enforced   -> a mechanism (hook/test/CI/rule) now prevents it
  tested     -> the prevention has a runnable check that passes
  closed     -> enforced + tested + no recurrence in a window
  dismissed  -> no permanent action justified (one-off / not reusable)

  A lesson is "learned" only when it reaches enforced or tested, with a
  runnable check. The status field makes that explicit and auditable.

Layer decision (the correct home for each lesson):
  local-memory | claude-md | skill | hook | regression-test | ci-gate | none

Stable ID (req 2): sha1 of the normalized violation text — collision-stable
across re-writes and re-saves, independent of phrasing drift. Not free-text.

Local-only + bounded (prune oldest). Never ships; the seed (repo) is the only
generic content, and it never overwrites user lessons.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from state import migrate, state_dir

MAX_LESSONS = 30

# Lifecycle states, ordered. A lesson advances via set_status().
STATUSES = ("observed", "confirmed", "generalized", "enforced", "tested",
            "closed", "dismissed")


LESSONS_DIR = None  # test override; None -> per-project state dir


def _dir() -> Path:
    if LESSONS_DIR is not None:
        try:
            LESSONS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return LESSONS_DIR
    migrate("lessons", Path(os.path.expanduser("~")) / ".claude" / "lessons")
    d = state_dir("lessons")
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _stable_id(violation: str) -> str:
    """Stable fingerprint: sha1 of normalized violation text (req 2)."""
    import re
    norm = re.sub(r"[^a-z0-9]+", " ", violation.lower()).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def add(violation: str, root_cause: str, correction: str, layer: str,
        recurrence_risk: str = "medium", tested: bool = False,
        test_ref: str = None, category: str = "process", source: str = "local",
        status: str = "observed"):
    """Write one lesson entry. Returns the stable id or None on failure."""
    try:
        if status not in STATUSES:
            status = "observed"
        entry = {
            "id": _stable_id(violation),
            "status": status,
            "date": time.strftime("%Y-%m-%d"),
            "category": category,
            "violation": violation,
            "root_cause": root_cause,
            "correction": correction,
            "layer": layer,
            "recurrence_risk": recurrence_risk,
            "tested": tested,
            "test_ref": test_ref,
            "source": source,
        }
        p = _dir() / f"{entry['id']}.json"
        # update in place if same id (dedupe by stable fingerprint), else new
        if p.exists():
            old = json.loads(p.read_text(encoding="utf-8"))
            old.update(entry)
            entry = old
        p.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        _prune()
        return entry["id"]
    except Exception:
        return None


def set_status(lesson_id: str, status: str) -> bool:
    """Advance a lesson through the lifecycle. Returns True on success."""
    if status not in STATUSES:
        return False
    try:
        p = _dir() / f"{lesson_id}.json"
        if not p.exists():
            return False
        entry = json.loads(p.read_text(encoding="utf-8"))
        entry["status"] = status
        if status in ("enforced", "tested", "closed") and entry.get("test_ref"):
            entry["tested"] = True
        p.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def all_lessons():
    out = []
    try:
        for p in sorted(_dir().glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
    except Exception:
        pass
    return out


def high_risk_untested():
    """Lessons at recurrence risk whose prevention isn't tested."""
    return [les for les in all_lessons()
            if les.get("recurrence_risk") == "high" and not les.get("tested")]


def relevant(signals: str):
    """Filter lessons relevant to the current project's signals.

    signals: a lowercased string (repo name + language + risk words) to match
    against category + violation keywords. Keeps the SessionStart digest small
    (token discipline): only matching lessons, capped.
    """
    sig = (signals or "").lower()
    if not sig:
        return []
    out = []
    for les in all_lessons():
        hay = f"{les.get('category','')} {les.get('violation','')} {les.get('root_cause','')}".lower()
        if any(w in hay for w in sig.split()):
            out.append(les)
    return out[:5]  # cap the digest


def _prune():
    try:
        files = sorted(_dir().glob("*.json"), key=lambda p: p.stat().st_mtime)
        for old in files[:-MAX_LESSONS]:
            old.unlink(missing_ok=True)
    except Exception:
        pass
