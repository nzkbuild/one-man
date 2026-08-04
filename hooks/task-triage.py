#!/usr/bin/env python3
"""UserPromptSubmit hook — classifies the prompt and injects the right briefing.

The ORCHESTRATOR of systematic skill reuse. Classifies every prompt as
bug/feature/refactor/question/chore, then injects as additionalContext:
  - the task type + one-line reason
  - which skills to invoke (from skills.flow.json, when present)
  - pre-mortem (edge cases the type normally trips on)
  - exit criteria (what "done" must satisfy)

Guide only — never blocks. Rough 2s budget: single regex pass over the prompt,
no I/O beyond reading the flow manifest. Any error -> exit 0 silent.

Design (ponytail): deliberately narrow keyword set. False positive on every
prompt would be noise; missed classifications fall back to a generic briefing.
"""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
FLOW_MANIFEST = HOME / ".claude" / "skills.flow.json"

# (type, patterns, pre-mortem, exit_criteria)
TASKS = [
    (
        "bug",
        [r"\b(bug|broken|crash\w*|error|fails?|wrong|not working|regression|500|exception)\b"],
        "Pre-mortem: reproduce first, read the error, find root cause not symptom, "
        "check all callers of the touched function, add a regression test.",
        "Exit: bug reproduced, root cause found, fix verified by a test that failed before.",
    ),
    (
        "feature",
        [r"\b(add|build|create|implement|new|feature|support|let me|make it|should (do|have|work))\b"],
        "Pre-mortem: empty/edge inputs, auth, concurrency, idempotency (double-click), "
        "backward compat, performance at scale.",
        "Exit: works end-to-end, edge cases handled, tests for the unhappy path, no regressions.",
    ),
    (
        "refactor",
        [r"\b(refactor|clean up|simplify|restructure|rewrite|dedupe|rename|move)\b"],
        "Pre-mortem: behavior must not change; tests are the safety net; small diffs; "
        "no unrelated rewrites.",
        "Exit: same behavior (tests green), smaller/cleaner, no unrelated changes.",
    ),
    (
        "question",
        [r"\b(what|how|why|explain|understand|difference|compare|which|does it)\b.*\?"],
        "Pre-mortem: answer from evidence (read the code), not assumption; state what "
        "was checked and what wasn't.",
        "Exit: accurate answer with evidence, limitations stated.",
    ),
    (
        "chore",
        [r"\b(install|update|upgrade|bump|migrate|deploy|release|backup|cleanup)\b"],
        "Pre-mortem: backup/rollback path first, verify after, no silent behavior change.",
        "Exit: change applied, verified, reversible.",
    ),
    (
        "design",
        [r"\b(design|ui|ux|interface|layout|page|component|visual|styling|frontend|mobile app)\b"],
        "Pre-mortem: run the design skill chain (brandkit -> design-taste -> "
        "minimalist-ui); real users, real content, a11y (WCAG 2.2 AA), no generic "
        "AI-looking output.",
        "Exit: design follows the chain, a11y checked, no generic slop.",
    ),
]


# ---- Risk classification (v1.5.0 M2) ----
# High-risk surfaces: money, auth, security, data, concurrency, crypto,
# migrations. A change touching these escalates scrutiny (evidence gate,
# isolated review). Low-risk: docs/typos/no behavior change. Everything else
# medium. Risk is advisory context — it drives the gates, not a block itself.
HIGH_RISK = re.compile(
    r"\b(auth|login|password|token|session|payment|checkout|billing|invoice|"
    r"security|vulnerab|inject|ssl|tls|crypto|encrypt|decrypt|hash|"
    r"migration|migrate|schema|concurren|race|deadlock|lock|"
    r"money|balance|transaction|refund|charge|sensitive|pii|gdpr)\b",
    re.IGNORECASE,
)
MEDIUM_RISK = re.compile(
    r"\b(api|endpoint|refactor|restructure|rewrite|multi-file|schema change|"
    r"database|db |sql|index|deploy|rollback|public|contract|version|"
    r"break|compatib)\b",
    re.IGNORECASE,
)


def classify_risk(prompt: str, task_type: str) -> str:
    """Return high|medium|low from the prompt + task type.

    High-risk signals dominate (a payment bug is high even as a 'bug').
    Medium falls back to task type (refactor/feature are inherently medium+).
    """
    if HIGH_RISK.search(prompt):
        return "high"
    if MEDIUM_RISK.search(prompt) or task_type in ("refactor", "feature"):
        return "medium"
    return "low"


def load_flow():
    """Read skills.flow.json if present — the trigger->skill routing table."""
    try:
        if FLOW_MANIFEST.exists():
            return json.loads(FLOW_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def classify(prompt: str):
    """Return (task_type, reason) — first matching task wins, else chore."""
    import re
    for ttype, patterns, _, _ in TASKS:
        for pat in patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                return ttype, pat
    return "chore", "no strong signal"


def skills_for(ttype: str, flow: dict):
    """Look up the skill route for this task type from the flow manifest.
    A design-style entry stores its route under 'chain' — unwrap it."""
    route = flow.get(ttype, flow.get("default", []))
    if isinstance(route, dict) and "chain" in route:
        return route["chain"]
    return route


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)
    prompt = (payload.get("prompt") or "").strip()
    if not prompt or len(prompt) > 2000:
        sys.exit(0)

    ttype, reason = classify(prompt)
    risk = classify_risk(prompt, ttype)
    # v1.7.0 M1: situation recognition (context, not just type)
    try:
        sys.path.insert(0, str(Path(__file__).parent / "lib"))
        import situations as _sit
        _sit_class = _sit.classify_situation(prompt, _sit.repo_state(Path.cwd()))
    except Exception:
        _sit_class = "brownfield"
    flow = load_flow()
    skills = skills_for(ttype, flow)

    # v1.6.0 F1/F2: the Policy Runtime evaluates (obligations/workflow from the
    # versioned policies); task-triage feeds it the classification. One source
    # of truth for obligations = policies/obligations.json (not code).
    try:
        sys.path.insert(0, str(Path(__file__).parent / "lib"))
        import evidence as _ev
        import policy_runtime as _pr
        plan = _pr.evaluate({"type": ttype, "risk": risk, "situation": _sit_class})
        _ev.write_record("current", {
            "type": ttype, "risk": risk,
            "obligations": plan["obligations"],
            "policy_version": plan["policy_version"],
            "workflow": plan["workflow"],
            "review_required": plan["review_required"],
        })
        # v1.6.0 F8: the decision record IS the observability trace.
        _ev.append_evidence("current", "policy_runtime",
                            f"plan: {plan['workflow']} review={plan['review_required']}",
                            exit_code=0)
    except Exception:
        pass

    # Pull pre-mortem + exit criteria for this type
    premortem = ""
    exit_criteria = ""
    for t, patterns, pm, ex in TASKS:
        if t == ttype:
            premortem, exit_criteria = pm, ex
            break

    lines = [
        "# Task triage (2s)",
        f"Type: {ttype}  (matched: {reason})",
        f"Risk: {risk}",
        f"Situation: {_sit_class}",
    ]
    if skills:
        lines.append(f"Skills to invoke: {', '.join(skills)}")
    if premortem:
        lines.append(f"Pre-mortem: {premortem}")
    if exit_criteria:
        lines.append(f"Exit criteria: {exit_criteria}")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "\n".join(lines),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
