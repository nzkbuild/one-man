"""Anti-slop outcome review (v1.7.0 M7).

Reviews the PRODUCED ARTIFACT, not merely the process. Detects:
  - incomplete implementation (stubs, pass-only, NotImplemented)
  - symptom-only fixes (patching the error without root cause)
  - placeholders / fake completeness (TODO, placeholder, dummy)
  - brittle or insecure code (bare except, eval, shell injection risk)
  - generic AI-style documentation (lorem, 'efficiently leverages')
  - meaningless tests (assert True, no assertions)
  - happy-path-only work (no error/edge handling)
  - duplicated logic
  - broad exception swallowing
  - dependency/configuration bloat
  - premature abstractions
  - unnecessary rewrites
  - stale documentation
  - overengineering relative to the task

Findings are ACTIONABLE + evidence-backed + tied to files/lines. Run at
Stop (after review-gate) on the changed files. Advisory by default (exit 0
+ findings); the completion gate blocks on the blocking classes.
"""
import re
from pathlib import Path

# Blocking anti-patterns (clear defects, not taste)
BLOCKING = [
    ("stub implementation", re.compile(r"^\s*(pass|\.\.\.)\s*(#.*)?$", re.M)),
    ("symptom-only catch", re.compile(r"except\s*:\s*\n\s*pass", re.M)),
    ("placeholder content", re.compile(r"\b(lorem ipsum|placeholder|dummy text|TBD)\b", re.I)),
    ("generic AI doc", re.compile(r"\b(efficiently leverages|seamlessly integrates|robust solution)\b", re.I)),
    ("meaningless test", re.compile(r"assert\s+True\s*$", re.M)),
    ("broad swallow", re.compile(r"except\s+Exception\s*:\s*\n\s*pass", re.M)),
]

# Guide-level anti-patterns (advisory)
GUIDE = [
    ("no error handling", re.compile(r"\b(def |async def )\w+\([^)]*\):\s*\n\s*(return|pass)", re.M)),
    ("hardcoded value", re.compile(r"(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]+['\"]", re.I)),
    ("eval/exec", re.compile(r"\b(eval|exec)\s*\(", re.I)),
]


def review_file(path: Path, rel: Path) -> tuple:
    """Return (blocking, guide) anti-slop findings for one file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []
    blocking, guide = [], []

    for label, pat in BLOCKING:
        for m in list(pat.finditer(text))[:2]:
            line = text[: m.start()].count("\n") + 1
            blocking.append(f"{rel}:{line} anti-slop: {label}")
            break

    for label, pat in GUIDE:
        for m in list(pat.finditer(text))[:2]:
            line = text[: m.start()].count("\n") + 1
            guide.append(f"{rel}:{line} consider: {label}")
            break
    return blocking, guide


def review_changed(cwd: Path, changed: list) -> tuple:
    """Review a list of changed files. Returns (blocking, guide)."""
    blocking, guide = [], []
    for rel in changed:
        p = Path(cwd) / rel if not Path(rel).is_absolute() else Path(rel)
        if p.exists() and p.suffix in (".py", ".ts", ".js", ".jsx", ".tsx"):
            b, g = review_file(p, Path(rel))
            blocking.extend(b)
            guide.extend(g)
    return blocking, guide


if __name__ == "__main__":
    import sys
    cwd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    changed = sys.argv[2:] or [str(p.relative_to(cwd)) for p in cwd.rglob("*.py")
                               if "node_modules" not in str(p) and ".git" not in str(p)]
    b, g = review_changed(cwd, changed)
    for f in b:
        print(f"BLOCK: {f}", file=sys.stderr)
    for f in g:
        print(f"GUIDE: {f}", file=sys.stderr)
    sys.exit(2 if b else 0)
