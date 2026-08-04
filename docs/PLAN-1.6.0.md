# One Man v1.6.0 — Policy-Driven Engineering Operating System (Implementation Plan)

**Status:** Approved architecture — implementation spec
**Date:** 2026-08-04
**Based on:** ASSESSMENT-1.6.0-final.md (approved) + final approval brief (11 layers, fitness, constitution)
**Foundation preserved:** evidence architecture, lesson architecture, privacy model, portability model (v1.5.x untouched)

---

## 1. The 11 architectural layers (each exactly one responsibility)

```
1. ENGINEERING PRINCIPLES   — immutable values (evidence over assumption, privacy,
                              CI as authority...). Never change automatically.
2. VERSIONED POLICIES       — deterministic behavior: controls.json, flow.json,
                              obligations map. Lifecycle: version/validate/deprecate.
3. ENGINEERING KNOWLEDGE    — advisory external input (seed, community). Never
                              overwrites policy directly.
4. EVIDENCE                 — the v1.5.x evidence store + decision records.
5. POLICY FITNESS           — per-policy health: fires, regressions, overrides,
                              false-positives. NEW telemetry store.
6. POLICY PROMOTION         — knowledge → evidence → validation → regression →
                              fitness → candidate → NEW policy version. Traceable.
7. POLICY RUNTIME           — policy-runtime.py: consumes task+repo+evidence+lessons+
                              policies → deterministic execution plan.
8. AUTONOMOUS EXECUTION     — gates execute; debt/drift/docs-sync/ADR decided.
9. VERIFICATION             — suite + gates + evidence non-stale → "done" proven.
10. LESSONS                 — corrections → ledger (lifecycle) → recurrence.
11. CONTINUOUS IMPROVEMENT  — recurrence/fitness → promotion proposal → regression.
```

## 1.5 Every layer must justify its existence

For each layer: responsibility, failure prevented, inputs, outputs, why it exists,
why it cannot merge. The full justification table:

| Layer | Responsibility | Prevents | Inputs | Outputs | Cannot merge because |
|---|---|---|---|---|---|
| Principles | immutable values | policy churn on values | — | stable constraint set | merging into policies would let them drift |
| Policies | deterministic behavior | behavior drift | principles | versioned rules | merging into runtime would lose traceability |
| Knowledge | advisory input | AI-whim overwrite | external sources | proposals | merging into policies would lose the promotion gate |
| Evidence | proof of state | unproven done | actions | decision records | merging into lessons loses per-task state |
| Fitness | policy health | zombie policies | telemetry | healthy/watch/zombie verdicts | merging into promotion loses continuous signal |
| Promotion | governed evolution | untraceable change | candidates + validation | new policy versions | merging into knowledge would allow silent overwrite |
| Runtime | deterministic evaluation | duplicated judgement | policies+evidence+lessons | execution plan | merging into execution loses the single evaluator |
| Execution | run the gates | manual process | plan | debt/drift/docs/ADR | merging into runtime would couple decision+action |
| Verification | prove done | false completion | suite+gates+evidence | verified state | merging into execution loses the independent check |
| Lessons | learning loop | repeated mistakes | corrections | ledger entries | merging into improvement loses the lifecycle |
| Improvement | evidence-backed evolution | static policy | recurrence+fitness | promotion proposals | merging into lessons loses the governance gate |

## 2. Engineering rationale (each layer's sole responsibility + the mistake it prevents)

| Layer | Prevents |
|---|---|
| Principles | policy churn on values (they must be stable) |
| Policies | behavior drift from documentation (policies ARE behavior) |
| Knowledge | AI-whim policy overwrite (advisory only) |
| Evidence | unproven "done" |
| Fitness | zombie policies (unused/overriding policies persist silently) |
| Promotion | untraceable policy change |
| Runtime | duplicated judgement (one evaluator) |
| Autonomous execution | manual process (gates run it) |
| Verification | false completion |
| Lessons | repeated mistakes (learning loop) |
| Improvement | static policy (evidence-backed evolution only) |

## 3. Policy lifecycle (layer 2)

- **Version:** `policy_version` field in controls.json/flow.json/obligations; decisions carry it.
- **Validate:** CI fixture — policy parses, deterministic, no unknown keys.
- **Deprecate:** old version marked `deprecated`, migration note, decision record shows which version applied.
- **Compatibility:** additive changes only within a minor; breaking = new major.

