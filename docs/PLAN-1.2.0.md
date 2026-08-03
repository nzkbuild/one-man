# one-man v1.1.0 + v1.2.0 — The Complete Plan

The v1.0.0 delivered the enforcement layer. This plan closes the remaining gaps to
billion-dollar-company standards: **reliability** (backup/rollback), **legitimacy**
(license/security/agents), **systematic reuse** (every skill/plugin wired into a flow),
and the **feedback loop** (measure → learn → improve).

---

## v1.1.0 — Reliability + Legitimacy (small, high-value)

### 1.1.1 Backup script (`scripts/backup.sh` + `.ps1`)
- Tars `~/.claude/` config + memory (settings.json, CLAUDE.md, hooks/, skills/, self/,
  plugins/installed_plugins.json) to `~/.claude-backups/one-man-<timestamp>.tar.gz`
- Restore flag: `backup.sh --restore <archive>` = one-command rollback of the whole system
- **Protects the irreplaceable**: your memory (LESSONS/PRINCIPLES/PREFERENCES) has no
  other copy today.
- Scheduled option documented (Task Scheduler / cron line in README)

### 1.1.2 Versioning discipline (`docs/versioning.md`)
- Semver policy: `vMAJOR.MINOR.PATCH` — PATCH=bugfix, MINOR=feature, MAJOR=breaking.
- Tag policy: every release = annotated tag, never re-tagged (the v1.0.0 move was a
  one-time correction, now prevented by plan-check).
- **Rollback drill**: `git checkout v1.0.0` + `backup.sh --restore` = exact previous
  state. Tested once per release (documented in CHANGELOG).
- CHANGELOG.md: every release gets an entry (Keep-a-Changelog format).

### 1.1.3 Legitimacy files
- `LICENSE` (MIT) — public repo without license = no legal use granted. Blocking gap.
- `CHANGELOG.md` — v1.0.0 + v1.1.0 entries.
- `SECURITY.md` — how to report a vulnerability.
- `AGENTS.md` — how an AI/agent works in this repo (architecture, commands, conventions).

### 1.1.4 Release
- `git tag v1.1.0` → push → CI green → plan-check passes (v1.2.0 items deferred in plan,
  exempt).

---

## v1.2.0 — The Feedback Loop + Systematic Reuse

### 1.2.1 `retrospective` (SessionEnd → stats.json) — THE measurement layer
- Records per-session: duration, files touched, commits, tests added, corrections
  (from prompt-guard hits), skill invocations.
- Appends to `~/.claude/self/stats.json`.
- Purpose: **you cannot improve what you don't measure**. This is the missing loop
  half — today the system enforces but never measures.

### 1.2.2 `task-triage` (UserPromptSubmit) — systematic reuse of pro-workflow
- Classifies the prompt (bug/feature/refactor/question), injects the right briefing:
  pre-mortem, exit criteria, gotchas — from the pro-workflow skill content.
- This is the *orchestrator*: it decides which skill applies to which prompt, so
  pro-workflow/dep-audit/audit get invoked at the right moment instead of sitting idle.

### 1.2.3 `discipline-guard` (PreToolUse) — anti-slop in code
- 5+ file blast radius → "design first?" nudge
- Existing pattern exists → "reuse first" nudge (anti-slop)
- `mkdir` when similar exists → reuse nudge

### 1.2.4 Skill-orchestration manifest (`skills.flow.json`) — THE systematic-reuse fix
The core insight from the audit: 13 design skills + superpowers + dep-audit sit
installed-but-idle. Fix = a flow manifest mapping **when each skill runs**:
| Trigger | Skill(s) wired |
|---|---|
| Prompt classified "design/UI" (task-triage) | brandkit → design-taste → minimalist-ui/industrial-brutalist |
| Prompt classified "feature/refactor" | pro-workflow → brainstorm → plan → implement → verify |
| New dependency detected (dep-guard) | dep-audit (full vetting) |
| Phase/milestone boundary (phase-gate) | audit |
| Correction (prompt-guard) | self-evolve |
| Turn end (verify-turn) | ship-gate + test suite |
| Session end (retrospective) | stats.json |

`task-triage` consumes this manifest to route every prompt to its skills. Skills stop
being "available" and become "invoked."

### 1.2.5 Anti-slop principle — codified in CLAUDE.md.global
- "Output must be reviewed against the repo's own standards, not just pass lint."
- "Every skill that applies must be invoked — idle skills are the gap."
- "When corrected, capture the rule — a mistake repeated is a process failure."

### 1.2.6 Release
- All 4 brains + flow manifest self-checked, CI green, plan-check verifies v1.1.0
  items are `[x]`, tags v1.2.0.

---

## Definition of done (both releases)

- [x] backup.sh restores a fixture archive in test
- [x] versioning.md + CHANGELOG + LICENSE + SECURITY + AGENTS committed
- [x] v1.1.0 tagged, CI green
- [x] retrospective writes stats.json (assert-tested)
- [x] task-triage classifies 5 sample prompts correctly (assert-tested)
- [x] discipline-guard fires on blast-radius, silent on small edits (assert-tested)
- [x] skills.flow.json routes a design prompt → design skills (smoke-tested)
- [x] v1.2.0 tagged, CI green, plan-check all `[x]`
