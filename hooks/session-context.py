#!/usr/bin/env python
"""SessionStart context builder for the self-evolving memory system.

Reads the hook payload JSON from HOOK_INPUT (the wrapper captures stdin into it) to learn
`cwd` and `source`, then assembles a budgeted, priority-ordered digest of:
  - global principles (~/.claude/self/PRINCIPLES.md)
  - global lessons (priority: pinned -> high -> most-recent normal, within budget)
  - global preferences
  - project lessons for the current cwd (~/.claude/projects/<slug>/memory/LESSONS.md)
  - project STATE.md (the current working thread)

READ-ONLY. Never writes. Any error -> exit 0 with no output so a session is never blocked.

Emits: {"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}
"""
import json
import os
import sys

HOME = os.path.expanduser("~")
SELF_DIR = os.path.join(HOME, ".claude", "self")

# Character budgets for the injected digest (approx; 1 token ~ 4 chars).
GLOBAL_LESSON_BUDGET = 4000
PROJECT_LESSON_BUDGET = 3000
PRIORITY_RANK = {"pinned": 0, "high": 1, "normal": 2}


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def strip_doc(text, drop_first_heading=True):
    """Drop HTML-comment anchors and the leading '# Title' + blockquote preamble."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("<!--"):
            continue
        if drop_first_heading and (s.startswith("# ") or s.startswith(">")):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def parse_entries(text):
    """Split a lessons file into (title, priority, body) entries by '## ' headings."""
    entries, cur = [], []
    for ln in text.splitlines():
        if ln.startswith("## "):
            if cur:
                entries.append(cur)
            cur = [ln]
        elif cur:
            cur.append(ln)
    if cur:
        entries.append(cur)

    parsed = []
    for block in entries:
        body = "\n".join(block).strip()
        prio = "normal"
        for ln in block:
            low = ln.lower()
            if "**priority:**" in low:
                val = low.split("**priority:**", 1)[1].strip()
                for k in PRIORITY_RANK:
                    if val.startswith(k):
                        prio = k
                        break
                break
        parsed.append((block[0][3:].strip(), prio, body))
    return parsed


def select_lessons(text, budget):
    """Return (selected_bodies, dropped_count). Order: pinned -> high -> recent normal.
    File order is newest-first, so we keep that as the tiebreak within each priority."""
    parsed = parse_entries(text)
    if not parsed:
        return [], 0
    # Stable sort by priority rank; file order (newest-first) preserved within a rank.
    ordered = sorted(range(len(parsed)), key=lambda i: PRIORITY_RANK.get(parsed[i][1], 2))
    selected, used, dropped = [], 0, 0
    for i in ordered:
        _, prio, body = parsed[i]
        # pinned always included regardless of budget; others must fit.
        if prio == "pinned" or used + len(body) <= budget:
            selected.append((i, body))
            used += len(body)
        else:
            dropped += 1
    # Present selected in the priority order we chose.
    return [b for _, b in selected], dropped


def slugify(cwd):
    return cwd.replace(":", "-").replace("\\", "-").replace("/", "-")


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    cwd = HOME
    source = "startup"
    if raw.strip():
        try:
            data = json.loads(raw)
            cwd = data.get("cwd") or cwd
            source = data.get("source") or source
        except Exception:
            pass

    parts = []

    # --- Global tier ---
    principles = strip_doc(read_text(os.path.join(SELF_DIR, "PRINCIPLES.md")))
    if principles:
        parts.append("# Standing workflow protocol (global)\n" + principles)

    g_text = read_text(os.path.join(SELF_DIR, "LESSONS.md"))
    g_sel, g_drop = select_lessons(g_text, GLOBAL_LESSON_BUDGET)
    if g_sel:
        block = "# Global lessons — do not repeat these (priority-ordered)\n" + "\n\n".join(g_sel)
        if g_drop:
            block += f"\n\n_({g_drop} more global lessons not shown — use /recall.)_"
        parts.append(block)
    # Nudge if lessons are near the budget — dropping is silent and permanent
    g_parsed = parse_entries(g_text)
    if len(g_parsed) > 15:
        parts.append(
            "# Memory maintenance needed\n"
            f"Global lessons: {len(g_parsed)} entries — nearing the token budget.\n"
            "Run `/memory-maintain` to dedup and prune before lessons start dropping silently."
        )

    prefs = strip_doc(read_text(os.path.join(SELF_DIR, "PREFERENCES.md")))
    if prefs:
        parts.append("# User preferences (global)\n" + prefs)

    # --- Project tier (scoped to current cwd) ---
    slug = slugify(cwd)
    proj_mem = os.path.join(HOME, ".claude", "projects", slug, "memory")
    proj_name = os.path.basename(cwd) or slug

    p_text = read_text(os.path.join(proj_mem, "LESSONS.md"))
    p_sel, p_drop = select_lessons(p_text, PROJECT_LESSON_BUDGET)
    if p_sel:
        block = f"# Project lessons for '{proj_name}' (priority-ordered)\n" + "\n\n".join(p_sel)
        if p_drop:
            block += f"\n\n_({p_drop} more project lessons not shown — use /recall.)_"
        parts.append(block)

    state = read_text(os.path.join(proj_mem, "STATE.md")).strip()
    if state:
        parts.append(f"# Current working state for '{proj_name}' (from STATE.md)\n" + state)

    # --- Project CLAUDE.md (the richest instruction file) ---
    claude_md = os.path.join(cwd, "CLAUDE.md")
    cm_text = read_text(claude_md).strip()
    if cm_text:
        parts.append(f"# Project CLAUDE.md for '{proj_name}'\n" + cm_text)

    if not parts:
        sys.exit(0)

    footer = (
        "\n\n---\nThis is your persistent memory. Follow the protocol. When corrected, invoke "
        "/self-evolve (choose global vs project scope). Use /checkpoint to save project state, "
        "/recall for full memory, /memory-maintain to prune."
    )
    if source == "compact":
        footer = (
            "\n\n---\nContext was just compacted. The above is your recovered memory + working "
            "state — resume the thread from STATE.md. " + footer.strip()
        )

    context = "\n\n---\n\n".join(parts) + footer

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
