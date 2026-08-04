# One Man v1.6.0 — Final Architecture: Policy-Driven Engineering Operating System

**Date:** 2026-08-04
**Status:** Final review — no implementation (per brief)
**Reframe:** From harness → **Policy-Driven, Evidence-Backed, Knowledge-Adaptive Engineering Operating System**. The objective is autonomous operation with minimal supervision — the system decides, executes deterministically, verifies with evidence, and evolves only via evidence-backed promotion.

---

## 1. Core philosophy

| Principle | Meaning |
|---|---|
| **Judgement explicit** | every decision has a named owner (the policy evaluator) |
| **Deterministic work automatic** | policy → action, no manual steps |
| **Evidence verified** | nothing ships without proof against current state |
| **Drift + debt continuously reduced** | classified, owned, closed, expired |
| **Self-improving** | only via evidence-backed policy promotion, never AI whim |
| **Privacy-safe, portable, simple** | the v1.5.x boundary is inviolable |

**Human intervention only when:** no deterministic policy exists, safety uncertain, or irreversible/destructive. Everything else executes.

## 2. The architectural layers (challenged + simplified)

The brief's 9 layers are correct but can be **collapsed to 6** — two merges remove ceremony without losing function:

```
1. PRINCIPLES        (stable, ~never change — exists in CLAUDE.md)
2. POLICIES          (versioned, deterministic, drive behavior — controls.json, flow.json)
3. KNOWLEDGE         (rapidly-changing external input — seed + community)
   └─ evidence-backed PROMOTION → becomes policy (never blind overwrite)
4. POLICY EVALUATION (decide.py: task+repo+evidence+lessons → deterministic actions)
5. AUTONOMOUS ACTIONS (gates execute; evidence recorded; drift/debt/docs-sync/ADR decided)
6. VERIFICATION + LESSONS (evidence → verify → lesson → improvement proposal → regression → new policy)
```

**Merges (simplification):**
- **Knowledge Validation** merges into **Knowledge** (validation IS the promotion gate — one mechanism)
- **Policy Evaluation** and **Automatic Actions** merge (evaluation output IS the action; no separate dispatch)

**Why 6 not 9:** the brief's layers 4-5 and 7-8-9 are one mechanism each, split for clarity. Collapsing removes the "policy evaluation" ceremony of a separate component — the decision function IS the evaluation, and the gates ARE the actions.

## 3. Policy lifecycle (the core gap — policies don't evolve today)

| Stage | Mechanism | Auto/approval |
|---|---|---|
| **Create** | policy file (controls.json, flow.json) — versioned | policy author |
| **Validate** | self-check: policy parses + deterministic (fixture) | auto (CI) |
| **Version** | semver per policy; `policy_version` in decisions | auto (bump on change) |
| **Evaluate** | decide.py consumes the active version | auto |
| **Deprecate** | old version marked deprecated, migration note | approval |
| **Migrate** | decision record carries the policy version → audit trail | auto |

**Policies drive behavior, are NOT documentation** — they're JSON consumed by decide.py, validated in CI, versioned, auditable.

## 4. Knowledge lifecycle (the brief's "never blindly overwrite")

```
New knowledge (seed, community, practice)
  → PROPOSE (an improvement proposal, not a change)
  → VALIDATE (regression: does it break existing decisions? fixture)
  → EVIDENCE (does it improve outcomes? lesson recurrence down? debt down?)
  → APPROVE (human, if no deterministic policy / safety / irreversible)
  → PROMOTE (new policy version, old deprecated)
  → VERIFY (CI green on the new version)
```

**The rule:** knowledge becomes policy ONLY through this evidence-backed promotion. An AI recommendation alone never changes policy. This is the continuous-policy-improvement loop the brief demands, made explicit.

## 5. Autonomous execution flow (per task)

```
PROMPT
  → decide.py: task type + risk + obligations + review/evidence requirements
    (consuming: task record, repo state, evidence, lessons, policies)
  → AUTONOMOUS: gates execute (danger/ship/review/evidence)
  → DECISIONS: debt created? drift classified? docs-sync flagged? ADR flagged?
  → EVIDENCE: every action recorded (result, exit, files, state_hash)
  → VERIFY: suite + gates green → "done" proven
  → LESSONS: correction → ledger (lifecycle) → recurrence detection
  → POLICY IMPROVEMENT: recurring lesson → proposal → regression → new policy
```

**Human touches only at:** no-policy, safety-uncertain, irreversible. Everything else is deterministic.

## 6. Revised v1.6.0 milestones (from decisions, not components)

