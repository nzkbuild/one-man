#!/usr/bin/env python3
"""Self-check for design-review.py — a11y + slop detection."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dr", Path(__file__).parent / "design-review.py")
_dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dr)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def review(content, suffix=".html"):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"file{suffix}"
        p.write_text(content, encoding="utf-8")
        b, g = _dr.review(p, Path(f"file{suffix}"))
        return b, g


# blocking a11y
b, _ = review('<img src="x.png">')
check("img no alt blocks", any("alt" in x for x in b))

b, _ = review('<input type="text" placeholder="Name">')
check("input no label blocks", any("accessible name" in x for x in b))

# guides
_, g = review("<p>Welcome to our revolution!</p>", ".html")
check("AI slop guides", any("marketing" in x for x in g))

_, g = review("<p>lorem ipsum dolor</p>", ".html")
check("placeholder guides", any("placeholder" in x for x in g))

# clean: alt + label present, no slop
b, g = review('<img src="x.png" alt="Chart">\n<input aria-label="Search">', ".html")
check("a11y-clean silent", not b and not g)

print(f"OK: {PASS} assertions passed")
