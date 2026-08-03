#!/usr/bin/env python3
"""Stop-hook ship gate — catches "done" declared over dead or flagged code.

Runs during the same Stop event as verify-turn (invoked from verify-turn.sh).
Scans source files changed in the turn for the anti-slop patterns a red test
suite cannot see: TODO/FIXME/XXX, console.log/debugger, commented-out code,
empty catch blocks, and a suspicious source:test ratio.

READ-ONLY. Exit 2 + stderr on findings (harness feeds it back to the model as
actionable feedback). Exit 0 silent when clean. Any crash -> exit 0 (fail-safe).

Design notes (ponytail):
- Deliberately conservative: only scans files changed in the last 10 min
  (same window as verify-turn), so it never audits the whole repo every Stop.
- Pattern list is deliberately narrow to avoid noise. The goal is to flag the
  common anti-patterns, not to be a full linter — that's ruff/mypy/eslint.
"""
import json
import os
import re
import sys
from pathlib import Path

CHANGED_WINDOW_MIN = 10  # grep match: verify-turn uses -newermt '-10 minutes'
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs"}

# Skip these paths when scanning (vendored/generated dirs).
SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build", ".next"}

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)
DEBUG_PATTERN = re.compile(r"(?<!['\"])\bconsole\.log\b(?!['\"])|(?<!['\"])debugger\b(?<!['\"])")
COMMENT_BLOCK_PATTERN = re.compile(r"^\s*(?:#|//)\s{0,3}[^#/\s]", re.M)
EMPTY_CATCH_PY = re.compile(r"\bexcept\s*.*:\s*\n\s*(?:pass|\.\.\.)\s*\n", re.M)
EMPTY_CATCH_JS = re.compile(r"\bcatch[^{]*\{\s*\}")


def is_source(p: Path) -> bool:
    return p.suffix in SOURCE_EXTS


def changed_recently(p: Path) -> bool:
    """Cheap proxy for 'changed this turn': mtime within the window (POSIX)."""
    try:
        import time
        age = (time.time() - p.stat().st_mtime) / 60
        return age <= CHANGED_WINDOW_MIN + 1
    except OSError:
        return False


def walk_changed_sources(cwd: Path):
    """Yield (abs_path, rel_path) for source files changed in the window."""
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            p = Path(root) / name
            if is_source(p) and changed_recently(p):
                rel = p.relative_to(cwd)
                yield p, rel


def scan_file(p: Path, rel: Path):
    """Return list of finding strings for one file (empty when clean)."""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings = []

    # TODO/FIXME — but skip URLs (a TODO(url) is often a tracking link).
    for m in TODO_PATTERN.finditer(text):
        seg = text[max(0, m.start() - 15): m.end() + 25].replace("\n", " ")
        # Skip if "http" appears anywhere near the match (tracking link).
        ctx = text[max(0, m.start() - 40): m.end() + 40]
        if "http" in ctx:
            continue
        line_no = text[: m.start()].count("\n") + 1
        findings.append(f"{rel}:{line_no} TODO/FIXME left: {seg.strip()[:60]}")
        break  # one per file is enough — the fix message points at the location

    # console.log / debugger in committed source
    if DEBUG_PATTERN.search(text):
        findings.append(f"{rel}: console.log/debugger in source — remove before shipping")

    # empty except/catch
    if p.suffix == ".py" and EMPTY_CATCH_PY.search(text):
        findings.append(f"{rel}: empty except block (pass) — add handling or logging")
    if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".rs"} and EMPTY_CATCH_JS.search(text):
        findings.append(f"{rel}: empty catch block")

    # commented-out code: comment lines that also contain =, (, ), ; are likely code
    COMM = re.compile(r"^\s*(?:#|//)[^\n]*[=\[\(\)]")
    count = sum(1 for ln in text.splitlines() if COMM.match(ln))
    if count >= 2:
        findings.append(f"{rel}: ~{count} lines look like commented-out code")

    return findings


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    cwd = Path.cwd()
    if raw.strip():
        try:
            data = json.loads(raw)
            if data.get("cwd"):
                cwd = Path(data["cwd"])
        except Exception:
            pass

    all_findings = []
    touched = []
    for p, rel in walk_changed_sources(cwd):
        touched.append(str(rel))
        all_findings.extend(scan_file(p, rel))

    if all_findings:
        lines = [
            "## Ship-gate: work is not done-yet -- fix these before reporting done:",
            "",
        ]
        for f in all_findings[:12]:
            lines.append(f"- {f}")
        if len(all_findings) > 12:
            lines.append(f"- …and {len(all_findings) - 12} more")
        lines.append("")
        lines.append("The test suite may be green, but this dead/flagged code ships anyway.")
        print("\n".join(lines), file=sys.stderr)
        sys.exit(2)

    # source:test ratio check — 5+ source files changed but 0 test files
    src = [t for t in touched if not (t.startswith("test") or "/test" in t or t.startswith("tests"))]
    tst = [t for t in touched if t.startswith("test") or "/test" in t or t.startswith("tests")]
    if len(src) >= 5 and len(tst) == 0:
        print(
            "## Ship-gate: 5+ source files changed with no test files updated.\n"
            "If this is a behavior change, add tests for what you changed.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
