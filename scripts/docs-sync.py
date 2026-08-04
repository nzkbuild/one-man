#!/usr/bin/env python3
"""Progressive documentation synchronization (v1.6.0 M6).

After a meaningful change, determines which engineering artifacts require
synchronization — README, CHANGELOG, plans, roadmap, architecture, release
notes, ADRs. Documentation evolves WITH implementation instead of relying on
memory (the plan-check lesson, generalized).

Auto-flag (advisory); approval-to-skip recorded (constitution: never silently
introduce drift). Output: the list of artifacts + why each needs sync.

Usage: python docs-sync.py [--changed file1 file2 ...]
       (no args: scans recent changes in the repo)
"""
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SYNC_LOG = HOME / ".claude" / "docs-sync.json"

# change pattern -> artifacts needing sync (+ why)
RULES = [
    (re.compile(r"\.py$|\.ts$|\.js$|\.tsx$"), [
        ("README.md", "implementation changed — API/usage may differ"),
        ("CHANGELOG.md", "notable change should be recorded"),
    ]),
    (re.compile(r"package\.json|pnpm-lock|lock"), [
        ("README.md", "dependencies changed — setup instructions may differ"),
        ("CHANGELOG.md", "dependency change is notable"),
    ]),
    (re.compile(r"docs/architecture/|ADR-"), [
        ("docs/architecture/", "architecture changed — ADR/architecture docs must reflect it"),
    ]),
    (re.compile(r"docs/PLAN-"), [
        ("docs/PLAN-*.md", "plan changed or milestone completed — update the plan"),
    ]),
    (re.compile(r"templates/CLAUDE\.md\.global|one-man\.controls\.json|skills\.flow\.json"), [
        ("AGENTS.md", "policy/rules changed — AGENTS.md conventions must reflect it"),
        ("CHANGELOG.md", "policy change is notable"),
    ]),
]


def artifacts_for(changed_files: list) -> list:
    """Return [(artifact, why)] needing sync for the changed files."""
    needed = {}
    for f in changed_files:
        for pat, artifacts in RULES:
            if pat.search(f):
                for art, why in artifacts:
                    needed.setdefault(art, set()).add(why)
    return [(a, "; ".join(sorted(ws))) for a, ws in needed.items()]


def record(changed_files: list, skipped: list = None):
    """Record the sync decision (auditable; approval-to-skip stored)."""
    import json
    try:
        entry = {
            "ts": time.time(),
            "changed": changed_files,
            "artifacts": artifacts_for(changed_files),
            "skipped": skipped or [],
        }
        log = []
        if SYNC_LOG.exists():
            try:
                log = json.loads(SYNC_LOG.read_text(encoding="utf-8"))
            except Exception:
                log = []
        log.append(entry)
        SYNC_LOG.write_text(json.dumps(log[-50:], indent=2), encoding="utf-8")
    except Exception:
        pass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        changed = args
    else:
        # scan recent changes (10-min window)
        cwd = Path.cwd()
        now = time.time()
        changed = []
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in
                       {"node_modules", ".git", "__pycache__", "venv", ".venv"}]
            for name in files:
                p = Path(root) / name
                try:
                    if now - p.stat().st_mtime < 600:
                        changed.append(str(p.relative_to(cwd)))
                except OSError:
                    pass

    if not changed:
        sys.exit(0)

    artifacts = artifacts_for(changed)
    if not artifacts:
        sys.exit(0)

    record(changed)
    print("## Progressive docs sync — these artifacts need updating:")
    for art, why in artifacts:
        print(f"- {art}: {why}", file=sys.stderr)
    # advisory: exit 0 (drift-gate handles high-severity blocking)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
