"""Per-project state store (v1.8.0) — scopes runtime state to the current repo.

Before: debt/evidence/fitness/lessons all lived in ~/.claude/<store> GLOBALLY,
so one project's findings bled into every other project's baseline
(the dogfood finding: one-man's debt=3 showed in unrelated jbt sessions).

After: each store lives in ~/.claude/state/<project-key>/<store>/ where
project-key is a stable hash of the canonical cwd. Two projects never share
state; the same project always resolves to the same key.

Global BY DESIGN (the rules, not the data):
  policies/*.json, one-man.controls.json, skills.flow.json  — shared config
  lessons memory via ~/.claude/projects/<slug>/memory/       — already scoped

Migration: existing global stores are moved into the current project's dir
once (idempotent — subsequent runs skip).

Local-only + bounded. Never ships.
"""
import hashlib
import os
import shutil
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
STATE_ROOT = HOME / ".claude" / "state"


def project_key(cwd: Path = None) -> str:
    """Stable key for the current project: sha1 of the canonical absolute cwd.

    The raw path is not used as the key (Windows separators/colons are
    filesystem-hostile and paths can move); the hash is stable and safe.
    """
    try:
        p = Path(cwd or os.getcwd()).resolve()
    except Exception:
        p = Path(cwd or os.getcwd())
    return hashlib.sha1(str(p).lower().encode("utf-8")).hexdigest()[:16]


def state_dir(store: str, cwd: Path = None) -> Path:
    """~/.claude/state/<project-key>/<store>/ — the per-project home of one store."""
    d = STATE_ROOT / project_key(cwd) / store
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def migrate(store: str, legacy: Path, cwd: Path = None) -> bool:
    """Move a legacy GLOBAL store (~/.claude/<store>/) into this project's dir.

    Idempotent: returns False if there is nothing to migrate (already done or
    no legacy data). Never copies — moves, so the global dir stops growing.
    """
    try:
        if not legacy.is_dir():
            return False
        target = state_dir(store, cwd)
        # legacy holds files -> move them in; empty legacy -> remove it
        files = [f for f in legacy.iterdir() if f.is_file()]
        if not files:
            try:
                legacy.rmdir()
            except Exception:
                pass
            return False
        if store == "lessons":
            # lessons may already be per-project: don't clobber project ones
            for f in files:
                dest = target / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
        else:
            for f in files:
                shutil.move(str(f), str(target))
        try:
            legacy.rmdir()
        except Exception:
            pass
        return True
    except Exception:
        return False
