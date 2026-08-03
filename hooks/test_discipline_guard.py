#!/usr/bin/env python3
"""Self-check for discipline-guard.py — anti-slop nudges."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dg", Path(__file__).parent / "discipline-guard.py")
_dg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dg)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


# 1. wide blast radius detection
check("build cmd is wide", _dg.wide_blast("pnpm build"))
check("git add NOT wide (VCS bookkeeping)", not _dg.wide_blast("git add -A"))
check("echo is not wide", not _dg.wide_blast("echo hello"))
check("plain ls is not wide", not _dg.wide_blast("ls -la"))

# 2. design marker suppresses nudge
check("design marker recognized", _dg.prompt_has_design("plan the refactor first"))
check("no design marker", not _dg.prompt_has_design("just fix it"))

# 3. reuse-first: similar_exists
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    (d / "user-service.ts").touch()
    check("similar exists", _dg.similar_exists(d, "user-service-v2.ts"))
    check("no similar", not _dg.similar_exists(d, "payment-service.ts"))
    check("short stem ignored", not _dg.similar_exists(d, "a"))

# 4. tests-missing scan
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # create 6 recent source files, 0 tests
    for i in range(6):
        (d / f"mod{i}.py").write_text("x=1\n")
    src, tst = _dg.recent_source_edits(d)
    check("6 src 0 test", src == 6 and tst == 0)
    # add a test file
    (d / "test_mod.py").write_text("def t(): pass\n")
    src, tst = _dg.recent_source_edits(d)
    check("src + test counted", src >= 6 and tst >= 1)

print(f"OK: {PASS} assertions passed")
