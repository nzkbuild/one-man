#!/usr/bin/env python3
"""Stop hook — design review for design-classified turns.

When the turn was classified "design" by task-triage, scans changed UI files
for the design chain's hard standards: a11y gaps (no alt, low contrast,
missing labels), placeholder content, generic AI-looking output markers.

Guide + conservative gate (exit 2 only on clear a11y defects — the a11y ones
are the non-negotiable ones). Any error -> exit 0.

Ponytail: a11y defects are mechanical (alt missing, no label); taste defects
(contrast, spacing) are guides. Split is deliberate.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

WINDOW_MIN = 10
UI_EXTS = {".html", ".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss"}
SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build", ".next"}

# a11y: img without alt — check the tag has an alt= attribute anywhere
NO_ALT = re.compile(r"<img\b(?![^>]*\balt=)[^>]*>", re.IGNORECASE)
# a11y: input/button without accessible name (placeholder-only is not a label)
NO_LABEL = re.compile(r"<(input|button)\b(?![^>]*\b(?:aria-label|label|name)=)[^>]*>", re.IGNORECASE)
# placeholder content
PLACEHOLDER = re.compile(r"\b(lorem ipsum|TODO text|example\.com|placeholder|dummy text)\b", re.IGNORECASE)
# generic AI output markers
AI_SLOP = re.compile(r"\b(welcome to our|get started today|revolutioniz|unleash|supercharge)\b", re.IGNORECASE)


def changed_files(cwd: Path):
    out = []
    now = time.time()
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.startswith(("test_", "design-review")):
                continue
            p = Path(root) / name
            if p.suffix in UI_EXTS:
                try:
                    if now - p.stat().st_mtime < (WINDOW_MIN + 1) * 60:
                        out.append((p, p.relative_to(cwd)))
                except OSError:
                    pass
    return out


def review(p: Path, rel: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []
    blocking, guide = [], []

    if p.suffix in (".html", ".tsx", ".jsx", ".vue", ".svelte"):
        for m in list(NO_ALT.finditer(text))[:3]:
            line = text[: m.start()].count("\n") + 1
            blocking.append(f"{rel}:{line} <img> without alt — a11y (WCAG 2.2 AA)")
            break
        for m in list(NO_LABEL.finditer(text))[:3]:
            line = text[: m.start()].count("\n") + 1
            blocking.append(f"{rel}:{line} input/button without accessible name — a11y")
            break
        if PLACEHOLDER.search(text):
            guide.append(f"{rel}: placeholder content — replace with real copy")

    if AI_SLOP.search(text):
        guide.append(f"{rel}: generic marketing phrasing — make it specific")

    return blocking, guide


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    cwd = Path.cwd()
    prompt = ""
    if raw.strip():
        try:
            data = json.loads(raw)
            if data.get("cwd"):
                cwd = Path(data["cwd"])
            prompt = data.get("prompt") or ""
        except Exception:
            pass

    # Only run for design-classified turns
    if not re.search(r"\b(design|ui|ux|interface|layout|page|component|visual)\b", prompt, re.IGNORECASE):
        sys.exit(0)

    blocking, guide = [], []
    for p, rel in changed_files(cwd):
        b, g = review(p, rel)
        blocking.extend(b)
        guide.extend(g)

    if not blocking and not guide:
        sys.exit(0)

    lines = []
    if blocking:
        lines.append("## Design review — a11y defects (fix before done):")
        for f in blocking[:6]:
            lines.append(f"- {f}")
    if guide:
        if lines:
            lines.append("")
        lines.append("## Design review — consider:")
        for f in guide[:5]:
            lines.append(f"- {f}")

    print("\n".join(lines), file=sys.stderr)
    sys.exit(2 if blocking else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
