---
name: memory-maintain
description: Prune, dedupe, and reprioritize the memory files so they stay small and high-signal. Use when a LESSONS.md grows large, /recall feels bloated, or periodically to keep memory from becoming a token sink.
allowed-tools: Read, Edit, Write, Bash(python*)
---

# Memory-maintain — keep memory small and high-signal

Memory that only grows becomes a token sink and buries important lessons. This skill is the
decay/prune discipline. **Never silently delete** — merge, demote, or archive, and always
report what changed.

## Which files
- Global: `~/.claude/self/LESSONS.md`, `~/.claude/self/PREFERENCES.md`
- Current project: `~/.claude/projects/<slug>/memory/LESSONS.md` (compute `<slug>`:
  ```!
  python -c "import os;print(os.getcwd().replace(':','-').replace('\\\\','-').replace('/','-'))"
  ```
Default to whichever the user names; if unspecified, do the current project's file.

## Steps
1. Read the target file. Count entries and note total size.
2. **Dedupe / merge:** combine entries expressing the same rule into the strongest single
   version (keep the highest priority among them). 
3. **Demote decayed lessons:** a `normal` lesson that's old and hasn't recurred can stay but
   should not crowd out others — the hook already budgets by priority, so mainly ensure
   priorities are honest (don't leave stale `high`/`pinned` that no longer matter).
4. **Merge scope errors:** if a project-specific lesson is sitting in global LESSONS.md,
   move it to the project file (and vice-versa). This repairs cross-project bleed.
5. **Archive, don't delete:** if truly removing an entry, move it to a `LESSONS.archive.md`
   in the same dir with a one-line reason, so nothing is lost.
6. Preserve the file's header, markers (`<!-- LESSONS-START -->`), and newest-first order.

## Report
End with a concise summary: entries before → after, what was merged/moved/archived, and
current size. If nothing needed changing, say so. Do not touch entries you didn't clearly
improve.
