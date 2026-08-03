# Versioning Discipline

How one-man versions, tags, and rolls back. Read before releasing.

## Semver

`vMAJOR.MINOR.PATCH`

| Bump | When | Example |
|---|---|---|
| **PATCH** | bugfix, no behavior change | `v1.1.0` → `v1.1.1` |
| **MINOR** | new feature, backward compatible | `v1.0.0` → `v1.1.0` |
| **MAJOR** | breaking change (hook contract, config schema) | `v1.2.0` → `v2.0.0` |

Rules:
- Never commit a version bump without a CHANGELOG entry for it.
- Never re-tag a released version. A moved tag is a rollback-consistency violation
  (the v1.0.0 move was a one-time correction — now prevented by plan-check + this doc).
- `plan-check.py --release` must pass before tagging (blocks release over open items).

## Tag policy

- Every release = annotated tag (`git tag -a vX.Y.Z -m "..."`).
- Tag lands on the commit whose CI is green.
- Tags are immutable after push. To fix a broken release: bump PATCH, release again.

## Rollback drill

Two layers, both tested:

**Layer 1 — code:** `git checkout v1.0.0` + re-run install = exact previous code state.
```
git checkout v1.1.0        # or any tag
bash scripts/install.sh     # re-apply hooks/skills/templates
```

**Layer 2 — personal data:** `backup.sh --restore` = exact previous config + memory.
```
bash scripts/backup.sh --list                  # find the archive
bash scripts/backup.sh --restore ~/.claude-backups/one-man-<ts>.tar.gz
```

A full rollback = Layer 1 + Layer 2 together. Run the drill once per release and
note it in the CHANGELOG entry.

## Release checklist (run every release)

1. `pnpm run check` green
2. `python3 scripts/plan-check.py --release` passes
3. CHANGELOG entry written
4. `git tag -a vX.Y.Z` on green commit
5. Push tag + branch
6. CI green on the tag
7. Rollback drill tested
