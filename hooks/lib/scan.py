"""Shared changed-file scanning for one-man Stop/PostToolUse hooks.

Consolidates the 3 duplicated `changed_files` implementations (review-gate,
perf-guard, design-review) into one helper. Each caller passes its own
skip-set (hooks must not scan their own sources or test fixtures).

Any error -> empty list (fail-open: a scan failure must not block a session).
"""
import os
import time
from pathlib import Path

DEFAULT_WINDOW_MIN = 10
DEFAULT_SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build", ".next"}


def changed_files(cwd: Path, window_min: int = DEFAULT_WINDOW_MIN,
                  skip_dirs: set = None, skip_names: tuple = ()):
    """Yield (path, rel_path) for source files changed within the window.

    cwd: project root to walk.
    window_min: files whose mtime is within this many minutes count as changed.
    skip_dirs: directory names to prune (defaults to build/vendor dirs).
    skip_names: filename prefixes to skip (hooks must skip their own sources
                and test fixtures — scanning them is self-referential noise).
    """
    if skip_dirs is None:
        skip_dirs = DEFAULT_SKIP_DIRS
    out = []
    now = time.time()
    try:
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            for name in files:
                if name.startswith(skip_names):
                    continue
                p = Path(root) / name
                if p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".rs"):
                    try:
                        if now - p.stat().st_mtime < (window_min + 1) * 60:
                            out.append((p, p.relative_to(cwd)))
                    except OSError:
                        pass
    except Exception:
        return []
    return out
