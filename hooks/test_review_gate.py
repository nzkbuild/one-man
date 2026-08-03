#!/usr/bin/env python3
"""Self-check for review-gate.py — defect detection."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("rg", Path(__file__).parent / "review-gate.py")
_rg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rg)

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

print(f"OK: {PASS} assertions passed")
