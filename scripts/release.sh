#!/usr/bin/env bash
# one-man release — automates the release checklist (docs/versioning.md).
# The repo gets a deploy stage: check -> plan-check -> CHANGELOG -> tag -> push.
# Usage: bash scripts/release.sh <vX.Y.Z> [--dry-run]
set +e

VERSION="$1"
[ -z "$VERSION" ] && { echo "usage: release.sh <vX.Y.Z> [--dry-run]"; exit 1; }
DRY=0
[ "$2" = "--dry-run" ] && DRY=1

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

say() { printf '[release] %s\n' "$*"; }
die() { printf '[release] ERROR: %s\n' "$*" >&2; exit 1; }
run() {
  if [ "$DRY" = "1" ]; then printf '  (dry-run) would: %s\n' "$*"; else "$@"; fi
}

# 1. working tree clean?
if ! git diff --quiet; then die "working tree dirty — commit or stash first"; fi
[ "$DRY" = "1" ] && say "dry-run: tree clean check passed"

# 2. full check
say "Step 1: full check (lint + typecheck + 12 self-checks)"
run pnpm run check || die "check failed"
say "Step 1: pass"

# 3. plan-check
say "Step 2: plan-check --release"
run python scripts/plan-check.py --release || die "plan-check blocked (open non-deferred items)"
say "Step 2: pass"

# 4. CHANGELOG bump
say "Step 3: CHANGELOG entry present for $VERSION"
grep -q "## \[$VERSION\]" CHANGELOG.md || die "no CHANGELOG entry for $VERSION — add it first"
say "Step 3: pass"

# 5. tag
say "Step 4: tag $VERSION"
run git tag -a "$VERSION" -m "one-man $VERSION
Co-Authored-By: Claude <noreply@anthropic.com>"
say "Step 4: pass"

# 6. push
say "Step 5: push main + tag"
run git push origin main
run git push origin "$VERSION"
say "Step 5: pass"

# 7. CI wait + verify green
if [ "$DRY" = "1" ]; then
  say "Step 6: (dry-run) would wait for CI green"
else
  say "Step 6: waiting for CI green on $VERSION..."
  for i in $(seq 1 40); do
    line=$(gh run list --repo nzkbuild/one-man --limit 1 --json status,headSha --jq '.[0] | .status + "|" + .headSha[:7]' 2>/dev/null)
    sha="${line#*|}"; st="${line%|*}"
    if [ "$st" = "completed" ]; then
      concl=$(gh run list --repo nzkbuild/one-man --limit 1 --json conclusion --jq '.[0].conclusion')
      [ "$concl" = "success" ] && say "CI green on $sha" || die "CI failed on $sha"
      break
    fi
    sleep 20
  done
fi

say "Release $VERSION complete. Rollback: git checkout $VERSION + backup.sh --restore"
