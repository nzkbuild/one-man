#!/usr/bin/env python3
"""Self-check for perf-guard.py — perf anti-pattern detection."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("pg", Path(__file__).parent / "perf-guard.py")
_pg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pg)

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
        return _pg.review(p, Path(f"file{suffix}"))


# N+1: query inside loop
n1 = review('''def f(users):
    for u in users:
        profile = Profile.objects.get(user_id=u.id)  # query in loop
        print(profile)
''')
check("N+1 flagged", any("N+1" in n for n in n1))

# nested same collection
nested = review('''def f(items):
    for a in items:
        for b in items:
            if a == b:
                pass
''')
check("nested same flagged", any("O(n" in n for n in nested))

# fetch-all
fa = review('''def f():
    return Model.objects.all()
''')
check("fetch-all flagged", any("fetch-all" in n for n in fa))

# clean code silent
clean = review('''def f(a, b):
    return a + b
''')
check("clean silent", clean == [])

print(f"OK: {PASS} assertions passed")
