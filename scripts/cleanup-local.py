#!/usr/bin/env python3
"""cleanup-local.py — prune Claude Code local cruft (v1.7.1).

Disk hygiene for the local harness: the session transcript dir grows unbounded
(463MB observed), plugin caches keep old versions, and the state/ dir accrues
dead project keys. None of this touches context — it's disk + startup scan
only.

Actions (all safe, all dry-run by default):
  --transcripts N   delete project *.jsonl older than N days (keeps memory/,
                    keeps the last K per project). Default 30 days.
  --plugins         remove old plugin versions (keep newest per plugin).
  --state           remove per-project state dirs older than N days.
  --dry-run         show what would be deleted (default on).
  --yes             actually delete.

Never touches: settings.json, hooks, policies, skills, self/, memory/.
"""
import argparse
import os
import shutil
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROJECTS = HOME / ".claude" / "projects"
PLUGIN_CACHE = HOME / ".claude" / "plugins" / "cache"
STATE_ROOT = HOME / ".claude" / "state"


def _age_days(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / 86400


def prune_transcripts(days: int, keep_last: int = 3, dry: bool = True):
    """Delete per-project *.jsonl older than `days`, keeping the newest K."""
    removed = 0
    kept = 0
    for proj in PROJECTS.iterdir():
        if not proj.is_dir():
            continue
        jl = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        # keep the newest K regardless of age
        for p in jl[:-keep_last] if len(jl) > keep_last else []:
            if _age_days(p) > days:
                if not dry:
                    p.unlink(missing_ok=True)
                removed += 1
        # anything older than days beyond the kept K
        for p in jl[:-keep_last]:
            if _age_days(p) > days and not dry:
                p.unlink(missing_ok=True)
        kept += len(jl[-keep_last:])
    print(f"transcripts: would remove {removed}, keep {kept} (dry-run)" if dry
          else f"transcripts: removed {removed}, kept {kept}")


def prune_plugins(dry: bool = True):
    """Remove old plugin versions (keep newest per plugin)."""
    removed = 0
    for vendor in PLUGIN_CACHE.iterdir():
        if not vendor.is_dir():
            continue
        for plugin in vendor.iterdir():
            if not plugin.is_dir():
                continue
            versions = sorted(
                [v for v in plugin.iterdir() if v.is_dir() and v.name[0].isdigit()],
                key=lambda v: v.name,
            )
            for old in versions[:-1]:  # keep newest
                if not dry:
                    shutil.rmtree(old, ignore_errors=True)
                removed += 1
    print(f"plugins: would remove {removed} old versions (dry-run)" if dry
          else f"plugins: removed {removed} old versions")


def prune_state(days: int, dry: bool = True):
    """Remove per-project state dirs (debt/evidence/fitness/lessons) older than N days."""
    removed = 0
    if not STATE_ROOT.is_dir():
        return
    for key_dir in STATE_ROOT.iterdir():
        if not key_dir.is_dir():
            continue
        if _age_days(key_dir) > days:
            if not dry:
                shutil.rmtree(key_dir, ignore_errors=True)
            removed += 1
    print(f"state: would remove {removed} stale project dirs (dry-run)" if dry
          else f"state: removed {removed} stale project dirs")


def main():
    ap = argparse.ArgumentParser(description="Prune Claude Code local cruft")
    ap.add_argument("--transcripts", type=int, default=30, help="days of transcripts to keep")
    ap.add_argument("--plugins", action="store_true", help="remove old plugin versions")
    ap.add_argument("--state", type=int, default=60, help="days before a state dir is stale")
    ap.add_argument("--dry-run", action="store_true", default=True, help="show only (default)")
    ap.add_argument("--yes", action="store_true", help="actually delete")
    args = ap.parse_args()

    dry = not args.yes
    if args.transcripts:
        prune_transcripts(args.transcripts, dry=dry)
    if args.plugins:
        prune_plugins(dry=dry)
    if args.state:
        prune_state(args.state, dry=dry)
    if dry:
        print("\nDry run — add --yes to actually delete.")


if __name__ == "__main__":
    main()
