# one-man install — Windows PowerShell bootstrap.
# Idempotent + convergent: safe to re-run, never destroys personal config.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/install.ps1 [-DryRun]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$ClaudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$Timestamp = [DateTimeOffset]::Now.ToUnixTimeSeconds()

function Say  { Write-Host "[one-man] $args" }
function Warn { Write-Host "[one-man] WARN: $args" -ForegroundColor Yellow }
function Die  { Write-Host "[one-man] ERROR: $args" -ForegroundColor Red; exit 1 }

function Run {
    if ($DryRun) {
        Write-Host "  (dry-run) would: $args"
    } else {
        & $args
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) { Die "command failed: $args" }
    }
}

# ---------- Step 0: prereq ----------
Say "Prereq check"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Die "node >= 22 required (missing)" }
if (-not (Get-Command git -ErrorAction SilentlyContinue))  { Die "git required (missing)" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Die "python required (missing)" }
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Warn "claude CLI not found - hooks install, but you need Claude Code to use them" }

# ---------- Step 1: backup ----------
if (Test-Path (Join-Path $ClaudeHome "settings.json")) {
    Say "Backup settings.json"
    Run Copy-Item (Join-Path $ClaudeHome "settings.json") (Join-Path $ClaudeHome "settings.json.bak.$Timestamp")
}
if (Test-Path (Join-Path $ClaudeHome "CLAUDE.md")) {
    Say "Backup CLAUDE.md"
    Run Copy-Item (Join-Path $ClaudeHome "CLAUDE.md") (Join-Path $ClaudeHome "CLAUDE.md.bak.$Timestamp")
}

# ---------- Step 2: ensure dirs ----------
New-Item -ItemType Directory -Force -Path @(
    (Join-Path $ClaudeHome "hooks"), (Join-Path $ClaudeHome "skills"),
    (Join-Path $ClaudeHome "self"), (Join-Path $ClaudeHome "plugins")
) | Out-Null

# ---------- Step 3: hooks ----------
Say "Install hooks (14)"
Run Copy-Item (Join-Path $Repo "hooks\*.sh") (Join-Path $ClaudeHome "hooks\") -Force
Run Copy-Item (Join-Path $Repo "hooks\*.py") (Join-Path $ClaudeHome "hooks\") -Force
Run Copy-Item (Join-Path $Repo "hooks\*.mjs") (Join-Path $ClaudeHome "hooks\") -Force
Run Copy-Item (Join-Path $Repo "hooks\test_*.py") (Join-Path $ClaudeHome "hooks\") -Force

# ---------- Step 4: skills (8 discipline) ----------
Say "Install discipline skills (8)"
$Skills = @("audit", "checkpoint", "ctx-agent-history-search", "dep-audit", "memory-maintain", "pro-workflow", "recall", "self-evolve")
foreach ($s in $Skills) {
    $dest = Join-Path $ClaudeHome "skills\$s"
    Run Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
    Run Copy-Item (Join-Path $Repo "skills\$s") $dest -Recurse -Force
}

# ---------- Step 5: self templates (never overwrite existing) ----------
Say "Install self/ templates (preserve existing)"
# PRINCIPLES is the generic discipline baseline — safe to refresh.
Run Copy-Item (Join-Path $Repo "self\PRINCIPLES.md.template") (Join-Path $ClaudeHome "self\PRINCIPLES.md") -Force
# PREFERENCES is user-curated — only write if missing.
if (-not (Test-Path (Join-Path $ClaudeHome "self\PREFERENCES.md"))) {
    Run Copy-Item (Join-Path $Repo "self\PREFERENCES.md.template") (Join-Path $ClaudeHome "self\PREFERENCES.md")
}

# ---------- Step 6: global CLAUDE.md ----------
Say "Install global CLAUDE.md (backup made)"
Run Copy-Item (Join-Path $Repo "templates\CLAUDE.md.global") (Join-Path $ClaudeHome "CLAUDE.md") -Force

# ---------- Step 7: merge settings ----------
Say "Merge settings - preserve env/model, add hooks + permissions"
if (Test-Path (Join-Path $ClaudeHome "settings.json")) {
    python (Join-Path $Repo "scripts\merge_settings.py") (Join-Path $ClaudeHome "settings.json") $ClaudeHome
} else {
    python (Join-Path $Repo "scripts\merge_settings.py") $ClaudeHome $ClaudeHome --init
}

# ---------- Step 8: validate ----------
Say "Validate hook wiring"
python (Join-Path $ClaudeHome "hooks\settings-validate.py") 2>$null
python (Join-Path $ClaudeHome "hooks\hook-health.py") 2>$null
Say "Hook self-checks:"
Push-Location (Join-Path $ClaudeHome "hooks")
python test_danger_guard.py
python test_dep_guard.py
python test_ship_gate.py
Pop-Location

# ---------- Step 9: done ----------
Say "Install complete. Restart Claude Code to bind settings permissions."
Say "Update anytime: git pull && .\scripts\install.ps1"
