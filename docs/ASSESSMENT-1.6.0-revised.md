# One Man v1.6.0 — Revised Architecture: Engineering Judgment First

**Date:** 2026-08-04
**Status:** Assessment only — no implementation (per brief)
**Reframe:** Not "add components" but "make the system think like an engineering lead." Start from decisions, not features.

---

## 1. Re-evaluated architecture — from decisions, not components

### The insight (verified)
The system **already makes engineering decisions** today, but they are:
- **implicit** — encoded in hook branches, not a named decision
- **scattered** — type/risk in task-triage, proven-done in gate, high-risk in review-gate
- **stateless** — a decision (e.g. "this is high-risk") is made, used, discarded; nothing learns from it
- **missing owners** — debt, drift, docs-sync, ADR have no decision point (verified: absent)

### The revised architecture
**One judgment layer — the Engineering Decision Engine — that consumes what exists and makes the decisions explicit + stateful.** It does NOT replace the hooks; it *centralizes the decision logic* they already run, so a decision is: named, recorded, retrievable, learnable.

```
EXISTING (consumed, not replaced)          DECISION ENGINE (new judgment layer)
─────────────────────────────              ─────────────────────────────────────
task-triage: type/risk/obligations   ──►   per task:
evidence-gate: proven-done?               • workflow selection (from type+risk)
review-gate: high-risk?                   • obligation selection (from type)
ship-gate: dead-code?                     • review requirement (high→isolated)
perf-guard: N+1?                          • evidence requirement (med/high→proof)
retrospective: stats                      • lesson creation (correction→ledger)
lesson ledger: lifecycle                  • debt creation (finding→debt, classified)
                                          • drift classification (change→affected docs)
                                          • docs-sync decision (what must update)
                                          • ADR decision (architectural?→ADR)
                                          • release readiness (all gates→verdict)
```

**The Engine is a decision function, not a daemon.** It answers "what should happen for this task/change?" — returning a structured decision record. The existing hooks call it; the gates enforce its output; the ledger/evidence store persist it.

## 2. Should the Decision Engine exist?

**Yes — but as a *decision function*, not a component.** The evidence: the system already makes these decisions implicitly; the Engine makes them explicit, consistent, and stateful. It consumes (task record, evidence, findings, lessons) — it does not add data sources. Without it, v1.6.0's components (debt, drift, docs-sync) would each re-derive "what kind of change is this?" — duplicated judgment, exactly the drift the system fights.

**The counter-argument (self-challenge):** "Is this just an orchestrator/ceremony?" — No: the decisions exist today; centralizing them removes duplication and makes them auditable. The Engine is a **pure function** (`decide(task_record, findings, lessons) → decision_record`), ~100 lines, tested like a hook. If it adds no value over the implicit branches, delete it — the hooks still work.

## 3. Updated v1.6.0 scope

| Capability | Decision it makes | When | Auto vs approval |
|---|---|---|---|
| **Decision Engine** (`hooks/lib/decide.py`) | workflow/obligation/review/evidence selection per task | prompt-time | auto (advisory output, gates enforce) |
| **Debt creation** | is this finding engineering debt? classify (tech/process/design) | finding-time (review/ship/perf) | auto-create; **advisory** (never blocks by itself); expires |
| **Debt lifecycle** | open → acknowledged → fixed → expired | life of the debt | auto-expire after N releases; **block only if debt is acknowledged+unfixed+high-risk** |
| **Drift classification** | does this change require doc/plan/ADR sync? | change-time | auto-flag; **explicit approval** to skip (recorded) |
| **Docs-sync decision** | which artifacts (README/CHANGELOG/plans/ADR) must update | change-time | auto-recommend; **approval** to skip |
| **ADR decision** | is this architectural? → lightweight ADR | change-time | auto-flag; **approval** to write |
| **Release readiness** | are all gates green for release? | release-time | auto-verdict (existing gates, aggregated) |

