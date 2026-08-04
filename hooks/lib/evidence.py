"""Per-task evidence store — the v1.5.0 evidence backbone.

One artifact, `~/.claude/evidence/<task_id>.json` (JSONL, bounded), written by
the hooks that already run. The completion gate (M4) reads it to prove an
engineering obligation was satisfied against the CURRENT code state.

Record shape:
  {task_id, created, type, risk, obligations: [str],
   evidence: [{kind, result, exit_code, files, state_hash, ts}],
   completed: false}

State hashing (staleness): hash the content of the files a piece of evidence
applies to. At gate time, re-hash; if any file differs, the evidence is stale
(the code moved on after verification).

Fail-open: any error -> no write, no block. Privacy: local only, never ships.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from state import migrate, state_dir

MAX_RECORDS = 200


EVIDENCE_DIR = None  # test override; None -> per-project state dir


def _dir() -> Path:
    if EVIDENCE_DIR is not None:
        try:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return EVIDENCE_DIR
    migrate("evidence", Path(os.path.expanduser("~")) / ".claude" / "evidence")
    d = state_dir("evidence")
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _path(task_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_id)[:80]
    return _dir() / f"{safe or 'task'}.json"


def state_hash(files) -> str:
    """Hash the content of the given files — the code state evidence applies to."""
    h = hashlib.sha256()
    if isinstance(files, str):
        files = [files]
    for f in files or []:
        try:
            p = Path(f)
            if p.exists():
                h.update(p.read_bytes())
        except Exception:
            pass
    return h.hexdigest()[:16]


def write_record(task_id: str, data: dict):
    """Create/overwrite a task record (task-triage: type/risk/obligations)."""
    try:
        rec = read_record(task_id) or {}
        rec.update(data)
        rec.setdefault("created", time.time())
        rec.setdefault("evidence", [])
        rec.setdefault("completed", False)
        _path(task_id).write_text(json.dumps(rec, indent=2), encoding="utf-8")
        _prune()
    except Exception:
        pass


def append_evidence(task_id: str, kind: str, result: str, exit_code=None, files=None,
                    capability=None, obligation=None):
    """Append one evidence entry (verify-turn: test result; review-gate: findings).

    v1.7.0 M2: capability + obligation tie the evidence to WHICH engineering
    capability satisfied WHICH obligation — proof of obligation, not invocation.
    """
    try:
        rec = read_record(task_id) or {}
        rec.setdefault("evidence", [])
        entry = {
            "kind": kind,
            "result": result,
            "exit_code": exit_code,
            "files": list(files) if files else [],
            "state_hash": state_hash(files),
            "ts": time.time(),
        }
        if capability:
            entry["capability"] = capability
        if obligation:
            entry["obligation"] = obligation
        rec["evidence"].append(entry)
        rec.setdefault("created", time.time())
        rec.setdefault("completed", False)
        _path(task_id).write_text(json.dumps(rec, indent=2), encoding="utf-8")
        _prune()
    except Exception:
        pass


def read_record(task_id: str):
    try:
        p = _path(task_id)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _prune():
    """Keep the store bounded (oldest records dropped)."""
    try:
        files = sorted(_dir().glob("*.json"), key=lambda p: p.stat().st_mtime)
        for old in files[:-MAX_RECORDS]:
            old.unlink(missing_ok=True)
    except Exception:
        pass
