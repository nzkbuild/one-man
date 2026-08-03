"""Lesson ledger — the closed-loop learning memory (v1.5.1 M1).

A structured record of violations, failures, root causes, corrections, and
recurrence risk. Written by self-evolve; read by check-lessons (recurrence
detection) and session-context (filtered relevance digest).

The core rule: a lesson counts only when it is retrievable, applied at the
right time, and its recurrence prevention is tested where practical. Writing
a note is not learning.

Entry shape:
  {id, date, category, violation, root_cause, correction, layer,
   recurrence_risk: high|medium|low, tested: bool, test_ref: str|None,
   source: "local"|"seed"}

Layer decision (the correct home for each lesson):
  local-memory | claude-md | skill | hook | regression-test | ci-gate | none

Local-only + bounded (prune oldest). Never ships; the seed (repo) is the only
generic content, and it never overwrites user lessons.
"""
import json
import os
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LESSONS_DIR = HOME / ".claude" / "lessons"
MAX_LESSONS = 30


def _dir() -> Path:
    try:
        LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return LESSONS_DIR


def _slug(text: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]
    return s or "lesson"


def add(violation: str, root_cause: str, correction: str, layer: str,
        recurrence_risk: str = "medium", tested: bool = False,
        test_ref: str = None, category: str = "process", source: str = "local"):
    """Write one lesson entry. Returns the id or None on failure."""
    try:
        entry = {
            "id": _slug(violation),
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
        # update in place if same id (dedupe), else new file
        if p.exists():
            old = json.loads(p.read_text(encoding="utf-8"))
            old.update(entry)
            entry = old
        p.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        _prune()
        return entry["id"]
    except Exception:
        return None


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
