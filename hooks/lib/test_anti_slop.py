#!/usr/bin/env python3
"""Self-check for anti-slop.py (v1.7.0 M7)."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("anti_slop", Path(__file__).parent / "anti-slop.py")
_as = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_as)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def review(content, suffix=".py"):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"f{suffix}"
        p.write_text(content, encoding="utf-8")
        return _as.review_file(p, Path(f"f{suffix}"))


# blocking: stub
b, _ = review("def f():\n    pass\n")
check("stub blocks", any("stub" in x for x in b))

# blocking: placeholder
b, _ = review("# placeholder content here\nx=1\n")
check("placeholder blocks", any("placeholder" in x for x in b))

# blocking: generic AI doc
b, _ = review("# This robust solution efficiently leverages the stack\nx=1\n")
check("generic AI doc blocks", any("generic AI doc" in x for x in b))

# blocking: meaningless test
b, _ = review("def test_x():\n    assert True\n")
check("meaningless test blocks", any("meaningless test" in x for x in b))

# guide: hardcoded secret
_, g = review("api_key = 'sk-abc123'\n")
check("hardcoded secret guides", any("hardcoded" in x for x in g))

# guide: eval
_, g = review("result = eval(expr)\n")
check("eval guides", any("eval" in x for x in g))

# clean code: no findings
b, g = review("def add(a, b):\n    if not isinstance(a, int):\n        raise TypeError('a')\n    return a + b\n")
check("clean code silent", not b and not g)

print(f"OK: {PASS} assertions passed")
