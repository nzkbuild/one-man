#!/usr/bin/env python3
"""Self-check for task-triage.py — classification + skill routing."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("tt", Path(__file__).parent / "task-triage.py")
_tt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tt)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def classify(prompt):
    return _tt.classify(prompt)[0]


# classification
check("bug", classify("the login is broken, getting 500 errors") == "bug")
check("feature", classify("add a dark mode toggle") == "feature")
check("refactor", classify("refactor the payment module") == "refactor")
check("question", classify("what does this function do?") == "question")
check("chore fallback", classify("just some minor stuff here") == "chore")
check("bug wins over feature", classify("add a fix for the crashing parser") == "bug")

# skills routing
flow = {"bug": ["systematic-debugging"], "feature": ["brainstorming", "writing-plans"], "default": ["pro-workflow"]}
check("bug routes to systematic-debugging", _tt.skills_for("bug", flow) == ["systematic-debugging"])
check("feature routes", _tt.skills_for("feature", flow) == ["brainstorming", "writing-plans"])
check("unknown routes to default", _tt.skills_for("weird", flow) == ["pro-workflow"])
check("missing flow -> empty", _tt.skills_for("bug", {}) == [])


# design routing via flow
flow_design = {"design": {"chain": ["brandkit", "design-taste-frontend", "minimalist-ui"]}}
check("design routes to chain", _tt.skills_for("design", flow_design) == ["brandkit", "design-taste-frontend", "minimalist-ui"])


# --- v1.5.0 M2: risk classification ---
check("payment bug is high", _tt.classify_risk("fix the payment bug", "bug") == "high")
check("auth change is high", _tt.classify_risk("update login token handling", "feature") == "high")
check("migration is high", _tt.classify_risk("write the data migration", "chore") == "high")
check("refactor is medium", _tt.classify_risk("refactor the module", "refactor") == "medium")
check("api change medium", _tt.classify_risk("change the api endpoint", "feature") == "medium")
check("docs typo low", _tt.classify_risk("fix typo in readme", "chore") == "low")
check("question low", _tt.classify_risk("what does this do?", "question") == "low")

print(f"OK: {PASS} assertions passed")
