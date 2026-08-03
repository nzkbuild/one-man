# Skill & Plugin Audit — v1.5.1 (req 4)

**Date:** 2026-08-04
**Method:** grep evidence — every skill/plugin checked for references in hooks/, scripts/, skills.flow.json, and the session transcript. Classification per the 6 categories. No ceremonial invocation forced; unused items classified, not forced.

---

## 8 discipline skills

| Skill | Refs | Classification | Rationale |
|---|---|---|---|
| audit | 6 | **useful, correctly reachable** | referenced by phase-gate + session-context; runs at phase boundaries |
| checkpoint | 5 | **useful, correctly reachable** | precompact-checkpoint + flow routing |
| self-evolve | 4 | **useful, correctly reachable** | session-context + flow routing; now writes the lesson ledger |
| pro-workflow | 2 | **useful, correctly reachable** | flow default routing |
| recall | 2 | **useful, correctly reachable** | session-context memory fallback |
| memory-maintain | 1 | **useful, correctly reachable** | session-context nudges it near budget |
| ctx-agent-history-search | 1 | **useful but under-routed** | routed for "question" type only; acceptable (question tasks are rarer) |
| dep-audit | 1 | **useful but under-routed** | routed for "chore" only; dep-guard hook covers the common case |

## 13 design skills

| Skill | Refs | Classification |
|---|---|---|
| brandkit | 3 | **useful, correctly reachable** (design chain) |
| design-taste-frontend | 2 | **useful, correctly reachable** (design chain) |
| minimalist-ui | 3 | **useful, correctly reachable** (design chain) |
| industrial-brutalist-ui | 1 | **useful, correctly reachable** (design variant) |
| imagegen-frontend-web/mobile | 1 each | **useful, correctly reachable** (design variant) |
| image-to-code | 0 | **not currently needed** (no image→code task this session; kept, deferred) |
| gpt-taste | 0 | **not currently needed** (overlaps design-taste; **duplicated** — defer, don't force) |
| high-end-visual-design | 0 | **not currently needed** (overlaps design chain; deferred) |
| redesign-existing-projects | 0 | **not currently needed** (no redesign task; deferred) |
| stitch-design-taste | 0 | **not currently needed** (niche; deferred) |
| find-skills | 0 | **obsolete** (a skill-discovery tool; the flow manifest replaced manual discovery) |
| full-output-enforcement | 0 | **not currently needed** (output-verbosity rule; CLAUDE.md covers it) |

## 6 plugins

| Plugin | Enabled | Classification |
|---|---|---|
| superpowers | ✅ | **useful, correctly reachable** (process skills routed via flow) |
| ponytail | ✅ | **useful, correctly reachable** (minimalism ladder, session-injected) |
| context-mode | ✅ | **useful, correctly reachable** (context efficiency, active) |
| vercel | ✅ | **useful, correctly reachable** (deploy tooling, on-demand) |
| typescript-lsp | ✅ | **useful, correctly reachable** (LSP for TS projects) |
| rust-analyzer-lsp | ✅ | **useful, correctly reachable** (LSP for Rust projects) |

---

## Actions taken

- **None removed or disabled** — every item is either useful+reachable or deferred with a reason. No ceremonial invocation was added.
- **Deferred (not needed now):** gpt-taste, high-end-visual-design, redesign-existing-projects, stitch-design-taste, image-to-code, full-output-enforcement.
- **Obsolete:** find-skills (the flow manifest replaced its purpose) — candidate for removal in v1.6.0, kept this patch (no churn).

## Conclusion

No unused-duplication forced into use. The gap F3 (dep-audit, ctx-agent-history-search under-routed) is acknowledged and **not** fixed with ceremony — their hooks (dep-guard) and question-routing cover the practical case. This matches the brief: classify, don't force.
