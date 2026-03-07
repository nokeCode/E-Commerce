<#
start-dev.ps1
Usage:
  - Double-click or run from PowerShell: .\start-dev.ps1
  - Provide optional parameters: -Host 127.0.0.1 -Port 8000

This script activates the virtualenv located at <workspace>/myenv, cd into HStore and starts Django devserver.
#>
Param(
    [string]$VenvActivate = "$PSScriptRoot\myenv\Scripts\Activate.ps1",
    [string]$ProjectDir = "$PSScriptRoot\HStore",
    [string]$Host = '127.0.0.1',
    [int]$Port = 8000
)

Write-Host "[start-dev] Script started (PSScriptRoot=$PSScriptRoot)" -ForegroundColor Cyan

if (-not (Test-Path $VenvActivate)) {
    Write-Error "Virtualenv activate script not found: $VenvActivate"
    Write-Host "Vérifiez que votre venv est à 'myenv' et que 'Activate.ps1' existe." -ForegroundColor Yellow
    exit 1
}

# Activate venv in this session
. $VenvActivate

# Change to project directory
if (-not (Test-Path $ProjectDir)) {
    Write-Error "Project directory not found: $ProjectDir"
    exit 1
}

Set-Location $ProjectDir
Write-Host "[start-dev] Activated venv and changed directory to: $(Get-Location)" -ForegroundColor Green

# Start Django dev server
Write-Host "[start-dev] Starting Django development server on $Host:$Port..." -ForegroundColor Cyan
python manage.py runserver "$Host`:$Port"
