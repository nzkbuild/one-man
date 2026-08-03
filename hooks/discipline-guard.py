#!/usr/bin/env python3
"""PreToolUse hook — anti-slop nudges at tool-call time. Guide, never blocks.

Catches the silent-quality-killers a linter can't:
  1. Wide blast radius: a command touching 5+ source files with no design marker
     (plan/design/spec) in the recent prompt -> "did you design this first?"
  2. Reuse-first: creating a dir/file when a similar pattern already exists in
     the repo -> "is there already X? reuse over reinvent."
  3. Tests-missing: build/lint after 5+ source edits with 0 test edits -> "write
     tests for what you changed."

READ-ONLY: inspects the command line + a shallow repo scan. Never writes.
Any error -> exit 0 (fail-open). Output via additionalContext on stdout.
"""
import json
import os
import re
import sys
from pathlib import Path

# A recent prompt that signals design intent — no nudge for designed work.
DESIGN_MARKERS = re.compile(r"\b(plan|design|spec|intent|design doc|architecture)\b", re.IGNORECASE)

# Commands that count as "wide blast radius" (multi-file EDIT ops).
# VCS bookkeeping (git add/commit/mv/rm) is NOT a design decision — excluded.
WIDE_COMMANDS = re.compile(
    r"(cp\s+-r|mv\s+.*\*|sed\s+-i|eslint\s+--fix|prettier\s+--write|"
    r"ruff\s+check\s+--fix|tsc|pnpm\s+build|npm\s+run\s+build|"
    r"pytest|vitest|jest|pnpm\s+test)",
    re.IGNORECASE,
)

# Test-file name signals
TEST_PATTERN = re.compile(r"(test|spec|__tests__|_test\.)", re.IGNORECASE)


def prompt_has_design(prompt: str) -> bool:
    return bool(DESIGN_MARKERS.search(prompt or ""))


def wide_blast(cmd: str) -> bool:
    return bool(WIDE_COMMANDS.search(cmd or ""))


def similar_exists(cwd: Path, new_name: str):
    """Cheap reuse check: does a sibling dir/file with the same stem exist?"""
    try:
        stem = Path(new_name).stem.lower()
        if not stem or len(stem) < 3:
            return False
        for p in cwd.iterdir():
            if p.name.lower().startswith(stem[:6]) and p.name != new_name:
                return True
    except Exception:
        pass
    return False


def recent_source_edits(cwd: Path, window_min: int = 15) -> tuple:
    """Count source vs test files modified recently (cheap mtime scan)."""
    src = test = 0
    try:
        now = __import__("time").time()
        for p in cwd.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".rs"):
                if p.stat().st_mtime > now - window_min * 60:
                    if TEST_PATTERN.search(p.name):
                        test += 1
                    else:
                        src += 1
    except Exception:
        pass
    return src, test


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command") or ""
    prompt = payload.get("prompt") or ""
    cwd = Path(payload.get("cwd") or os.getcwd())

    nudges = []

    # 1. Wide blast radius without design intent
    if tool in ("Bash", "PowerShell") and wide_blast(cmd) and not prompt_has_design(prompt):
        nudges.append("Wide blast radius command without a design marker — did you "
                      "design this first? A plan/spec beats a 5-file shotgun edit.")

    # 2. Reuse-first on mkdir/new-file
    if tool in ("Bash", "PowerShell") and ("mkdir" in cmd or "New-Item" in cmd):
        m = re.search(r"(?:mkdir|New-Item)[^\S]*.*?([A-Za-z0-9_-]+)\s*$", cmd)
        if m and similar_exists(cwd, m.group(1)):
            nudges.append(f"Reuse-first: a similar path to '{m.group(1)}' already exists "
                          "in this repo — check before creating a duplicate.")

    # 3. Tests-missing after source edits
    if tool in ("Bash", "PowerShell") and re.search(r"(build|tsc|pytest|vitest|jest)", cmd):
        src, tst = recent_source_edits(cwd)
        if src >= 5 and tst == 0:
            nudges.append(f"{src} source files changed with 0 test files — write tests "
                          "for what you changed before declaring done.")

    if not nudges:
        sys.exit(0)

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": "# Discipline guard\n" + "\n".join(f"- {n}" for n in nudges),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