## 4. Knowledge lifecycle (layer 3 → 6)

```
knowledge (seed/community)
  → PROPOSE (improvement proposal: what, why, evidence)
  → VALIDATE (regression: does it break existing decisions? fixture)
  → FITNESS (does it improve outcomes? fire/override/false-positive deltas)
  → APPROVE (human if no-policy/safety/irreversible; else auto)
  → PROMOTE (new policy version, old deprecated, traceable)
  → VERIFY (CI green on new version)
```

## 5. Policy fitness lifecycle (layer 5)

- **Telemetry store** (`~/.claude/fitness/<policy>.json`): per-policy counters — fires, regressions, overrides, false-positives, last-seen.
- Fed by: the Policy Runtime (fires), evidence gate (regressions), override path (overrides), lesson ledger (false-positive pattern → policy).
- **Fitness verdict:** healthy (low override/false-positive rate) / watch (rising) / zombie (no fires in N sessions → deprecation candidate).
- **Report:** surfaced at SessionStart (one line) + CI.


## 2.5 Trust hierarchy (knowledge is not equally trustworthy)

| Trust level | Source | May propose? | May overwrite policy? |
|---|---|---|---|
| 1 (highest) | Engineering Principles | never | never |
| 2 | Versioned Engineering Policies | — | — (they ARE policy) |
| 3 | Official specs / language standards | yes | never silently |
| 4 | Official tooling/framework docs | yes | never silently |
| 5 | Verified empirical engineering evidence | yes | never silently |
| 6 | Community best practices | propose only | never |
| 7 (lowest) | AI model recommendations | propose only | never |

Knowledge produces evidence; evidence qualifies a Policy Candidate; regression +
fitness validate the candidate; only then may a new policy version be promoted.
All promotions versioned + traceable.

## 6. Promotion lifecycle (layer 6)

The governance gate: a promotion candidate requires evidence + regression + fitness delta. **Evidence alone never silently activates a policy.** All promotions traceable (who/what/when/why) + versioned.

## 7. Autonomous execution flow (layers 7-8)

```
PROMPT
  → policy-runtime.py (layer 7): type + risk + obligations + review/evidence requirements
    from policies + evidence + lessons + repo state
  → EXECUTION (layer 8): gates run; decisions made:
      debt created? (review/ship/perf findings → classified)
      drift flagged? (change → affected artifacts, severity, owner, sync action)
      docs-sync needed? (README/CHANGELOG/plans/ADR list)
      ADR warranted? (architectural? → lightweight ADR flag)
  → EVIDENCE (layer 4): every action recorded (result, exit, files, state_hash)
  → VERIFICATION (layer 9): suite + gates + non-stale evidence → done proven
  → LESSONS (layer 10): correction → ledger → recurrence detection
  → IMPROVEMENT (layer 11): recurrence/fitness → proposal → regression → policy
```

## 8. Constitutional rules (non-negotiable, enforced)

| Rule | Enforcement |
|---|---|
| Never bypass evidence | evidence-gate (existing) |
| Never bypass CI as final authority | CI runs all gates (existing) |
| Never bypass privacy | seed test + scan (existing) |
| Never overwrite policy from knowledge | promotion gate (NEW) |
| Never silently introduce drift | drift decision (NEW) + approval-to-skip recorded |
| Never silently introduce undocumented policy | policy versioning (NEW) |
| Never silently discard evidence | evidence store (existing) |
| **Engineering behaviour must never change silently** | every policy evolution observable, versioned, reproducible, explainable (NEW) |

## 9. Revised implementation milestones

| # | Milestone | Layer | Files |
|---|---|---|---|
| M1 | Policy versioning + validation | 2 | controls.json, flow.json, obligations map, CI fixture |
| M2 | Policy fitness telemetry | 5 | `hooks/lib/fitness.py` (new) + writers |
| M3 | policy-runtime.py — the Policy Runtime | 7 | `hooks/lib/policy-runtime.py` (new) + parity test |
| M4 | Debt as policy output | 8 | `hooks/lib/debt.py` (new) + writers (review/ship/perf) |
| M5 | Drift as policy output | 8 | `scripts/drift-check.py` (new) + classification |
| M6 | Docs-sync + lightweight ADR | 8 | `scripts/docs-sync.py` (new), ADR template |
| M7 | Promotion gate | 6 | `scripts/promote.py` (new) + CI fixture |
| M8 | Release readiness + release | 9, 11 | `scripts/readiness.py` (new), CHANGELOG, tag — pending approval |

