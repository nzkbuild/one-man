#!/usr/bin/env python3
"""Stop hook — automated code review of the turn's changed files.

The solo-developer's missing second pair of eyes. Catches what lint cannot:
design debt, hidden coupling, premature abstraction, magic numbers, duplicated
logic, missing error handling, wrong-algorithm-for-data.

CONSERVATIVE by design: only clear defects block (exit 2). Subjective opinions
are guides only (exit 0 + stderr). A false-positive gate on opinion is worse
than a missed nudge. Any error -> exit 0 (fail-open).

Scans files changed in the last 10 min (same window as verify-turn/ship-gate).
"""
import json
import os
import re
import sys
from pathlib import Path

CHANGED_WINDOW_MIN = 10
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs"}

# ---- Defect patterns: clear, mechanical, actionable ----

# Magic numbers (literals > 10 used in code, not config/constants)
MAGIC = re.compile(r"[=(\[,\s]\d{3,}(?:[.,]\d+)?[)\],;\s]")

# Bare except / catch-all swallow without handling
BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*$", re.M)

# TODO/FIXME left (ship-gate catches too, but review names the line)
TODO = re.compile(r"\b(TODO|FIXME|XXX)\b")

# Duplicated block heuristic: 3+ identical consecutive lines (strong signal)
def _dup_block(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i in range(len(lines) - 2):
        if lines[i] == lines[i + 1] == lines[i + 2] and len(lines[i]) > 15:
            return lines[i][:50]
    return None


# Missing error handling: bare open()/read without try
BARE_IO = re.compile(r"\bopen\s*\([^)]*\)\s*(?!\s*try)")


sys.path.insert(0, str(Path(__file__).parent / "lib"))
import scan as _scan  # noqa: E402 — local lib, path insert required

def changed_files(cwd: Path):
    return _scan.changed_files(cwd, window_min=CHANGED_WINDOW_MIN,
                               skip_names=("test_", "perf-guard", "review-gate", "understand-guard"))


def review_file(p: Path, rel: Path):
    """Return (blocking, guide) findings for one file."""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []
    blocking, guide = [], []

    # Magic numbers — guide (could be intentional)
    for m in list(MAGIC.finditer(text))[:3]:
        line_no = text[: m.start()].count("\n") + 1
        guide.append(f"{rel}:{line_no} magic number {m.group(0).strip()} — name it or comment it")
        break

    # Bare except — blocking (swallows errors silently)
    for m in BARE_EXCEPT.finditer(text):
        line_no = text[: m.start()].count("\n") + 1
        blocking.append(f"{rel}:{line_no} bare except — add handling or logging")
        break

    # TODO left in changed code — blocking (dead-end debt)
    for m in TODO.finditer(text):
        line_no = text[: m.start()].count("\n") + 1
        blocking.append(f"{rel}:{line_no} TODO/FIXME left in changed code")
        break

    # Duplicated block — guide (could be legit)
    dup = _dup_block(text)
    if dup:
        guide.append(f"{rel}: duplicated block ('{dup}…') — extract or justify")

    return blocking, guide


def _task_risk():
    """Read the current task's risk from the evidence record (M3)."""
    try:
        sys.path.insert(0, str(Path(__file__).parent / "lib"))
        import evidence as _ev
        rec = _ev.read_record("current")
        return (rec or {}).get("risk", "low")
    except Exception:
        return "low"


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

    risk = _task_risk()

    # v1.5.0 M5: high-risk tasks require context-isolated review. The gate
    # cannot spawn agents — it REQUIRES the isolation as a completion
    # condition: the model must delegate to a fresh-context subagent given
    # only the diff + task record + repo conventions, then record the
    # findings in the evidence store. Absent that record, the gate blocks.
    if risk == "high":
        try:
            sys.path.insert(0, str(Path(__file__).parent / "lib"))
            import evidence as _ev
            rec = _ev.read_record("current") or {}
            ev = rec.get("evidence", [])
            if not any(e.get("kind") == "isolated_review" for e in ev):
                print(
                    "## High-risk change requires context-isolated review.\n"
                    "Delegate to a fresh subagent with ONLY: the diff, this task's "
                    "record, and the repo conventions (no implementation context). "
                    "Record the findings as evidence kind=isolated_review.",
                    file=sys.stderr,
                )
                sys.exit(2)
        except Exception:
            pass

    blocking, guide = [], []
    for p, rel in changed_files(cwd):
        b, g = review_file(p, rel)
        blocking.extend(b)
        guide.extend(g)

    # v1.6.0 M4: blocking findings become engineering debt automatically.
    try:
        sys.path.insert(0, str(Path(__file__).parent / "lib"))
        import debt as _debt
        for f in blocking:
            _debt.create(str(rel), f, severity="high", source="review-gate")
    except Exception:
        pass

    if not blocking and not guide:
        sys.exit(0)

    lines = []
    if blocking:
        lines.append("## Code review — clear defects in changed files (fix before done):")
        for f in blocking[:10]:
            lines.append(f"- {f}")
        if len(blocking) > 10:
            lines.append(f"- …and {len(blocking) - 10} more")
    if guide:
        if lines:
            lines.append("")
        lines.append("## Code review — consider:")
        for f in guide[:6]:
            lines.append(f"- {f}")

    print("\n".join(lines), file=sys.stderr)
    sys.exit(2 if blocking else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
