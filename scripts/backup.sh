#!/usr/bin/env bash
# one-man backup — protect the irreplaceable: your ~/.claude config + memory.
# Backs up settings.json, CLAUDE.md, hooks/, skills/, self/ (memory!),
# plugins/installed_plugins.json. Restores in one command.
#
# Usage:
#   bash scripts/backup.sh                 # create timestamped backup
#   bash scripts/backup.sh --restore FILE  # restore from an archive
#   bash scripts/backup.sh --list          # list available backups
set +e

CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
BACKUP_DIR="${ONE_MAN_BACKUP_DIR:-$HOME/.claude-backups}"
TS="$(date +%Y%m%d-%H%M%S)"

say()  { printf '[backup] %s\n' "$*"; }
die()  { printf '[backup] ERROR: %s\n' "$*" >&2; exit 1; }

mkdir -p "$BACKUP_DIR"

case "$1" in
  --list)
    ls -1 "$BACKUP_DIR"/one-man-*.tar.gz 2>/dev/null | sed 's/.*one-man-//; s/\.tar\.gz//'
    exit 0
    ;;
  --restore)
    ARCHIVE="$2"
    [ -z "$ARCHIVE" ] && die "usage: backup.sh --restore <archive>"
    [ -f "$ARCHIVE" ] || die "archive not found: $ARCHIVE"
    say "Restoring from $ARCHIVE"
    say "Backing up current state first (safety)..."
    tar -czf "$BACKUP_DIR/one-man-pre-restore-$TS.tar.gz" -C "$(dirname "$CLAUDE_HOME")" "$(basename "$CLAUDE_HOME")" 2>/dev/null || say "note: nothing to pre-backup"
    tar -xzf "$ARCHIVE" -C "$(dirname "$CLAUDE_HOME")" || die "restore failed"
    say "Restore complete. Restart Claude Code."
    exit 0
    ;;
esac

# Default: create backup
[ -d "$CLAUDE_HOME" ] || die "no ~/.claude to back up"
say "Backing up $CLAUDE_HOME -> $BACKUP_DIR/one-man-$TS.tar.gz"
tar -czf "$BACKUP_DIR/one-man-$TS.tar.gz" \
  -C "$(dirname "$CLAUDE_HOME")" \
  --exclude='.claude/hooks/__pycache__' \
  --exclude='.claude/plugins/cache' \
  "$(basename "$CLAUDE_HOME")" 2>/dev/null
[ $? = 0 ] && say "Backup created: $BACKUP_DIR/one-man-$TS.tar.gz" || die "backup failed"
ls -lh "$BACKUP_DIR/one-man-$TS.tar.gz" | awk '{print "  size:", $5}'
