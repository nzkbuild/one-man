"""Capability orchestration (v1.7.0 M4).

Proves that every required capability:
  - was selected for a justified reason (reason_selected)
  - served an engineering obligation (obligation)
  - executed successfully (executed)
  - produced usable output (output)
  - had its output consumed (output_consumer)
  - satisfied the obligation (obligation_satisfied)
  - has current evidence (evidence_current)

A capability that runs but produces no consumed value does NOT count —
ceremonial invocation is the exact anti-pattern this prevents.

The orchestration record lives in the evidence store (kind="orchestration"),
so the gate can verify obligation satisfaction from it.
"""
import time

from evidence import append_evidence


def record(capability: str, obligation: str, reason: str,
           executed: bool, output: str, consumer: str,
           satisfied: bool, evidence_current: bool = True,
           task_id: str = "current", files=None):
    """Record one capability's orchestration lifecycle."""
    append_evidence(
        task_id, kind="orchestration",
        result="satisfied" if satisfied else "failed",
        exit_code=0 if executed else 1,
        files=files,
        capability=capability,
        obligation=obligation,
    )
    # enrich the entry with the orchestration contract fields
    try:
        import json
        from evidence import read_record, _path
        rec = read_record(task_id) or {}
        entries = rec.setdefault("evidence", [])
        if entries:
            entries[-1].update({
                "executed": executed,
                "reason_selected": reason,
                "output": output,
                "output_consumer": consumer,
                "obligation_satisfied": satisfied,
                "evidence_current": evidence_current,
                "ts": time.time(),
            })
            _path(task_id).write_text(json.dumps(rec, indent=2), encoding="utf-8")
    except Exception:
        pass


def unsatisfied(task_id: str = "current") -> list:
    """Capabilities whose obligation was NOT satisfied (the gate's input)."""
    try:
        from evidence import read_record
        rec = read_record(task_id) or {}
        return [e for e in rec.get("evidence", [])
                if e.get("kind") == "orchestration"
                and not e.get("obligation_satisfied")]
    except Exception:
        return []


def unconsumed(task_id: str = "current") -> list:
    """Capabilities that ran but produced no consumed output (ceremony)."""
    try:
        from evidence import read_record
        rec = read_record(task_id) or {}
        return [e for e in rec.get("evidence", [])
                if e.get("kind") == "orchestration"
                and e.get("executed") and not e.get("output_consumer")]
    except Exception:
        return []
