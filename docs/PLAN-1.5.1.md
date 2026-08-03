# One Man v1.5.1 — Closed-Loop Learning Patch

**Status:** Proposed (implementation not started)
**Date:** 2026-08-04
**Scope:** Patch-sized, backward-compatible. No v1.6.0 adaptive work, no cloud, no redesign of the evidence architecture, no personal memory into the repo.
**Goal:** The smallest reliable loop that turns valuable mistakes into tested improvements — retrievable, applied at the right time, recurrence tested.

---

## 0. Verified findings (evidence from the v1.5.0 session)

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F1 | **Repeated lint-mistake class**: E741 (ambiguous `l`) hit 6+ times across session | 6 hook files still contain `for l in`-class patterns; 14 fix-class commits | verify-edit catches it, but the *class* recurs — no prevention, only detection |
| F2 | **5 CI failures in last 20 runs** | gh run list | Each was a local-catchable issue (YAML colon, test isolation) that pushed to main first — the v1.4.0 lesson, **recurred** |
| F3 | **Skills routed but unreferenced by flows**: dep-audit (0 refs), ctx-agent-history-search (0 refs) | grep | `skills.flow.json` routes them; **no hook/flow invokes them** — the "installed but unused" gap, real |
| F4 | **Version bump missed at release** (package.json stayed 1.0.0 until caught) | git log | No mechanical version-consistency check — human catch |
| F5 | **No structured lesson record**: corrections exist as memory notes, not retrievable/tested | session-context reads memory, nothing else | "AI learns" is unverifiable — no record of violation → root cause → recurrence risk |
| F6 | **Test-isolation gap caused a CI failure**: M5 test scanned the real repo | 741e2a3 fix | Local-vs-CI parity: local passed, CI failed — the exact class that recurs |

## 1. Patch scope — the smallest loop

**One new artifact, three small changes, zero new hooks-of-new-kind, zero new plugins.**

### A. `lessons/` — structured lesson ledger (the loop's memory)
- `~/.claude/lessons/<slug>.json`: `{id, date, category, violation, root_cause, correction, recurrence_risk, layer, tested, source}`.
- Written by **self-evolve** (extended, not new): when a correction is captured, it also writes a ledger entry.
- **Layers** (the decision process, item 2): local memory / CLAUDE.md rule / skill / hook / regression test / CI gate / no action.
- **Relevance + token discipline** (item 8): a SessionStart hook injects only lessons matching the current project's *signals* (repo name, language, risk) — a small filtered digest, not the full history. Bounded at ~30 active lessons, pruned oldest.

### B. `scripts/check-lessons.py` — recurrence detection (item 4)
- Scans the ledger for `recurrence_risk: high` entries whose `tested: false` or whose test hasn't run recently.
- Outputs: "lesson X recurs at risk — its test: Y" → surfaced at SessionStart.
- Verifies each `tested: true` lesson has a runnable check (the test file exists + passes).
- Self-check: fixture ledger → detection fires / silent when clean.

### C. Extend `self-evolve` to write the ledger (item 1+2)
- On `/self-evolve`, alongside the memory note, write the structured entry with the layer decision.
- The layer is chosen by the correction's nature: hook-fixable → hook + regression test; rule-worthy → CLAUDE.md; one-off → no action (documented).

### D. Promote to repo (item 5) — a curated `lessons/` seed
- The v1.5.0 session's generalized lessons (test isolation, local-vs-CI parity, version consistency, lint classes) as **generic, non-personal entries** in `lessons/seed.json` — the installer copies them as the initial ledger (user lessons stay local; seed is reusable).
- Installer: copies seed to `~/.claude/lessons/` if empty; never overwrites user lessons.

### E. CI parity check (item 6) — the F6 regression
- The M5 test-isolation fix becomes a **regression test**: a test that asserts hook tests run against an isolated cwd (the exact CI-failure class).
- Plus: `check-lessons.py` runs in CI (fails if a `tested: true` lesson's check is missing/broken).

### F. Version-consistency check (item 6, F4)
- `claude-health.sh` gains a check: `package.json` version == latest git tag == controls version. The exact miss that delayed v1.5.0 dies locally.

## 2. Milestones

| # | Milestone | Files |
|---|---|---|
| M1 | Lesson ledger (A) + self-evolve extension (C) | `hooks/lib/lessons.py` (new), `skills/self-evolve/` |
| M2 | Recurrence detection (B) + SessionStart relevance filter (A) | `scripts/check-lessons.py` (new), `hooks/session-context.py` (filter) |
| M3 | CI parity regression test (E) + version-consistency check (F) | `hooks/lib/test_*.py`, `claude-health.sh` |
| M4 | Repo promotion: seed + installer (D) | `lessons/seed.json` (new), `scripts/install.sh/.ps1` |
| M5 | Release prep (patch: version 1.5.1, CHANGELOG, plan-check) — **pending user decision** | |

## 3. Acceptance criteria + tests

- **M1:** ✅ DONE — hooks/lib/lessons.py (add/all/high_risk_untested/relevant, bounded 30); self-evolve SKILL.md gains the ledger step (layer decision table). 9-assertion self-check.
- **M2:** check-lessons detects a `recurrence_risk: high, tested: false` lesson; silent when clean; SessionStart injects only project-relevant lessons (fixture signals). 6 assertions.
- **M3:** regression test asserts hook tests run isolated (the F6 class); health check fails when version mismatches tag. 4 assertions.
- **M4:** seed installs when `~/.claude/lessons/` empty, never overwrites; seed contains zero personal data (scan). 3 assertions.

## 4. Deferred / rejected

- **Rejected:** more skills/hooks/plugins (the brief says don't); auto-tuning (v1.6.0).
- **Deferred:** v1.6.0 adaptive workflow, cloud sync, per-project lesson profiles.

## 5. Token/latency discipline (item 8)

- Ledger digest at SessionStart is **filtered** (project signals) + **bounded** (30 entries) + **compact** (one line per lesson, no history dump).
- check-lessons runs in CI, not per-turn.
- Self-evolve writes the ledger **without** injecting its content back into the prompt (write-only; retrieval is SessionStart-filtered).

## 6. Privacy / portability

- Ledger lives in `~/.claude/lessons/` (local). Seed is curated generic lessons only — zero personal data (scan-verified).
- No personal memory, transcripts, or logs copied. Installer never overwrites user lessons.

## 7. Rollback

- Each milestone is a small additive change; removing `lessons/` + the session-context filter line restores prior behavior. Evidence architecture untouched.
