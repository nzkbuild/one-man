---
name: audit
description: Phase-gate drift audit — run when a milestone/phase is finished, before shipping, or any time the project feels off. Finds problems that live BETWEEN files and that per-file linters are structurally blind to: code unreachable from the entry point, the same concept implemented twice, infrastructure built but never wired, security settings declared in config but never enforced, and money/auth paths with no test. Use for "audit this", "360 audit", "second pass", "find edge cases", "what's missing", "is this ready to ship", "what did we break".
---

# Drift audit (phase gate)

Per-edit hooks catch defects **inside** a file. This catches drift — the gap between
what the project *claims* to do and what it actually does, which accumulates as a
project evolves and is invisible from any single file.

## When to run it

- A phase or milestone (P/M) is finished
- Before shipping or deploying
- After a long stretch of changes, or when returning to a project after time away
- Any time the user says the project feels off, or asks "what's missing"

Do **not** run it on every edit. It is a gate, not a linter — running it constantly
trains the user to ignore it.

## How to run

```bash
python ~/.claude/skills/audit/audit.py [project_dir]
```

Takes 10–60s depending on repo size (it invokes ruff and mypy). Python and TS/JS.
It only ever reports; it never edits or deletes.

## What it checks

| Check | The failure it catches |
|---|---|
| Reachability | Abandoned layers — code unreachable from any entry point (incl. Docker/CI-declared ones) |
| Duplicate concepts | Two classes with the same name — callers silently using different shapes |
| Config vs code | A security setting in `.env` that no code enforces. **The most dangerous class**: the project looks configured correctly and isn't |
| Critical coverage | Money/auth/secret functions with no test naming them |
| Tool debt | ruff/mypy findings, summarized — with `None`-related type errors called out as latent crashes |
| TS/JS risk patterns | `eval`, `dangerouslySetInnerHTML`, hardcoded env fallbacks, `@ts-ignore`, `any` |

## Reporting the results — this matters most

The user is a self-described vibe coder: they cannot verify these findings
themselves, so an unverified claim is worse than no claim.

1. **Verify before repeating.** Static analysis produces false positives. Read the
   actual line (`codegraph_explore` or Read) before telling the user they have a
   vulnerability. Real examples from this tool's own development: `S105
   hardcoded-password` fired on `TOKEN = "token"` (an Enum member), and `health.py`
   showed as unreachable when `Dockerfile.api` runs it as `python -m app.api.health`.
2. **"Unreachable" is a question, not a verdict.** It means *either* an abandoned
   layer to delete *or* something that should be wired and isn't. Those need opposite
   fixes. Determine which before proposing anything.
3. **Never auto-delete.** Deleting "dead" code is destructive and static analysis
   cannot see every entry point. Propose; let the user decide.
4. **Rank by consequence, lead with the worst.** Data loss and unenforced auth
   outrank style debt.
5. **Say what you could not check.** Architecture quality, whether the flow matches
   the user's intent, and business-logic correctness are not mechanically detectable.
   Do not imply a clean audit means a correct project.

## Fixing what it finds

Fix in consequence order, and re-run the audit after each fix to confirm the finding
is gone — the audit is both the worklist and the verification. Commit between fixes
so each one is independently revertable.

Watch for coupled findings: the fix for one may be blocked by another. Example — the
repair for "orders stored in RAM" is to wire up `sqlite_repo.py`, but that file holds
13 `None`-type errors, so it must be fixed *before* being wired, not after.
