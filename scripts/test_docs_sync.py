#!/usr/bin/env python3
"""Self-check for scripts/docs-sync.py (v1.6.0 M6)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("ds", Path(__file__).parent / "docs-sync.py")
_ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ds)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


# .py change -> README + CHANGELOG sync
arts = _ds.artifacts_for(["app.py"])
check("py change -> README", any(a == "README.md" for a, _ in arts))
check("py change -> CHANGELOG", any(a == "CHANGELOG.md" for a, _ in arts))

# package.json change -> README + CHANGELOG
arts = _ds.artifacts_for(["package.json"])
check("package change -> README", any(a == "README.md" for a, _ in arts))

# ADR change -> architecture docs
arts = _ds.artifacts_for(["docs/architecture/ADR-002.md"])
check("ADR change -> architecture", any(a == "docs/architecture/" for a, _ in arts))

# plan change -> plan docs
arts = _ds.artifacts_for(["docs/PLAN-1.6.0.md"])
check("plan change -> plan", any(a == "docs/PLAN-*.md" for a, _ in arts))

# policy change -> AGENTS.md + CHANGELOG
arts = _ds.artifacts_for(["one-man.controls.json"])
check("policy change -> AGENTS", any(a == "AGENTS.md" for a, _ in arts))
check("policy change -> CHANGELOG", any(a == "CHANGELOG.md" for a, _ in arts))

# no relevant change -> no artifacts
check("unrelated change -> none", _ds.artifacts_for(["notes.txt"]) == [])

# dedupe: two py files -> README listed once
arts = _ds.artifacts_for(["a.py", "b.py"])
check("dedupe", sum(1 for a, _ in arts if a == "README.md") == 1)

print(f"OK: {PASS} assertions passed")
