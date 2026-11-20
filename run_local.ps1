<#
.SYNOPSIS
    One-Click Local Environment Setup, Verification, and Service Launcher
    for the Multi-Domain AI Incident Triage Bootcamp (aiml_rpd).

.USAGE
    .un_local.ps1                  # Verify setup, run pytest, and launch Phoenix + FastAPI/Gradio
    .un_local.ps1 -InstallDeps     # Also install/upgrade all packages from requirements.txt
    .un_local.ps1 -SkipTests       # Skip pytest regression suite for faster startup
    .un_local.ps1 -Domain cicd_devops  # Launch with a specific active domain
#>

param(
    [switch]$InstallDeps,
    [switch]$SkipTests,
    [string]$Domain = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Hybrid AI/ML Bootcamp & Multi-Domain Triage Launcher" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Ensure .env exists from .env.example
if (-not (Test-Path "$RepoRoot\.env")) {
    if (Test-Path "$RepoRoot\.env.example") {
        Copy-Item "$RepoRoot\.env.example" "$RepoRoot\.env"
        Write-Host "[1/6] Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Warning "[1/6] .env.example not found; relying on configs/app_config.yaml defaults."
    }
} else {
    Write-Host "[1/6] Found existing .env configuration." -ForegroundColor Green
}

if ($Domain -ne "") {
    $env:BOOTCAMP_DOMAIN = $Domain
    Write-Host "      Override BOOTCAMP_DOMAIN = $Domain" -ForegroundColor Yellow
}

# 2. Create or Activate .venv
if (-not (Test-Path "$RepoRoot\.venv\Scripts\Activate.ps1")) {
    Write-Host "[2/6] Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv "$RepoRoot\.venv"
}
. "$RepoRoot\.venv\Scripts\Activate.ps1"
Write-Host "[2/6] Activated .venv ($(python --version))" -ForegroundColor Green

# 3. Install/Upgrade Dependencies if requested
if ($InstallDeps) {
    Write-Host "[3/6] Installing/updating dependencies from requirements.txt..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install -r "$RepoRootequirements.txt"
} else {
    Write-Host "[3/6] Checking core imports (use -InstallDeps to install/upgrade packages)..." -ForegroundColor Green
}

# 4. Verify Core Modules, Externalized Settings & Local Model Weights
python -c @"
import os, sys
from engine.settings import SETTINGS
from engine.use_case_loader import UseCaseLoader
from engine.qdrant_store import QdrantVectorStore
from engine.router import ModelRouter
from engine.debugger import TraceDebugger
import fastapi, gradio, phoenix

model_ok = os.path.isdir(SETTINGS.local_model_path)
print(f'[4/6] Settings Verified -> Domain={SETTINGS.active_domain} | Phoenix={SETTINGS.phoenix_ui_url} | API={SETTINGS.api_base_url}')
print(f'      Local Qwen Model Dir Present: {model_ok} ({SETTINGS.local_model_path})')
if not model_ok:
    print('      WARNING: Local model directory not found at configured path; check LOCAL_MODEL_PATH in .env!')
"@

# 5. Run Full-Repository Pytest Regression Suite (6 Domains = 60 Incidents)
if (-not $SkipTests) {
    if (Test-Path "$RepoRoot	ests	est_all_domains.py") {
        Write-Host "[5/6] Running pytest regression suite across all 6 domains..." -ForegroundColor Yellow
        pytest -q
        Write-Host "[5/6] All regression tests passed!" -ForegroundColor Green
    } else {
        Write-Host "[5/6] No tests/test_all_domains.py found; skipping pytest." -ForegroundColor DarkGray
    }
} else {
    Write-Host "[5/6] Skipped pytest (-SkipTests)." -ForegroundColor DarkGray
}

# 6. Launch Arize Phoenix (6008) in a dedicated window & FastAPI/Gradio (8000) in current window
$PhoenixPortInUse = Get-NetTCPConnection -LocalPort 6008 -ErrorAction SilentlyContinue
if (-not $PhoenixPortInUse) {
    Write-Host "[6/6] Launching standalone Arize Phoenix server on http://127.0.0.1:6008..." -ForegroundColor Cyan
    $PhoenixCmd = "Set-Location '$RepoRoot'; . '.\.venv\Scripts\Activate.ps1'; `$env:PHOENIX_PORT='6008'; `$env:PHOENIX_GRPC_PORT='14317'; phoenix serve"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $PhoenixCmd
    Start-Sleep -Seconds 3
} else {
    Write-Host "[6/6] Arize Phoenix already listening on port 6008." -ForegroundColor Green
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host " READY! Open these URLs in your browser:" -ForegroundColor Green
Write-Host "   -> Interactive Gradio Console : http://127.0.0.1:8000/ui" -ForegroundColor White
Write-Host "   -> FastAPI Swagger Docs       : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "   -> A2A v1.0 Agent Card        : http://127.0.0.1:8000/.well-known/agent-card.json" -ForegroundColor White
Write-Host "   -> Arize Phoenix Traces       : http://127.0.0.1:6008" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

uvicorn app.main:app --host 127.0.0.1 --port 8000
