# One Man v1.7.0 — Local Claude Code Reality and Wiring Audit

**Date:** 2026-08-04
**Method:** Evidence-based — traced every capability to its consumer via grep + live-file checks + session transcript. Existence ≠ operation; green tests ≠ wired.

---

## 1. Local Claude Code system map

| Layer | Local files | Wired? | Consumer |
|---|---|---|---|
| Hooks (32 entries) | `~/.claude/hooks/` | ✅ live settings | 10 events |
| Policy Runtime | `~/.claude/hooks/lib/policy-runtime.py` | ✅ via task-triage (verified 2 refs) | UserPromptSubmit |
| Policies | `~/.claude/policies/` **MISSING** | ❌ falls back to repo path | runtime (repo-only) |
| Fitness | `~/.claude/hooks/lib/fitness.py` + `~/.claude/fitness/policy-1_6_0.json` | ✅ runtime records | verdict/report (no consumer yet) |
| Debt | `~/.claude/hooks/lib/debt.py` | ✅ review-gate writes | readiness (repo-only) |
| Drift | **MISSING live** | ❌ CI + readiness (repo-only) | release |
| Readiness | **MISSING live** | ❌ pre-push (repo-only) | release |
| Evidence | `~/.claude/hooks/lib/evidence.py` | ✅ verify-turn + triage | gate |
| Lessons | `~/.claude/hooks/lib/lessons.py` | ✅ self-evolve + session-context | recurrence |
| Skills (8+13) | live | ⚠️ routed; execution unproven | flows |
| Plugins (6) | live enabled | ✅ | on-demand |

## 2. Capability + wiring matrix (who calls / trigger / input / output / consumer / skip-fail)

| Capability | Called by | Trigger | Output | Consumer | Skipped→ | Fails→ |
|---|---|---|---|---|---|---|
| task-triage | hook | prompt | type/risk/obligations + runtime plan | evidence store | no briefing | fail-open |
| **Policy Runtime** | task-triage | prompt | execution plan | evidence + fitness | no plan | fail-open |
| **Fitness** | runtime | prompt | applied-record | verdict (NO consumer yet) | no telemetry | fail-open |
| **Debt** | review-gate | Stop findings | debt entry | readiness (repo-only) | debt lost | fail-open |
| **Drift** | CI + readiness | push/release | drift report | release gate | drift silent | fail-open |
| **Readiness** | pre-push | push | READY/NOT-READY | push block | no gate | fail-open |
| Evidence | verify-turn | Stop | test evidence | gate | unproven done | fail-open |
| Lessons | self-evolve | correction | ledger entry | session-context | no learning | fail-open |

## 3. Trigger-to-consumer traces (verified)

**Prompt trace (WORKS end-to-end):**
```
raw prompt → task-triage hook (UserPromptSubmit) → classify(type/risk)
→ policy-runtime.evaluate() → plan (obligations from policies/obligations.json,
  workflow, review/evidence reqs) → evidence record seeded → fitness.record(applied)
→ briefing injected → model acts
```
**Verified:** 42 runtime mentions in session transcript; `policy-1_6_0.json` exists.

**Stop trace (WORKS in repo):**
```
Stop → verify-turn (suite + evidence) → review-gate (findings → debt.create)
→ ship-gate → evidence-gate (obligations + staleness) → done-or-block
```

**Release trace (WORKS in repo, NOT live):**
```
pre-push → check + health + plan-check + readiness (debt + drift + version)
→ push → CI (self-checks + policy-validate + lesson + evidence + drift jobs)
```
**Live gap:** drift-check/readiness/policies are repo-only — pre-push on a fresh
machine has no readiness, no drift, no policies.

## 4. Local vs One Man parity matrix

| Capability | Carried correctly | Outdated | Absent from One Man | Local-only |
|---|---|---|---|---|
| Hooks | ✅ | — | — | — |
| Runtime | ✅ (file) | — | — | — |
| **Policies** | ❌ **NOT installed by installer** | — | ❌ **the v1.6.0 policy layer is not portable** | — |
| Fitness | ✅ file | — | verdict no consumer | telemetry local |
| Debt | ✅ | — | — | entries local |
| Drift/Readiness | ✅ repo | — | ❌ not installed live | — |
| Evidence/Lessons | ✅ | — | — | records local |
| Skills/Plugins | manifest | ⚠️ | design skills symlinked | — |

## 5. Privacy/portability classification
- **Local-only (correct):** evidence/debt/fitness/lesson records, memory, credentials, paths.
- **One Man (correct):** hooks, runtime, lib, scripts, tests, policies — **EXCEPT policies aren't installed** (bug).

## 6. Dead / unwired / unused / bypassable
1. **policies/ not copied by installers** (CRITICAL — portability broken)
2. **Fitness verdict has NO consumer** (report exists, nothing reads it)
3. **drift-check + readiness not installed live** (repo-only)
4. **Promotion not auto-triggered** (CLI-only; acceptable — human-gated)
5. **13 design skills routed, execution unproven** (the standing v1.7.0 gap)
6. **review-gate debt writer** — works, but debt has no live consumer outside repo

## 7. Token/latency findings
- task-triage + runtime: 2 python launches per prompt (~small, acceptable)
- 32 hook entries × per-event python = real per-turn cost (pre-existing, known)
- fitness.record: one JSON write per prompt — negligible
- **No new token bloat introduced by v1.6.0** (all lightweight, local, one-line)

## 8. Required local fixes (before v1.7.0)
1. **Installers must copy `policies/`** → the policy layer becomes portable (the #1 blocker)
2. **Sync drift-check + readiness to live** (they exist in repo; live env lacks them)
3. **Give fitness verdict a consumer** (SessionStart one-line, or fold into readiness)
4. Re-run install → verify live parity

## 9. Safe promotion candidates
- Installer policies/ copy fix (portable, privacy-safe)
- Fitness verdict → readiness (aggregates telemetry into the release gate)
- drift/readiness live sync (already generalized)

## 10. Verified baseline required before v1.7.0
- Live `~/.claude/policies/` exists + matches repo
- drift-check + readiness installed live + pre-push wired
- Fitness verdict consumed (not just recorded)
- Install on a fixture HOME → policy layer present

## 11. Concise v1.7.0 architecture plan (from findings ONLY)
1. **Fix portability** (installers copy policies/) — the v1.6.0 layer must reproduce
2. **Close the fitness-consumer gap** (verdict → SessionStart + readiness)
3. **Skill-invocation proof** (the standing gap: 13 design skills routed, unproven)
4. **Autonomous discovery** (the brief's goal) — only after 1–3, because the
   current system can't be trusted on a fresh machine without policies

---

## The audit's answer
- **What local Claude Code actually does:** prompt→runtime→evidence→gates works end-to-end (verified: 42 runtime fires, fitness recording, debt from findings).
- **What genuinely activates and affects outcomes:** task-triage/runtime/evidence/debt (in-repo), gates, lessons.
- **Dead/unwired/skipped:** fitness verdict (no consumer), policies not installed, drift/readiness not live, promotion CLI-only, design-skill execution unproven.
- **What One Man accurately reproduces:** hooks, runtime, lib, evidence/lessons — **NOT the policy layer (installer gap).**
- **What must be repaired before autonomous discovery:** the portability gap + live sync + fitness consumer. Until policies/ installs, One Man cannot reproduce the v1.6.0 operating system on a fresh machine.