**Debt semantics (the brief's question):**
- **auto** when a finding is mechanical (bare except, TODO left, N+1) — recorded as debt
- **advisory** by default — never blocks alone
- **blocks** only when: acknowledged + unfixed + high-risk + release-time (the release readiness verdict)
- **expires** after N releases with no action (stale debt auto-closes, keeps the register honest)

**Drift semantics:**
- **classification** (docs/plan/version/architecture) + **severity** (low/med/high) + **owner** (the change that caused it) + **recommended action** (which doc to sync) + **verification** (did the sync happen) + **closure** (drift resolved)

## 4. Revised milestones

| # | Milestone | Decision made |
|---|---|---|
| M1 | `decide.py` — the decision function (workflow/obligation/review/evidence per task) | centralize existing decisions |
| M2 | Debt: creation + classification + lifecycle (writers from review/ship/perf findings) | is this debt? |
| M3 | Drift: classification + severity + owner + recommended action + closure | what must sync? |
| M4 | Docs-sync + ADR decisions (auto-flag, approval-to-skip, lightweight ADR) | what documentation? |
| M5 | Release readiness (aggregate gates + debt + drift → verdict) | is it releasable? |
| M6 | Release prep (version 1.6.0, CHANGELOG, CI, tag) — pending approval | |

## 5. Acceptance criteria

- **M1:** decide() returns the same workflow/obligation/review/evidence as the hooks today (parity test); decision record persisted. 6 assertions.
- **M2:** a review-gate bare-except finding → debt entry (classify tech), lifecycle open→fixed→expired; debt never blocks alone; blocks only acknowledged+unfixed+high-risk at release. 7 assertions.
- **M3:** a change touching README-relevant paths → drift flagged (severity, owner, action); sync verified → closed; skip requires approval. 6 assertions.
- **M4:** architectural change → ADR flagged; docs-sync lists the right artifacts. 4 assertions.
- **M5:** release readiness verdict = all gates + debt + drift; blocks when high-risk debt open. 4 assertions.
- **M6:** 21+ self-checks, CI green both OSes, privacy clean, plan-check `[x]`.

## 6. Risks

- **Engine becomes ceremony** → it's a pure function consuming existing data; if it duplicates (not centralizes) decisions, delete it. Parity test (M1) proves it matches the hooks.
- **Debt register bloats** → expiry auto-closes stale; advisory-only by default.
- **Drift false-positives** → advisory-first, approval-to-skip recorded.
- **ADR ceremony** → lightweight: 5-line template (decision/why/alternatives), approval-gated, never forced.

## 7. Deferred

- **v1.7.0:** skill-invocation proof (agent instrumentation), architectural fitness functions, full task-context retrieval, multi-device sync.
- **Never:** cloud, personal memory into repo, weakening the local/One Man boundary.

## 8. Engineering rationale (every capability)

| Capability | The mistake it prevents | The cost it reduces |
|---|---|---|
| Decision Engine | Duplicated/implicit judgment (each hook re-derives "what kind of change?") | maintenance + drift |
| Debt register | Debt discovered, fixed, forgotten — no lifecycle | re-discovery + recurrence |
| Drift classification | Docs/plans silently diverge from code (the plan-check lesson, generalized) | doc debt + misdirection |
| Docs-sync | Manual doc updates skipped | stale docs (worse than none) |
| ADR | Architectural decisions lost to tribal memory | re-derivation + wrong choices |
| Release readiness | "Looks done" ≠ "is done" (the evidence lesson, aggregated) | bad releases |

## 9. Simplifications made (vs the previous proposal)

1. **Removed the standalone health-score component** — the release-readiness verdict (M5) *is* the health signal, aggregated at the right time (release), not a dashboard.
2. **Removed contextual-retrieval extension** — the Engine's decision record *is* the retrieval context (per-task decisions, not a task-matching system). Full retrieval stays v1.7.0.
3. **Merged drift + docs-sync + ADR into ONE decision** ("what must sync?") — one judgment, three outputs, not three components.
4. **Debt and drift share the lifecycle pattern** (open→closed, auto-expire) — one mechanism, two uses.

## 10. Comparison: previous vs revised

| | Previous (component-oriented) | Revised (judgment-first) |
|---|---|---|
| Debt register | a component | a *decision* ("is this debt?") with lifecycle |
| Drift checks | a component | a *decision* ("what must sync?") with classification/closure |
| Health score | a component | absorbed into release readiness |
| Contextual retrieval | a component | absorbed into the decision record |
| **Core** | 4 features | **1 decision function + 3 outputs** |

**Why the revised is better:** the previous proposal would have produced four systems that each re-derive "what kind of change is this?" — duplicated judgment. The revised produces ONE judgment layer that answers the question once, and the four outputs (debt, drift, docs-sync, readiness) fall out of it. Fewer moving parts, less duplication, decisions auditable and learnable — the system thinks like a lead, not like a toolkit.

---

**Self-challenge (final):** "Is the Engine just a refactor?" — It's a refactor *plus* the missing statefulness: today a decision is made and discarded; the Engine persists it (decision record), which is what makes debt/drift/lessons possible. Without the persistence, it's ceremony. With it, it's the judgment backbone. If the persistence proves unused, the Engine collapses back to the hooks — the parity test guarantees no regression.

*End of revised assessment. No code modified. Ready for design approval before implementation.*
