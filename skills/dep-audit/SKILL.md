---
name: dep-audit
description: Audits project dependencies for staleness, security vulnerabilities, duplicate packages, and unused deps.
---

# Dependency Auditor

Runs a multi-prong audit of the project's dependency health:

- `pnpm audit` — security vulnerabilities
- `npx depcheck` — unused dependencies, missing dependencies
- `pnpm outdated` — stale packages needing updates
- Manual checks: last commit date for critical deps, duplicate packages

## Usage

```
/dep-audit
```

Invoke this skill when:
- Before adding a new dependency (is there already something that covers this?)
- At milestone boundaries (pre-release audit)
- When the user asks "is our dependency tree healthy?"
- When PostToolUse dep-guard flags a new install

## Script

Run these commands and report findings:

1. Security audit:
```bash
pnpm audit --json 2>/dev/null || npm audit --json 2>/dev/null
```

2. Unused/missing dependencies:
```bash
npx depcheck --ignores="@types/*,eslint*,prettier,husky,lint-staged,typescript" 2>/dev/null
```

3. Staleness:
```bash
pnpm outdated --format json 2>/dev/null || npm outdated --json 2>/dev/null
```

4. Critical dep health (manually review these):
```bash
for pkg in better-auth prisma @prisma/client; do
  npm view "$pkg" time --json 2>/dev/null | python -c "
import json, sys
data = json.load(sys.stdin)
versions = sorted(data.items(), key=lambda x: x[1])
latest = versions[-1]
print(f'{sys.argv[1]}: latest={latest[0]} ({latest[1]})')
" "$pkg"
done
```

Report findings by severity: critical (vulnerabilities), high (unused deps, stale majors), low (stale patches).
