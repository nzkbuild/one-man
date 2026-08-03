---
name: recall
description: Load the full memory (global + current project) into context. Use when you need the complete history beyond the session-start digest, or the user asks what you remember.
allowed-tools: Read, Bash(python*)
---

# Recall — load full memory (both tiers)

The SessionStart hook injects only a budgeted, priority-ordered digest. Use this to pull the
complete picture when needed.

## Steps

1. **Global tier** — read:
   - `~/.claude/self/PRINCIPLES.md`
   - `~/.claude/self/LESSONS.md`
   - `~/.claude/self/PREFERENCES.md`

2. **Project tier** — resolve the current project memory dir and read its files if present:
   ```!
   python -c "import os,glob;s=os.getcwd().replace(':','-').replace(chr(92),'-').replace('/','-');d=os.path.expanduser('~/.claude/projects/'+s+'/memory');print('\n'.join(glob.glob(d+'/*.md')) or 'no project memory yet')"
   ```
   Read any `LESSONS.md`, `STATE.md`, `MEMORY.md` listed.

3. Respond:
   - If asked a specific question, answer from the content and cite the file + scope.
   - Otherwise summarize: lesson counts per tier, any `pinned`/`high` lessons called out,
     current project STATE (goal/next), and current preferences.
   - Do not dump raw files verbatim unless explicitly asked.
