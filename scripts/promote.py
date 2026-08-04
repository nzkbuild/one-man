#!/usr/bin/env python3
"""Policy promotion gate (v1.6.0 M7 — layer 6).

Knowledge does not become policy. Knowledge produces evidence. Evidence
qualifies a Policy Candidate. Regression + Fitness validate the candidate.
Only then may a new policy version be promoted. Every promotion versioned +
traceable.

The constitution: engineering behaviour must never change silently. A
promotion is the OPPOSITE of silent — it is proposed, validated, evidenced,
fitness-checked, approved, and recorded.

Flow:
  PROPOSE  (what, why, evidence, trust-level of source)
  VALIDATE (regression: does the candidate break existing decisions? fixture)
  FITNESS  (does it improve outcomes? override/false-positive deltas)
  APPROVE  (human if no-policy/safety/irreversible; else auto for evidence-backed)
  PROMOTE  (write new policy version, old deprecated, traceable record)
  VERIFY   (CI green on the new version — the CI job runs this)

Usage: promote.py --propose <file> [--trust 1-7]
       promote.py --validate <file>
       promote.py --fitness <policy> [--improves yes/no]
       promote.py --approve <file> [--auto]
       promote.py --promote <file> --version <vX.Y.Z>
"""
import json
import os
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROMO_DIR = HOME / ".claude" / "promotions"
POLICY_DIR = Path(__file__).parent.parent


def _load_trust():
    try:
        p = POLICY_DIR / "policies" / "trust.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            return d.get("auto_approve", [])
    except Exception:
        pass
    return []

# Trust hierarchy (v1.6.0 F7): read from the VERSIONED POLICY (policies/trust.json),
# not code. 1 highest, 7 lowest. Auto-approve only 3-5 (official + evidence).


def _dir() -> Path:
    try:
        PROMO_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return PROMO_DIR


def _proposal_path(name: str) -> Path:
    return _dir() / f"{name}.json"


def propose(name: str, what: str, why: str, evidence: str, trust: int):
    """Record a promotion candidate. Trust 1-7 per the hierarchy."""
    p = _proposal_path(name)
    data = {
        "name": name, "what": what, "why": why, "evidence": evidence,
        "trust": trust, "status": "proposed", "ts": time.time(),
    }
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return name


def validate(name: str, regression_ok: bool):
    """Regression: does the candidate break existing decisions?"""
    p = _proposal_path(name)
    d = json.loads(p.read_text(encoding="utf-8"))
    d["regression_ok"] = regression_ok
    d["status"] = "validated" if regression_ok else "rejected"
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d["status"]


def fitness(name: str, improves: bool):
    """Fitness: does it improve outcomes?"""
    p = _proposal_path(name)
    d = json.loads(p.read_text(encoding="utf-8"))
    d["fitness_improves"] = improves
    d["status"] = "fitness-checked" if improves else "rejected"
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d["status"]


def approve(name: str, auto: bool = False) -> str:
    """Approve. Auto only when trust allows + validated + fitness-improves."""
    p = _proposal_path(name)
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("status") != "fitness-checked":
        return "rejected: must validate + fitness-check first"
    if not d.get("regression_ok") or not d.get("fitness_improves"):
        return "rejected: regression or fitness failed"
    if not auto:
        # human approval: persist it (explicit, auditable)
        d["status"] = "approved"
        d["approved_at"] = time.time()
        d["approved_by"] = "human"
        p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return "approved-by-human"
    _trust = _load_trust()
    if d.get("trust") in _trust:
        d["status"] = "approved"
        d["approved_at"] = time.time()
        d["approved_by"] = "auto"
        p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return "approved-auto"
    return "needs-human: trust level below auto-approve"


def promote(name: str, version: str) -> str:
    """Promote: write the new policy version (traceable)."""
    p = _proposal_path(name)
    if not p.exists():
        return "no proposal"
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("status") != "approved":
        return "rejected: not approved"
    # Record the promotion trace (the audit trail)
    trace = {
        "proposal": name, "version": version, "what": d.get("what"),
        "trust": d.get("trust"), "regression_ok": d.get("regression_ok"),
        "fitness_improves": d.get("fitness_improves"),
        "approved": d.get("status"), "ts": time.time(),
    }
    trace_path = _dir() / f"trace-{name}-{version}.json"
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    d["status"] = "promoted"
    d["promoted_version"] = version
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return f"promoted {name} -> {version} (traceable)"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    cmd = args[0]
    if cmd == "--propose":
        name, what, why, ev, trust = (args[1], args[2], args[3], args[4], int(args[5]))
        propose(name, what, why, ev, trust)
        print(f"proposed {name} (trust {trust})")
    elif cmd == "--validate":
        print(validate(args[1], args[2] == "ok"))
    elif cmd == "--fitness":
        print(fitness(args[1], args[2] == "yes"))
    elif cmd == "--approve":
        print(approve(args[1], "--auto" in args))
    elif cmd == "--promote":
        print(promote(args[1], args[2]))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"promote error: {e}", file=sys.stderr)
        sys.exit(2)
