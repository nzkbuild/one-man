# One Man v1.6.0 — Architectural Assessment & Design Review

**Date:** 2026-08-04
**Status:** Assessment only — no implementation (per brief)
**Scope:** Challenge the current direction, verify against the actual repo (v1.5.1, tree clean, tags verified), identify missing engineering capabilities, recommend the smallest architecture that delivers the greatest long-term value.

---

## 1. Current architecture assessment

### The system in one diagram

```
PROMPT → task-triage (type + RISK + obligations) → evidence record seeded
  ↓ (work; verify-turn runs suite)
verify-turn → appends test evidence (result/exit/files/state_hash)
  ↓ Stop
ship-gate → TODO/dead-code gate
review-gate → high-risk requires isolated_review evidence
evidence-gate → obligations backed by non-STALE evidence, else block "done"
  ↓
CI (linux+windows) → self-checks, plan-check, evidence-gate fixture, lesson fixture, observe
  ↓
SessionStart → memory digest + filtered lesson digest (one-line, bounded)
  ↓
Corrections → self-evolve → lesson ledger (lifecycle) → recurrence detection → seed promotion
```

**Architecture class:** a *layered enforcement harness* — prompt-time guidance (triage, guards), tool-time gates (danger, verify-edit), end-time gates (ship, review, evidence), session-time retrieval (memory, lessons), CI-time authority, and a closed learning loop (ledger → detection → seed).

### Verified state (v1.5.1)
- 32 hooks, 11 lib modules, 12 scripts, 6 plan docs, lesson seed
- Evidence architecture (v1.5.0) intact: record, gate, staleness, isolated review
- Learning loop (v1.5.1) intact: ledger, lifecycle, stable IDs, recurrence detection, filtered digest, CI fixture
- 21/21 self-checks, 30/30 health, CI green, privacy clean

## 2. Verified strengths

| Strength | Evidence |
|---|---|
| **Enforcement is layered and non-bypassable at the top** | CI is the authority; local hooks are fast feedback (pre-push runs check+health+plan-check) |
| **Evidence, not assertion** | obligations + state-hash staleness + isolated review; "done" requires proof against current code |
| **Privacy boundary is real** | zero personal data in repo (scan-verified); seed rejects 8 categories; local/One Man separation explicit |
| **Portability** | idempotent install, backup + restore-drill, clean-device CI observe |
| **Closed learning loop** | violation → structured lesson (lifecycle) → recurrence detection → filtered retrieval → CI-enforced |
| **Token discipline** | digest is one-line/bounded; detection runs in CI not per-turn |

## 3. Verified weaknesses

| Weakness | Evidence | Consequence |
|---|---|---|
| **W1 — Skill invocation still unproven** | audit classifies *reachability*; nothing records that a routed skill ran | The brief's core fear ("AI silently ignores tools") remains unverified at the invocation level |
| **W2 — No technical-debt register** | nothing tracks debt across sessions | Debt is discovered, fixed, forgotten — no lifecycle, no recurrence signal |
| **W3 — Drift detection is reactive, not systematic** | no automated check that docs/architecture/implementation agree | Documentation drift (the plan-check lesson) recurs per-release |
| **W4 — No project health signal** | health checks the *harness*, not the *project* being worked on | Can't tell "healthy project" from "debt-heavy project" |
| **W5 — Lesson retrieval is repo-signal only** | digest filters by repo name/language | Not task-aware; the brief's "engineering intelligence" (contextual retrieval) is missing |
| **W6 — No debt/drift reporting** | loop-report is manual, monthly | No recurring, automated engineering-quality signal |

## 4. Missing engineering capabilities (vs high-performing orgs)

Verified gaps, ranked by value-to-ceremony:

1. **Technical-debt register** (identify/classify/lifecycle/report) — highest value, mechanical, small
2. **Automated anti-drift** (docs-vs-code, plan-vs-reality, version consistency) — the plan-check lesson generalized
3. **Project health scoring** (debt load, test ratio, drift count → a score) — decision support
4. **Engineering quality metrics** (from existing stats.json + ledger) — measurement, not new infra
5. **Architectural fitness functions** (coupling/cohesion checks on the repo) — valuable, risk of ceremony
6. **Release readiness assessment** (aggregate all gates into one pre-release verdict) — consolidation, not new

## 5. Recommended v1.6.0 scope — "Engineering Intelligence"

**The smallest architecture: one new artifact (debt register) + one generalization (drift checks) + one aggregation (health score).**