| # | Milestone | The decision it makes |
|---|---|---|
| M1 | **Policy layer**: version controls.json + flow.json; `policy_version` in decisions | what policy applies? |
| M2 | **decide.py**: the evaluator (consumes task/repo/evidence/lessons/policies → deterministic actions + decision record) | what must happen for this task? |
| M3 | **Debt as policy output**: auto-create/classify/lifecycle/expire/block-at-release | is this debt? does it block? |
| M4 | **Drift as policy output**: classify/severity/owner/sync-action/verify/close, across all artifacts | what must sync? |
| M5 | **Docs-sync + lightweight ADR**: auto-flag, approval-to-skip, 5-line ADR | what documentation? |
| M6 | **Knowledge promotion gate**: propose→validate→evidence→approve→promote→verify | does this knowledge become policy? |
| M7 | **Release readiness**: all gates + debt + drift → verdict | is it releasable? |
| M8 | Release prep (version 1.6.0, CHANGELOG, CI, tag) — pending approval | |

## 7. Acceptance criteria

- **M1:** policies versioned; decision record carries policy_version; deprecation + migration tested. 5 assertions.
- **M2:** decide() parity with current hooks (same verdicts); deterministic on fixture. 6 assertions.
- **M3:** debt auto-created from review finding, classified, expires; blocks only acknowledged+unfixed+high-risk at release. 7 assertions.
- **M4:** drift flagged with severity/owner/sync-action; verified → closed; approval-to-skip recorded. 6 assertions.
- **M5:** architectural change → ADR flagged; docs-sync lists correct artifacts. 4 assertions.
- **M6:** promotion gate: proposal without evidence rejected; with regression+evidence promoted. 5 assertions.
- **M7:** readiness verdict aggregates gates+debt+drift; blocks on high-risk open debt. 4 assertions.
- **M8:** 21+ self-checks, CI green both OSes, privacy clean, plan-check `[x]`.

## 8. Risks

- **Policy complexity** (versioning ceremony) → policies are small JSON; versioning is a field + CI check, not a system.
- **Knowledge promotion blocked by over-approval** → the gate auto-approves evidence-backed, low-risk changes; human only for safety/irreversible.
- **Drift false-positives** → advisory-first, approval-to-skip.
- **Debt bloat** → expiry auto-closes; advisory by default.
- **Over-automation** (autonomous work exceeds safety) → the philosophy's guard: human only for no-policy/safety/irreversible — the gates enforce this.

## 9. Deferred

- **v1.7.0:** skill-invocation proof (agent instrumentation), architectural fitness functions, full task-context retrieval, multi-device sync, policy UI.
- **Never:** cloud, personal memory into repo, weakening the local/One Man boundary.

## 10. Comparison: three architectures

| | v1.5.1 (harness) | v1.6.0-proposed (components) | **v1.6.0-final (policy-driven)** |
|---|---|---|---|
| Core | enforcement + learning loop | 4 components | **1 policy layer + 1 evaluator + outputs** |
| Decisions | implicit, scattered | centralized (decision fn) | **versioned policies → deterministic** |
| Knowledge | static seed | (not addressed) | **evidence-backed promotion** |
| Policies | static JSON | (not addressed) | **versioned lifecycle** |
| Autonomy | gates enforce | advisory | **autonomous, human-only-when-needed** |
| Drift/debt | none | components | **policy outputs** |
| Improvement | seed + self-evolve | (not addressed) | **evidence-backed promotion loop** |

**Why the final is better:** the component version would produce four systems that still don't evolve — static behavior. The policy-driven version makes the *policies themselves* the artifact that evolves, so the whole system (decisions, debt, drift, docs, readiness) stays consistent with one versioned source of truth. That's the difference between "automated" and "self-adapting."

## 11. Engineering rationale (every decision)

| Decision | Rationale |
|---|---|
| 6 layers, not 9 | merges that reduce ceremony without losing function |
| Policies versioned | one source of truth; decisions auditable; evolution safe |
| Knowledge promotion gated | prevents AI-whim policy churn; keeps policies stable |
| decide.py = evaluator | centralizes judgment; parity-tested; deletable |
| Debt/drift = policy outputs | one mechanism (lifecycle) reused; not isolated subsystems |
| Docs-sync + ADR auto-flagged | prevents the plan-check lesson (doc drift) generally |
| Release readiness | aggregates; "looks done" ≠ "is done" |
| Human-only-when-needed | the philosophy's guardrail, mechanically enforced |

## 12. Self-challenge (final)

- **"Is policy versioning ceremony?"** — It's a field + CI check. Without it, a promoted policy change is untraceable — the exact drift we fight. Kept, minimal.
- **"Is the promotion gate bureaucracy?"** — It's the brief's own requirement (knowledge never blindly overwrites policy). It auto-approves evidence-backed changes; human only for safety. Kept.
- **"Is decide.py redundant with task-triage?"** — task-triage classifies; decide.py *decides* (consumes the classification + more). Parity test (M2) proves it matches; if it duplicates, delete. Kept with the test.
- **"Could this be simpler?"** — The v1.5.x foundation (evidence, lessons, privacy, portability) is untouched per the brief. The ONLY new mechanisms are: policy versioning, decide.py, and the promotion gate — three small, testable, deletable additions that transform "automated" into "autonomous + self-adapting."

*End of final architecture review. No code modified. Ready for approval before implementation.*
