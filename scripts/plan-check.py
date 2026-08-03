#!/usr/bin/env python3
"""plan-check.py — fail when "done" is declared over open plan items.

Parses PLAN-1.0.0.md (or any plan file passed as argv[1]). Counts unchecked
checklist lines `- [ ]`. Exits 2 if any remain AND the caller claims a release /
completion milestone (detected from the commit message or a --release flag).

Rules (ponytail):
- `- [ ]` lines explicitly marked "deferred"/"v1.1"/"NOT built" are exempt —
  they are honest deferrals, not gaps.
- Exit 2 only under --release; plain run prints the open count (informational).
- READ-ONLY. Never writes.
"""
import re
import sys
from pathlib import Path

# A line is a deferral when it names a future version/scope ("v1.1", "defer",
# "out of scope"). A deferral does NOT block release — regardless of status
# words like "not built" (status) vs blocking words like "required for release".
DEFERRAL = re.compile(r"defer(red)?|v1\.1|v1\.2|out of scope|later", re.IGNORECASE)
# Blocking qualifiers override a deferral: these say "this MUST ship first".
BLOCKING = re.compile(r"required (for|before)|must (ship|have)|blocking|release gate", re.IGNORECASE)


def is_exempt(line: str) -> bool:
    return bool(DEFERRAL.search(line)) and not BLOCKING.search(line)


def all_open_items(plan: Path):
    """Every unchecked checklist line (exempt or not) — visible in plain mode."""
    found = []
    for i, line in enumerate(plan.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^\s*- \[ \]", line):
            found.append((i, line.strip()))
    return found


def main():
    release = "--release" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--release"]
    plan = Path(args[0]) if args else Path("PLAN-1.0.0.md")
    if not plan.exists():
        print(f"plan-check: {plan} not found", file=sys.stderr)
        sys.exit(1)

    open_ = all_open_items(plan)
    if open_:
        print(f"plan-check: {len(open_)} open item(s) in {plan.name}:")
        for ln, text in open_[:15]:
            mark = " " if is_exempt(text) else "*"
            print(f"  [{mark}] {plan.name}:{ln} {text[:70]}")
        if len(open_) > 15:
            print(f"  …and {len(open_) - 15} more")
        if release:
            blockers = [x for x in open_ if not is_exempt(x[1])]
            if blockers:
                print("plan-check: --release with non-deferred open items — BLOCKED. Ship nothing over an open plan.", file=sys.stderr)
                sys.exit(2)
    if release:
        print(f"plan-check: {plan.name} — clear to release (open items are exempt deferrals)")
    else:
        print(f"plan-check: {plan.name} — {len(open_)} open item(s)")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"plan-check error: {e}", file=sys.stderr)
        sys.exit(1)