| Component | What | New? |
|---|---|---|
| **Debt register** (`~/.claude/debt/`, `hooks/lib/debt.py`) | identify (from review-gate findings, ship-gate blocks, perf-guard hits) → classify (tech/process/design) → lifecycle (open→acknowledged→fixed→expired) | NEW |
| **Drift checks** (`scripts/drift-check.py`) | docs-vs-code, plan-vs-reality (plan-check generalized), version consistency (existing) → one drift report | GENERALIZE |
| **Project health score** (`scripts/health-score.py`) | debt load + test ratio + drift count + lesson recurrence → 0-100 score + verdict | NEW (aggregates existing) |
| **Contextual lesson retrieval** (extend `lessons.relevant`) | task-type + repo signals (NOT full task-context matching — that's v1.7.0) | EXTEND |

**Explicitly NOT in v1.6.0:** skill-invocation proof (needs agent-level instrumentation — v1.7.0), architectural fitness functions (ceremony risk), full task-context retrieval (token cost).

## 6. Milestone breakdown

| # | Milestone | Files |
|---|---|---|
| M1 | Debt register + lifecycle | `hooks/lib/debt.py` (new) + self-check |
| M2 | Debt writers (review-gate, ship-gate, perf-guard append debt entries) | 3 hook edits |
| M3 | Drift checks (generalize plan-check → drift-check incl. docs-vs-code) | `scripts/drift-check.py` (new) |
| M4 | Project health score (aggregates debt + drift + tests) | `scripts/health-score.py` (new) + CI job |
| M5 | Contextual lesson retrieval extension | `hooks/lib/lessons.py` (extend `relevant`) |
| M6 | Release prep (version 1.6.0, CHANGELOG, CI, tag) — pending approval |

## 7. Acceptance criteria

- **M1:** debt entry created by review-gate finding → lifecycle advances (open→fixed→expired). 6 assertions.
- **M2:** each writer appends with the right classify; dedupe by stable fingerprint. 5 assertions.
- **M3:** drift-check flags docs-vs-code mismatch; silent when aligned; version drift caught. 5 assertions.
- **M4:** health score computed from fixture debt+drift+tests; verdict threshold tested. 4 assertions.
- **M5:** retrieval matches task-type+repo signals; still bounded+one-line. 3 assertions.
- **M6:** 21+ self-checks, CI green both OSes, plan-check `[x]`, privacy clean.

## 8. Risks

- **Debt register becomes ceremony** (debt recorded, never acted on) → mitigation: M4 health score makes debt *visible* in one number; expiry auto-closes stale debt.
- **Drift-check false positives** (docs legitimately lag code) → mitigation: conservative patterns, advisory-first (exit 0 + report), gate only on release.
- **Health score gamified** (optimize the score, not the work) → mitigation: score is advisory, not a gate; the gates (evidence, ship) stay the real authority.
- **Token cost of contextual retrieval** → mitigation: capped, one-line, task-type keyword + repo signal only (no history dump).

## 9. Deferred to later releases

- **v1.7.0:** skill-invocation proof (agent-level instrumentation), architectural fitness functions, full task-context retrieval, multi-device sync.
- **Never:** cloud services, personal memory into repo, weakening the local/One Man boundary.

## 10. Why each capability belongs in v1.6.0

| Capability | Why v1.6.0, not later |
|---|---|
| Debt register | The **highest-value mechanical gap** — debt already exists (review/ship/perf findings) but is discarded at turn-end; capturing it is the natural extension of the evidence store |
| Drift checks | Generalizes an **existing, proven check** (plan-check) — low risk, immediate value |
| Health score | **Aggregates existing signals** (stats, debt, drift) — no new data, just a verdict |
| Contextual retrieval | Small extension of `lessons.relevant` — the brief's "engineering intelligence" starts here; full task-context matching is the v1.7.0 refinement |

**The through-line:** v1.5.x proved *enforcement + learning*. v1.6.0 adds the *intelligence layer* — debt awareness, drift detection, health signal — all built on existing data, none requiring new ceremony or weakening the privacy boundary.

---

## Self-challenge (the brief's requirement)

- **Am I adding ceremony?** The debt register risks it. Mitigation: it's written by hooks that already run (no new hooks), aggregated into one score (not a dashboard), and expiry auto-closes stale entries. If it becomes unused within a release, remove it — the score survives.
- **Is the health score overengineering?** One number from existing data, advisory, not a gate. If it's noise, it's one script to delete. The alternative (no signal) is worse.
- **Is contextual retrieval scope-creep?** Kept minimal: task-type keyword + repo signal, capped, one-line. The brief names it explicitly ("engineering intelligence") — it belongs.
- **Simplest architecture?** Three new artifacts (debt, drift, health), all small, all consuming existing data, zero new plugins/hooks-of-new-kind. This is the smallest set that moves from *enforcement* to *intelligence*.

*End of assessment. No code modified. Ready for design approval before implementation.*
