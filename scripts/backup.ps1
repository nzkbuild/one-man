# one-man backup — Windows PowerShell. Same contract as backup.sh.
# Usage:
#   powershell -File scripts/backup.ps1              # create backup
#   powershell -File scripts/backup.ps1 -Restore F   # restore from archive
#   powershell -File scripts/backup.ps1 -List        # list backups
param(
    [switch]$List,
    [string]$Restore
)

$ClaudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$BackupDir = Join-Path $env:USERPROFILE ".claude-backups"
$Ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function Say { Write-Host "[backup] $args" }
function Die { Write-Host "[backup] ERROR: $args" -ForegroundColor Red; exit 1 }

if ($List) {
    Get-ChildItem (Join-Path $BackupDir "one-man-*.tar.gz") -ErrorAction SilentlyContinue | ForEach-Object {
        $_.Name -replace "one-man-", "" -replace "\.tar\.gz$", ""
    }
    exit 0
}

if ($Restore) {
    if (-not (Test-Path $Restore)) { Die "archive not found: $Restore" }
    Say "Restoring from $Restore"
    # Pre-backup current state (safety)
    if (Test-Path $ClaudeHome) {
        tar -czf (Join-Path $BackupDir "one-man-pre-restore-$Ts.tar.gz") -C (Split-Path $ClaudeHome -Parent) (Split-Path $ClaudeHome -Leaf)
    }
    tar -xzf $Restore -C (Split-Path $ClaudeHome -Parent)
    if ($LASTEXITCODE -ne 0) { Die "restore failed" }
    Say "Restore complete. Restart Claude Code."
    exit 0
}

if (-not (Test-Path $ClaudeHome)) { Die "no ~/.claude to back up" }
Say "Backing up $ClaudeHome -> $BackupDir\one-man-$Ts.tar.gz"
tar -czf (Join-Path $BackupDir "one-man-$Ts.tar.gz") `
    -C (Split-Path $ClaudeHome -Parent) `
    --exclude=".claude/hooks/__pycache__" `
    --exclude=".claude/plugins/cache" `
    (Split-Path $ClaudeHome -Leaf)
if ($LASTEXITCODE -ne 0) { Die "backup failed" }
Say "Backup created: $BackupDir\one-man-$Ts.tar.gz"
