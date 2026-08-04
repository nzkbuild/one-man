"""Controlled re-planning (v1.7.0 M6).

Re-plan ONLY when verified evidence changes assumptions, feasibility, risks,
dependencies, scope, or implementation order. Records:
  - what changed
  - why it changed
  - evidence that triggered it
  - affected milestones
  - whether completed work remains valid
  - which previous evidence became stale
  - the new dependency order

Prevents silent plan drift AND unnecessary repeated planning. A plan does
not change because the AI "feels like it" — it changes when verified
evidence demands it.

The re-plan record lives in the evidence store (kind="replan"), so the
change is auditable.
"""
import time

from evidence import append_evidence


def replan(trigger_evidence: str, what_changed: str, why: str,
           affected_milestones: list, completed_valid: bool,
           stale_evidence: list, new_order: list,
           task_id: str = "current") -> None:
    """Record a controlled re-plan. Returns nothing; the record is the audit."""
    append_evidence(
        task_id, kind="replan",
        result="replanned" if completed_valid else "replanned-invalidating",
        exit_code=0,
        capability="replan",
        obligation="re-plan only on verified evidence change",
    )
    try:
        import json
        from evidence import read_record, _path
        rec = read_record(task_id) or {}
        entries = rec.setdefault("evidence", [])
        if entries:
            entries[-1].update({
                "trigger_evidence": trigger_evidence,
                "what_changed": what_changed,
                "why": why,
                "affected_milestones": affected_milestones,
                "completed_work_valid": completed_valid,
                "stale_evidence": stale_evidence,
                "new_dependency_order": new_order,
                "ts": time.time(),
            })
            _path(task_id).write_text(json.dumps(rec, indent=2), encoding="utf-8")
    except Exception:
        pass


def replans(task_id: str = "current") -> list:
    """All re-plan records (the audit trail)."""
    try:
        from evidence import read_record
        rec = read_record(task_id) or {}
        return [e for e in rec.get("evidence", []) if e.get("kind") == "replan"]
    except Exception:
        return []
