# ADR-001: one-man is a modular monorepo

- **Status:** accepted
- **Date:** 2026-08-04
- **Author:** nzkbuild

## Decision

one-man ships as a **single modular monorepo** — hooks/, skills/, templates/,
scripts/, test/, docs/ in one repo, one version line, one CI. Not split into
multiple packages/repos.

## Context

The alternative was a multi-repo or multi-package split (hooks in one package,
skills in another, templates in a third, each independently versioned).

## Alternatives considered

1. **Multi-repo** (hooks/skills/templates separate repos) — rejected: they ship
   together, install together (`git pull && install`), and version together. A
   version mismatch between a hooks package and a skills package would be a
   silent-configuration bug.
2. **Monorepo with packages/** (npm workspaces per concern) — rejected: no
   runtime dependency between the parts; each is copied/installed, not imported.
   Workspaces add tooling for zero benefit at this scale.
3. **Single flat repo** (no dirs) — rejected: the concern separation (hooks vs
   skills vs scripts vs templates) is load-bearing for maintainability.

## Why monorepo wins

- One `git pull && install` = one consistent state.
- One version tag = one rollback point (`git checkout v1.2.0`).
- One CI run validates the whole system on both OSes.
- The `install.manifest.json` seam allows a future package split WITHOUT breaking
  the monorepo (the manifest is the package boundary).

## Consequences

- Version bumps touch the whole repo (hooks + skills + templates together) —
  acceptable: they're one product.
- Contributors must understand the full layout, not one package. Mitigated by
  AGENTS.md.

## Upgrade path

If the system grows past ~30 hooks or gains a second product line, re-evaluate
a `packages/` split using `install.manifest.json` as the boundary. Not before.
