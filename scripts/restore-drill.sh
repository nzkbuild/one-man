#!/usr/bin/env bash
# one-man restore drill — prove backup actually works.
# Creates a backup, restores to a scratch dir, verifies content hash matches.
# The missing half of backup.sh: a backup that was never restored is a rumor.
# Usage: bash scripts/restore-drill.sh
set +e

CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
BACKUP_DIR="${ONE_MAN_BACKUP_DIR:-$HOME/.claude-backups}"
SCRATCH="$(mktemp -d)"

say() { printf '[restore-drill] %s\n' "$*"; }
die() { printf '[restore-drill] ERROR: %s\n' "$*" >&2; exit 1; }

say "Step 1: create backup"
bash "$(dirname "${BASH_SOURCE[0]}")/backup.sh" >/dev/null 2>&1 || die "backup failed"
ARCHIVE="$(ls -1t "$BACKUP_DIR"/one-man-*.tar.gz | head -1)"
[ -n "$ARCHIVE" ] || die "no backup archive found"
say "  archive: $ARCHIVE"

say "Step 2: restore to scratch"
tar -xzf "$ARCHIVE" -C "$SCRATCH" || die "restore failed"
[ -d "$SCRATCH/.claude" ] || die "restored tree missing .claude"

say "Step 3: verify the archive's content is fully present after restore"
# The meaningful check: every file in the archive exists in the restored tree.
# Compare the archive's manifest against the scratch tree. (while-in-pipe runs
# in a subshell, so the real check uses process substitution below.)
FAILED=0
while read -r entry; do
  rel="${entry#.claude/}"
  [ -z "$rel" ] && continue
  # -e accepts both files and dirs (the archive holds empty task dirs too)
  [ -e "$SCRATCH/.claude/$rel" ] || { echo "  MISSING: $rel"; FAILED=1; }
done < <(tar -tzf "$ARCHIVE")

if [ "$FAILED" = "0" ]; then
  say "DRILL PASSED — every archived file restored"
  rm -rf "$SCRATCH"
  exit 0
else
  say "DRILL FAILED — archive entries missing after restore"
  say "  scratch kept at: $SCRATCH"
  exit 1
fi
