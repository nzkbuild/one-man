#!/usr/bin/env python3
"""Self-check for review-gate.py — defect detection."""
import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

_spec = importlib.util.spec_from_file_location("rg", Path(__file__).parent / "review-gate.py")
_rg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rg)

sys.path.insert(0, str(Path(__file__).parent / "lib"))
import evidence as _ev  # noqa: E402 — local lib, path insert required

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def review(content, suffix=".py"):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"file{suffix}"
        p.write_text(content, encoding="utf-8")
        b, g = _rg.review_file(p, Path(f"file{suffix}"))
        return b, g


# blocking defects
b, _ = review("def f():\n    try:\n        x()\n    except:\n        pass\n")
check("bare except blocks", any("bare except" in x for x in b))

b, _ = review("def f():\n    pass  # TODO: finish this\n")
check("TODO blocks", any("TODO" in x for x in b))

# guides (non-blocking)
_, g = review("def f():\n    total = 12345 + 1\n    return total\n")
check("magic number guides", any("magic number" in x for x in g))

_, g = review("a = 1\nb = 2\nsame_thing(x, y)\nsame_thing(x, y)\nsame_thing(x, y)\n")
check("dup block guides", any("duplicated" in x for x in g))

# clean code: no findings
b, g = review("def add(a, b):\n    return a + b\n")
check("clean py silent", not b and not g)


# --- v1.5.0 M5: context-isolated review for high-risk ---
def run_gate(risk, evidence_list):
    """Run review-gate main() with a task record; return (exit, stderr).
    Points cwd at an EMPTY temp dir so the repo's own files never enter the
    scan — this test exercises the isolation logic only, not the repo review."""
    with tempfile.TemporaryDirectory() as tmp:
        _ev.EVIDENCE_DIR = Path(tmp)
        _ev.write_record("current", {"type": "bug", "risk": risk, "evidence": evidence_list})
        os.environ["HOOK_INPUT"] = json.dumps({"cwd": tmp})
        buf = io.StringIO()
        with redirect_stderr(buf):
            try:
                _rg.main()
                return 0, buf.getvalue()
            except SystemExit as e:
                return e.code, buf.getvalue()

# high-risk, no isolated review -> blocked
code, out = run_gate("high", [])
check("high-risk requires isolated review", code == 2)
check("isolation requested", "isolated review" in out)

# high-risk WITH isolated review evidence -> passes (no isolation block)
code, out = run_gate("high", [{"kind": "isolated_review", "result": "reviewed", "ts": 1}])
check("isolated review recorded passes", code == 0)

# low-risk -> no isolation requirement
code, out = run_gate("low", [])
check("low-risk no isolation needed", code == 0)

print(f"OK: {PASS} assertions passed")
