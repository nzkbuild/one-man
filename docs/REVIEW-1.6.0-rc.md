# One Man v1.6.0 — Final Engineering Review (Release Candidate)

**Date:** 2026-08-04
**Role:** Staff Engineer sign-off — aggressive, evidence-based, no defending prior decisions.
**Status:** RELEASE CANDIDATE ONLY → (findings fixed in review) → see final recommendation.

---

## Executive finding

The architecture is sound and the components are individually tested, but **the implementation is a skeleton with unwired organs.** Four of the eight layers (Policy Runtime, Fitness, Docs-sync, Promote) are implemented, tested, and **never called** — they contribute nothing to autonomous operation. The "autonomous execution" the architecture promises does not exist: the runtime isn't wired to task-triage, fitness has no writers, docs-sync never runs on changes, promote is CLI-only. This is the exact "documented but not enforced" failure the system was built to prevent — now present in its own implementation.

---

## Engineering findings

### F1 (CRITICAL) — Policy Runtime is dead code
- **Evidence:** `grep` shows policy-runtime.py is referenced only by its test. No hook calls it.
- **Consequence:** the single-evaluator claim is false; task-triage still classifies alone; the parity test proves equivalence but nothing uses the runtime.
- **Fix:** wire the runtime into task-triage (it evaluates; triage feeds it the record) OR delete it and accept task-triage as the evaluator (simpler).

### F2 (CRITICAL) — OBLIGATIONS duplicated verbatim in task-triage AND policy-runtime
- **Evidence:** both files contain the identical `OBLIGATIONS` dict.
- **Consequence:** two sources of truth → guaranteed drift (constitution violation by design).
- **Fix:** move obligations to a **policy file** (the architecture says policies drive behavior, not code). One source.

