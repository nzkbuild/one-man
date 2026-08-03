---
name: self-evolve
description: Capture a durable lesson or preference into memory after a correction or confirmed guidance. Use when the user corrects a mistake, expresses a repeated frustration, or confirms a way of working worth remembering across sessions.
allowed-tools: Read, Edit, Write, Bash(python*)
---

# Self-evolve — persist a lesson (scoped, prioritized, deduped)

Update memory so a lesson survives to future sessions. Discipline matters: bad captures
create noise, cross-project bleed, and token bloat. Follow these steps exactly.

## 1. Is it worth capturing?
Extract the *generalizable rule*, not the incident. If it's a one-off with no reusable
rule, say so and STOP — do not write. Never record secrets, tokens, or transient data.

## 2. Choose scope (this prevents cross-project bleed)
- **Global** → `~/.claude/self/LESSONS.md` (or `PREFERENCES.md`): ONLY if the lesson helps
  on *unrelated* projects (a universal workflow/tone/tooling rule).
- **Project** → `~/.claude/projects/<slug>/memory/LESSONS.md`: anything tied to this
  codebase, stack, client, or domain. Compute `<slug>` from the current working directory:
  ```!
  python -c "import os;print(os.getcwd().replace(':','-').replace('\\\\','-').replace('/','-'))"
  ```
  If that project memory dir or file doesn't exist yet, create it.

When unsure, default to **project** scope — it's easy to promote later, hard to unbleed.

## 3. Assign priority
- `pinned` — critical, must never be dropped from the session digest (rare; use sparingly).
- `high` — important, survives ahead of recent trivia.
- `normal` — default.

## 4. Dedupe
Read the target file first. If an equivalent entry exists, refine it in place (and raise
priority if warranted) rather than adding a duplicate.

## 5. Backup before writing
Before editing LESSONS.md or PRINCIPLES.md:
```bash
cp ~/.claude/self/LESSONS.md ~/.claude/self/.LESSONS.md.bak 2>/dev/null
cp ~/.claude/self/PRINCIPLES.md ~/.claude/self/.PRINCIPLES.md.bak 2>/dev/null
```
For project-scoped lessons, back up the project LESSONS.md the same way.
This gives a rollback path if the write truncates the file on disk error.

## 6. Write the entry
Insert at the TOP of the entries (just after `<!-- LESSONS-START -->`), newest-first:
```
## YYYY-MM-DD — <short title>
**Priority:** pinned | high | normal
**Rule:** <the durable, generalizable lesson>
**Apply:** <how/when to apply it next time>
```
Use today's date. Keep the entry to 4 lines. Preferences: a concise bullet in the
appropriate `PREFERENCES.md` under its marker.

## 6. Confirm
Report one line: what you saved, the scope (global/project), and the priority. The
SessionStart hook loads it next session automatically — no restart needed.

If invoked with arguments, treat `$ARGUMENTS` as the lesson text to capture.
