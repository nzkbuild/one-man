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

# ---------- Step 5.7: lesson ledger seed (only if empty) ----------
$lessonsDir = Join-Path $ClaudeHome "lessons"
if (-not (Test-Path $lessonsDir) -or -not (Get-ChildItem $lessonsDir -ErrorAction SilentlyContinue)) {
    New-Item -ItemType Directory -Force -Path $lessonsDir | Out-Null
    python -c "
import json
seed = json.load(open(r'$Repo\lessons\seed.json'))
for l in seed['lessons']:
    open(r'$lessonsDir' + l['id'] + '.json', 'w').write(json.dumps(l))
"
    Say "  seeded lesson ledger"
} else {
    Say "  ledger exists - not overwriting user lessons"
}

# ---------- Step 5.6: control criticality ----------
Run Copy-Item (Join-Path $Repo "one-man.controls.json") (Join-Path $ClaudeHome "one-man.controls.json") -Force

# ---------- Step 5.5: skills.flow.json ----------
Run Copy-Item (Join-Path $Repo "skills.flow.json") (Join-Path $ClaudeHome "skills.flow.json") -Force

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

# ---------- Step 7.5: plugins + design skills (from manifest, per-machine) ----------
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Say "Install plugins from manifest"
    $manifest = Get-Content (Join-Path $Repo "install.manifest.json") -Raw | ConvertFrom-Json
    foreach ($p in $manifest.plugins) {
        if ($DryRun) { Write-Host "  (dry-run) would: claude plugins install $p" }
        else {
            $ans = Read-Host "  Install plugin $p? [Y/n]"
            if ($ans -notin @("n", "N")) { claude plugins install $p 2>$null; Say "  installed $p" }
            else { Say "  skip $p" }
        }
    }
    Say "Symlink design skills from ~/.agents/skills (when present)"
    foreach ($s in $manifest.designSkills) {
        $src = Join-Path $env:USERPROFILE ".agents\skills\$s"
        $dst = Join-Path $ClaudeHome "skills\$s"
        if (Test-Path $src) {
            if ($DryRun) { Write-Host "  (dry-run) would: ln -s $s" }
            elseif (-not (Test-Path $dst)) { New-Item -ItemType SymbolicLink -Path $dst -Target $src -ErrorAction SilentlyContinue | Out-Null }
        }
    }
} else {
    Warn "claude CLI not found - skipping plugin/design-skill install (run after installing Claude Code)"
}

# ---------- Step 8: validate (real run only; dry-run must not execute python) ----------
if (-not $DryRun) {
    Say "Validate hook wiring"
    try { python (Join-Path $ClaudeHome "hooks\settings-validate.py") 2>$null } catch {}
    try { python (Join-Path $ClaudeHome "hooks\hook-health.py") 2>$null } catch {}
    Say "Hook self-checks:"
    Push-Location (Join-Path $ClaudeHome "hooks")
    python test_danger_guard.py
    if ($LASTEXITCODE) { Pop-Location; Die "danger-guard self-check failed" }
    python test_dep_guard.py
    if ($LASTEXITCODE) { Pop-Location; Die "dep-guard self-check failed" }
    python test_ship_gate.py
    if ($LASTEXITCODE) { Pop-Location; Die "ship-gate self-check failed" }
    Pop-Location
} else {
    Say "Dry-run: skipping validation (would run hook self-checks on real install)"
}

# ---------- Step 9: done ----------
Say "Install complete. Restart Claude Code to bind settings permissions."
Say "Update anytime: git pull && .\scripts\install.ps1"
