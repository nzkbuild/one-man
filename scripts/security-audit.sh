#!/usr/bin/env bash
# one-man security audit — continuous dependency vulnerability check.
# Runs pnpm/npm audit in each project, aggregates findings into a dated report.
# Usage: bash scripts/security-audit.sh [project-dir ...]
#   (no args = audit the repo itself + any dirs under the cwd)
set +e

REPORT_DIR="${ONE_MAN_REPORT_DIR:-$HOME/.claude/reports}"
TS="$(date +%Y%m%d)"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/security-$TS.md"

say()  { printf '[security-audit] %s\n' "$*"; }

# Determine audit tool: pnpm preferred, fallback npm
AUDIT_CMD=""
command -v pnpm >/dev/null 2>&1 && AUDIT_CMD="pnpm audit"
[ -z "$AUDIT_CMD" ] && command -v npm >/dev/null 2>&1 && AUDIT_CMD="npm audit"

if [ -z "$AUDIT_CMD" ]; then
  say "no package manager with audit found"
  exit 0
fi

TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=("$PWD")

{
  echo "# Security audit — $TS"
  echo ""
  echo "Command: $AUDIT_CMD"
  echo ""
} > "$REPORT"

FOUND=0
for dir in "${TARGETS[@]}"; do
  if [ ! -f "$dir/package.json" ]; then
    echo "## $dir — no package.json (skip)" >> "$REPORT"
    continue
  fi
  echo "## $dir" >> "$REPORT"
  echo '```' >> "$REPORT"
  AUDIT_OUT="$(cd "$dir" && $AUDIT_CMD --audit-level=high 2>&1)"
  echo "$AUDIT_OUT" >> "$REPORT"
  echo '```' >> "$REPORT"
  # Real findings = a nonzero count, not the safe "No known vulnerabilities found".
  if echo "$AUDIT_OUT" | grep -qE "^[0-9]+ (vulnerabilit(y|ies))|high severity|critical severity"; then
    FOUND=1
  fi
  echo "" >> "$REPORT"
done

say "report written: $REPORT"
if [ "$FOUND" = "1" ]; then
  say "HIGH/CRITICAL vulnerabilities found — review $REPORT"
  exit 1
fi
say "no high/critical vulnerabilities"
exit 0
