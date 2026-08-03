---
name: checkpoint
description: Save or update the current project's working state (goal, done, next, key decisions, open questions) so a new session or a post-compaction context can resume the thread intact. Use at milestones, before long breaks, or when the user asks to save progress.
allowed-tools: Read, Write, Bash
---

# Checkpoint — save the project working thread

Write the current state to the project's `STATE.md` so nothing is lost across sessions or
compaction. This is a single **current-state** file (overwrite, not an append log).

## Steps

1. Resolve the project memory dir from the current working directory:
   On Windows (Git Bash):
   ```!
   CWD=$(cmd //c cd 2>nul || cygpath -w "$PWD")
   SLUG=$(echo "$CWD" | sed 's/[:\\]/-/g')
   MEMORY_DIR="$HOME/.claude/projects/$SLUG/memory"
   ```
   On macOS/Linux:
   ```!
   CWD="$PWD"
   SLUG=$(echo "$CWD" | sed 's/[:\\\/]/-/g')
   MEMORY_DIR="$HOME/.claude/projects/$SLUG/memory"
   ```
   Create it if it doesn't exist (`mkdir -p "$MEMORY_DIR"`).

2. Read the existing `STATE.md` there (if any) so you update rather than blindly replace —
   preserve still-relevant decisions.

3. Write `STATE.md` with this structure, kept tight (this is injected every session, so it
   must stay small — trim completed detail aggressively):
   ```
   # Project State — <project name>
   _Updated: YYYY-MM-DD_

   ## Goal
   <the current objective in 1-2 lines>

   ## Done
   - <key completed milestones, not every step>

   ## Next
   - <the immediate next actions>

   ## Key decisions
   - <decisions + one-line rationale that future-me must not re-litigate>

   ## Open questions / blockers
   - <unresolved items, or "none">
   ```

4. Confirm in one line what you saved and where. Next session the SessionStart hook injects
   this automatically.

## Rules
- Keep it current, not historical — prune finished work down to a short "Done" summary.
- No secrets or transient data.
- If invoked with arguments, treat `$ARGUMENTS` as notes to fold into the state.