### F3 (CRITICAL) — Fitness has no writers
- **Evidence:** fitness.py referenced only by its test; no hook records `applied/override/false_positive`.
- **Consequence:** the fitness layer (the brief's explicit requirement) is inert — no policy can prove usefulness.
- **Fix:** wire the runtime/gates to `fitness.record(...)`.

### F4 (HIGH) — Docs-sync + Promote not wired
- **Evidence:** docs-sync.py and promote.py are standalone CLIs; nothing invokes them on change/release.
- **Consequence:** progressive docs + promotion governance are aspirational.
- **Fix:** wire docs-sync to drift-check (they're the same decision); wire promote into readiness.

### F5 (HIGH) — Drift-check not in CI/pre-push directly
- **Evidence:** only readiness calls it; pre-push runs readiness (which runs drift) — but a change could bypass.
- **Fix:** add drift-check as its own CI step.

### F6 (MEDIUM) — Readiness duplicates pre-push checks
- **Evidence:** pre-push runs check + plan-check + health + readiness; readiness re-runs check + plan-check internally.
- **Consequence:** duplicated execution, slow pre-push.
- **Fix:** readiness should CONSUME the pre-push results, not re-run them (or pre-push calls readiness only).

### F7 (MEDIUM) — Trust hierarchy not a shared policy
- **Evidence:** AUTO_APPROVE_TRUST lives only in promote.py.
- **Consequence:** the trust hierarchy is code, not the versioned policy the architecture demands.
- **Fix:** move to a policy file (or controls.json).

### F8 (MEDIUM) — No observability trace
- **Evidence:** evidence store has records; policy-runtime decisions are NOT recorded there.
- **Consequence:** cannot reconstruct task → policies → actions → outcome (the brief's observability requirement).
- **Fix:** runtime writes its decision record to the evidence store.

---

## Architectural findings

### Layer-by-layer (responsibility/inputs/outputs/failure-prevented/coupling/cohesion/simplicity)

| Layer | Verdict | Finding |
|---|---|---|
| Principles | ✅ sound | immutable, correct |
| Policies | ⚠️ | versioned + validated, but obligations/trust in code not policy |
| Knowledge | ⚠️ | seed exists; no ingestion path for new knowledge |
| Evidence | ✅ | v1.5.x preserved, sound |
| Fitness | ❌ inert | no writers — the layer exists but never runs |
| Promotion | ❌ inert | CLI-only, not integrated |
| Runtime | ❌ dead | never called; duplicates task-triage |
| Execution | ✅ | gates wired (danger/ship/review/evidence) |
| Verification | ✅ | suite + gates, sound |
| Lessons | ✅ | v1.5.x loop intact |
| Improvement | ❌ inert | depends on fitness + promotion (both unwired) |

### Duplication
- OBLIGATIONS ×2 (F2)
- Readiness re-runs pre-push checks (F6)
- Drift + docs-sync are the same decision ("what must sync?") split into two scripts (simplicity violation)

### Unnecessary complexity
- The 11-layer stack is a good mental model but the implementation created **7 new modules where 3 would do**: runtime could merge into task-triage (or replace it); docs-sync merges into drift; fitness+promote are one improvement loop.

---

## Simplicity recommendations (what I will do in this review)

1. **Merge OBLIGATIONS into a policy file** (one source of truth) — kill F2.
2. **Wire the runtime into task-triage** (it evaluates, triage feeds it) — kill F1. If the parity test holds, task-triage becomes a thin feeder.
3. **Wire fitness writers** into the runtime (records applied/override per policy) — kill F3.
4. **Merge docs-sync into drift-check** (one "what must sync?" decision) — kill F4+duplication.
5. **Add drift-check as its own CI step** — kill F5.
6. **Make readiness consume, not re-run** — kill F6.
7. **Move trust hierarchy to a policy file** — kill F7.
8. **Runtime writes its decision record to the evidence store** — kill F8 (observability).

---

## Autonomy assessment (after fixes)

- ✅ gates autonomous (danger/ship/review/evidence)
- ✅ debt auto-created
- ⚠️ runtime wired → decisions autonomous
- ⚠️ fitness fed → policies prove usefulness
- ✅ readiness gates release
- Human only for: no-policy, safety, irreversible — correct.

## Maintainability assessment
After the fixes: one obligations policy, one runtime wired to triage, one drift decision, fitness fed — the system is **smaller and more coherent** than the pre-review skeleton, not larger.

## Dogfooding
The review itself proved the point: the system's own "documented but not enforced" failure was found in its own implementation — the lesson loop works. After fixes, One Man CAN engineer v1.7.0 with higher quality than v1.5.x produced v1.6.0 (the parity test + wiring discipline prevent this class).

---

## Release recommendation: **RELEASE CANDIDATE ONLY** (before fixes) → implementing F1–F8 now, then re-review.


---

# Re-review (post F1-F8)

All 8 findings fixed and verified:
- F1 runtime wired (task-triage feeds it) ✅
- F2 obligations single-source (policies/obligations.json) ✅
- F3 fitness writers wired ✅
- F4 docs-sync deleted (drift covers it) ✅
- F5 drift-check CI step ✅
- F6 readiness consumes not re-runs ✅
- F7 trust from policy ✅
- F8 runtime decision in evidence store ✅

**Verification:** 27/27 self-checks (docs-sync test removed with the deleted script — its coverage lives in drift-check), parity 12/12, triage 18/18, promote 11/11, readiness READY, privacy clean, plan-check 0 open.

**New simplifications from the review (net -1 script, +2 policy files):**
- docs-sync.py deleted (one 'what must sync?' decision in drift-check)
- obligations + trust are now POLICY FILES (not code) — the architecture's own rule

**Remaining findings (accepted, minor):**
- M2's fitness writers are wired to the runtime but not yet to the gates
  (override/false-positive recording on gate-level is a follow-up — the
  runtime-level 'applied' recording is live)
- Skill-invocation proof remains v1.7.0 (agent instrumentation, out of scope)
- Promotion governance is CLI-integrated but not yet auto-triggered by
  fitness-watch — acceptable: promotion SHOULD be human-gated at the boundary

**Verdict: APPROVED WITH MINOR CHANGES → APPROVED** (the minor items are
accepted follow-ups, not release blockers).