## 10. Acceptance criteria

- **M1:** ✅ DONE — policy_version added to controls.json + flow.json; scripts/validate-policies.py (parse + version + strict-schema keys for controls, structure-only for flow); CI job added. 4 assertions; 22/22 runner.
- **M2:** ✅ DONE — hooks/lib/fitness.py (applications/successes/regressions/overrides/false_positives/maintenance per policy; healthy/watch/zombie verdict; one-line report). 7 assertions; 23/23 runner.
- **M3:** policy_runtime() parity with current hooks (same verdicts); deterministic. 6 assertions.
- **M4:** debt auto-created, classified, lifecycle, expires, blocks only acknowledged+unfixed+high-risk at release. 7 assertions.
- **M5:** drift classified (severity/owner/artifacts/sync-action); verified→closed; approval-to-skip recorded. 6 assertions.
- **M6:** docs-sync lists correct artifacts for a change; ADR flagged for architectural. 4 assertions.
- **M7:** promotion requires evidence+regression+fitness; evidence-alone rejected; traceable. 5 assertions.
- **M8:** readiness aggregates gates+debt+drift; 21+ self-checks, CI green both OSes, privacy clean, plan-check `[x]`.

## 11. Risks

- **Layer ceremony** (11 layers of documentation) → layers are a mental model; implementation is 4 new small modules (fitness, decide, debt, drift) + 2 scripts (docs-sync, promote) + versioning fields. No daemons, no services.
- **Fitness becomes a dashboard** → one-line SessionStart report + CI check, not a UI.
- **Promotion over-governance** → auto-approve evidence-backed low-risk; human only for safety/irreversible.
- **Drift false-positives** → advisory-first, approval-to-skip.
- **Debt bloat** → expiry auto-closes.

## 12. Deferred

- **v1.7.0:** skill-invocation proof (agent instrumentation), architectural fitness functions, full task-context retrieval, multi-device sync, policy UI.
- **Never:** cloud, personal memory into repo, weakening the local/One Man boundary.

## 13. Migration from v1.5.x

- **Backward-compatible:** all v1.5.x hooks/lib keep working; new modules are additive.
- **Parity test (M3)** guarantees policy_runtime() matches current hook verdicts — no behavior change at migration.
- **Evidence/lessons/privacy/portability untouched** (per constitution).
- Rollback: each milestone independently revertible; the parity test is the safety net.

## 14. Comparison against previous architectures

| | v1.5.x (harness) | v1.6.0 (policy OS) |
|---|---|---|
| Decisions | implicit, scattered | **versioned policies → deterministic** |
| Policies | static JSON | **lifecycle: version/validate/deprecate** |
| Knowledge | static seed | **evidence-backed promotion** |
| Fitness | none | **telemetry: fires/overrides/false-positives** |
| Autonomy | gates enforce | **autonomous; human-only-when-needed** |
| Drift/debt | none | **policy outputs with lifecycle** |
| Improvement | seed+self-evolve | **promotion loop, traceable** |
| Constitution | implicit | **7 explicit non-negotiable rules** |

---

## Self-challenge (final)

- **"Are 11 layers overkill?"** — They're a mental model with 1 responsibility each; the implementation is 4 modules + 2 scripts. The layers prevent the exact failure of the component-proposal (systems that don't evolve). Kept, minimal.
- **"Is fitness a dashboard?"** — It's counters + one-line report + zombie detection. Without it, policies can't prove usefulness (the brief's explicit requirement). Kept, minimal.
- **"Is policy-runtime.py redundant?"** — Parity test (M3) proves it matches the hooks; if it duplicates, delete. It adds the statefulness (decision record) that makes fitness/lessons possible. Kept with the test.
- **"Could this be simpler?"** — The v1.5.x foundation is untouched. The additions are the minimum that transforms "automated" into "autonomous + self-adapting": versioning (traceability), fitness (evidence of usefulness), decide (one evaluator), promotion (governance), debt/drift/docs-sync/readiness (policy outputs). Each justified by a specific mistake it prevents (§2).

*End of implementation plan. Architecture approved — ready to implement on your go.*
