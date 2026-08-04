#!/usr/bin/env python3
"""Fresh-install end-to-end parity (v1.7.0 M3).

Installs One Man into a clean fixture HOME, then runs a representative task
through: policies load -> Policy Runtime -> evidence -> fitness -> readiness.

Fails if the repo implementation works but the INSTALLED environment does
not reproduce the same behavior (the portability guarantee).

Runs in CI after install; the fixture HOME is provided via FIXTURE_HOME.
"""
import os
import sys
import tempfile
from pathlib import Path

# Windows cp1252 stdout chokes on unicode arrows in imported docstrings —
# force UTF-8 so tracebacks print instead of crashing.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).parent.parent

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def main():
    # fixture HOME: from env (CI) or a fresh temp dir
    fixture = Path(os.environ.get("FIXTURE_HOME", tempfile.mkdtemp(prefix="one-man-fixture-")))
    claude_home = fixture / ".claude"

    # 1. simulate install: copy the generalized mechanisms into the fixture
    #    (mirrors install.sh's copy list — the CI observe job does the real one)
    (claude_home / "hooks" / "lib").mkdir(parents=True, exist_ok=True)
    (claude_home / "policies").mkdir(parents=True, exist_ok=True)
    for f in (REPO / "hooks").glob("*.py"):
        (claude_home / "hooks" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    for f in (REPO / "hooks" / "lib").glob("*.py"):
        (claude_home / "hooks" / "lib" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    for f in (REPO / "policies").glob("*.json"):
        (claude_home / "policies" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    for f in ("one-man.controls.json", "skills.flow.json"):
        (claude_home / f).write_text((REPO / f).read_text(encoding="utf-8"), encoding="utf-8")

    # 2. policies loadable from the INSTALLED location (not the repo)
    sys.path.insert(0, str(claude_home / "hooks" / "lib"))
    import importlib.util
    _spec = importlib.util.spec_from_file_location("policy_runtime", claude_home / "hooks" / "lib" / "policy-runtime.py")
    pr = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(pr)
    pr.REPO = claude_home  # point the runtime at the installed policies
    plan = pr.evaluate({"type": "bug", "risk": "high"})
    check("policies load from installed location", plan["policy_version"] == "1.6.0")
    check("obligations from installed policy", any("regression" in o for o in plan["obligations"]))

    # 3. evidence + fitness work against the installed HOME
    import evidence as ev
    ev.HOME = fixture
    ev.EVIDENCE_DIR = fixture / ".claude" / "evidence"
    ev.write_record("current", {"type": "bug", "risk": "high",
                                "obligations": plan["obligations"], "evidence": []})
    f = fixture / "app.py"
    f.write_text("x=1\n")
    ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f)],
                       capability="verify-turn", obligation="suite passes")

    import fitness as fit
    fit.HOME = fixture
    fit.FITNESS_DIR = fixture / ".claude" / "fitness"
    for pol in ("obligations", "trust", "one-man.controls", "skills.flow"):
        fit.record(pol, "applied")
    check("fitness records in installed location",
          (fit.FITNESS_DIR / "obligations.json").exists())

    # 4. readiness gate works against the installed state
    import gate as g
    g._ev = ev  # gate uses the installed evidence
    import io
    from contextlib import redirect_stderr
    buf = io.StringIO()
    with redirect_stderr(buf):
        try:
            g.main()
            code = 0
        except SystemExit as e:
            code = e.code
    check("gate passes with capability-tied evidence", code == 0)

    print(f"OK: {PASS} assertions passed — fresh-install parity verified")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FRESH-INSTALL PARITY FAILED: {e}", file=sys.stderr)
        sys.exit(2)
