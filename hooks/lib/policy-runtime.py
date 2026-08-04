"""Policy Runtime (v1.6.0 M3 — layer 7).

The single evaluator: consumes task classification, repository state,
engineering evidence, lessons, and the active policy versions, and produces a
deterministic execution plan (workflow, obligations, review requirement,
evidence requirement). It does NOT invent judgement — it evaluates the
versioned policies. It does NOT duplicate the gates — they execute the plan.

Parity contract (the migration safety net): for a given task record, the
runtime must produce the SAME verdicts the v1.5.x hooks produce today.
The parity test enforces this — if the runtime drifts from the hooks, the
test fails and the runtime is wrong, not the hooks.

Consumes:
  - policies: controls.json (criticality), flow.json (skill routing),
    obligations map (by task type)
  - evidence: the current task record (type, risk, obligations, evidence)
  - lessons: relevant past lessons (recurrence risk)

Produces:
  {type, risk, obligations, workflow, review_required, evidence_required,
   policy_version, skills}
"""
import json
import os
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
REPO = Path(__file__).parent.parent.parent

# ---- obligations: from the versioned policy file (one source of truth) ----

def _load_obligations():
    d = _load_policy("policies/obligations.json")
    return d.get("obligations", {})


# ---- workflow by risk (advisory output; gates enforce) ----
WORKFLOW = {
    "high": ["isolated-review", "evidence-gate", "ship-gate"],
    "medium": ["evidence-gate", "ship-gate"],
    "low": ["basic-verification"],
}

# ---- review requirement by risk (the review-gate's rule) ----
REVIEW_REQUIRED = {"high": "isolated", "medium": "standard", "low": None}


def _load_policy(name: str):
    try:
        p = REPO / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    try:
        p = HOME / ".claude" / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _load_controls():
    return _load_policy("one-man.controls.json")


def _load_flow():
    return _load_policy("skills.flow.json")


def evaluate(task_record: dict) -> dict:
    """Produce the deterministic execution plan for a task record.

    task_record: {type, risk, obligations?, evidence?, ...} — the v1.5.x
    evidence record shape.
    """
    ttype = task_record.get("type", "chore")
    risk = task_record.get("risk", "low")

    controls = _load_controls()
    flow = _load_flow()
    policy_version = controls.get("policy_version", "unknown")

    # obligations: from the policy file (one source of truth), or the record's own
    obligations = task_record.get("obligations") or _load_obligations().get(ttype, [])

    # skills: from flow routing (design chain unwrapped)
    route = flow.get(ttype, flow.get("default", []))
    if isinstance(route, dict) and "chain" in route:
        skills = route["chain"]
    else:
        skills = route

    # v1.6.0 F3 / v1.7.0 M1: fitness writer — record EACH policy evaluated
    # (per-policy telemetry, not one version-keyed blob).
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import fitness as _fit
        for pol in ("one-man.controls", "skills.flow", "obligations", "trust"):
            _fit.record(pol, "applied")
    except Exception:
        pass

    return {
        "type": ttype,
        "risk": risk,
        "obligations": obligations,
        "workflow": WORKFLOW.get(risk, WORKFLOW["low"]),
        "review_required": REVIEW_REQUIRED.get(risk),
        "evidence_required": risk in ("high", "medium"),
        "skills": skills,
        "policy_version": policy_version,
    }


if __name__ == "__main__":
    try:
        raw = os.environ.get("HOOK_INPUT", "")
        if raw.strip():
            record = json.loads(raw).get("task_record", {})
        else:
            record = {}
        plan = evaluate(record)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "# Policy runtime plan\n" + "\n".join(
                f"- {k}: {v}" for k, v in plan.items()),
        }}))
    except Exception:
        sys.exit(0)
