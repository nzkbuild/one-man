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
    flow = load_flow()
    skills = skills_for(ttype, flow)

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
