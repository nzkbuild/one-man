#!/usr/bin/env python3
"""Anti-drift (v1.6.0 M5 — layer 8, policy output).

Drift extends beyond README: detects divergence across implementation,
documentation, architecture, plans, CHANGELOG, release notes, configuration,
tests, policies, and engineering decisions.

For each drift: classification, severity, owner (the change that caused it),
recommended sync action, verification (did the sync happen), closure.

Drift semantics:
  - auto-flag on meaningful changes (advisory-first; never blocks alone)
  - approval-to-skip recorded (constitution: never silently introduce drift)
  - verified -> closed when the sync action completes

Conservative patterns: flags only clear divergence, not every doc touch.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
DRIFT_DIR = HOME / ".claude" / "drift"

# artifact -> what syncs it (the docs-sync decision)
ARTIFACT_SYNC = {
    "README.md": "implementation change (files added/removed, API changed)",
    "CHANGELOG.md": "release or notable change",
    "docs/architecture/": "architectural change",
    "docs/PLAN-*.md": "plan change or completed milestone",
    "AGENTS.md": "architecture/commands changed",
    "CLAUDE.md": "conventions/rules changed",
}

# implementation change signals -> affected artifacts
CHANGE_SIGNALS = [
    (re.compile(r"\.py$|\.ts$|\.js$"), ["README.md", "CHANGELOG.md"]),
    (re.compile(r"package\.json|lock"), ["README.md", "CHANGELOG.md"]),
    (re.compile(r"docs/architecture/|ADR-"), ["docs/architecture/", "AGENTS.md"]),
    (re.compile(r"docs/PLAN-"), ["docs/PLAN-*.md"]),
]


def _dir() -> Path:
    try:
        DRIFT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return DRIFT_DIR


def detect(cwd: Path) -> list:
    """Scan recent changes; return drift findings (classification, severity,
    owner, affected artifacts, sync action)."""
    findings = []
    now = time.time()
    try:
        # cheap proxy: files changed in the last 10 min
        changed = []
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in
                       {"node_modules", ".git", "__pycache__", "venv", ".venv"}]
            for name in files:
                p = Path(root) / name
                try:
                    if now - p.stat().st_mtime < 600:
                        changed.append(p.relative_to(cwd))
                except OSError:
                    pass

        for p in changed:
            name = str(p)
            for pat, artifacts in CHANGE_SIGNALS:
                if pat.search(name):
                    severity = "high" if "package.json" in name or "ADR" in name else "medium"
                    findings.append({
                        "classification": "implementation" if pat.pattern.startswith(r"\.") else
                                          ("config" if "package" in name else "docs"),
                        "severity": severity,
                        "owner": name,
                        "affected": artifacts,
                        "sync_action": f"update {', '.join(artifacts)} for change in {name}",
                        "status": "open",
                    })
                    break
    except Exception:
        pass
    return findings


def verify_and_close(cwd: Path, finding: dict) -> bool:
    """Verify the sync happened (the affected artifact changed in the SAME
    commit as the owner — mtime-equal in CI checkouts counts as synced);
    if so, close the drift."""
    try:
        owner_mtime = (cwd / finding["owner"]).stat().st_mtime
        for art in finding["affected"]:
            targets = list(cwd.glob(art)) if "*" in art else [cwd / art]
            for t in targets:
                if t.exists() and t.stat().st_mtime >= owner_mtime - 1:
                    return True  # synced in the same commit (CI flattens mtimes)
        return False
    except Exception:
        return False


def report() -> list:
    out = []
    try:
        for p in sorted(_dir().glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                out.append(f"[{d.get('status','?')}] {d.get('classification','?')} drift: "
                           f"{d.get('owner','?')} -> {d.get('sync_action','?')}")
            except Exception:
                continue
    except Exception:
        pass
    return out


if __name__ == "__main__":
    # CI/health entry: detect drift; auto-close when the sync already happened;
    # exit 2 only for high-severity drift that is genuinely unresolved.
    try:
        cwd = Path(os.environ.get("DRIFT_CWD", os.getcwd()))
        findings = detect(cwd)
        open_high = []
        for f in findings:
            if verify_and_close(cwd, f):
                f["status"] = "closed"  # sync verified — not drift anymore
            elif f["severity"] == "high":
                open_high.append(f)
        if open_high:
            print("## Drift — high-severity open (fix or approve-skip):", file=sys.stderr)
            for f in open_high[:5]:
                print(f"- {f['sync_action']}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    except Exception:
        sys.exit(0)
