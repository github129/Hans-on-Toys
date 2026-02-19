#Requires -Version 5.1
<#
.SYNOPSIS
    Build Hans-on-Toys as a standalone shot.exe (no Python required).

.EXAMPLE
    .\scripts\build.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $PSScriptRoot

# Install PyInstaller if needed
Write-Host "Checking PyInstaller..." -ForegroundColor Cyan
py -m pip install pyinstaller --quiet
Write-Host "  OK" -ForegroundColor Gray

# Build
Write-Host "Building..." -ForegroundColor Cyan
Push-Location $projectDir
try {
    py -m PyInstaller shot.spec --noconfirm
} finally {
    Pop-Location
}

# Result
$exePath = Join-Path $projectDir "dist\shot.exe"
if (Test-Path $exePath) {
    $sizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Build succeeded!" -ForegroundColor Green
    Write-Host "  Output: $exePath  ($sizeMB MB)" -ForegroundColor White
    Write-Host ""
    Write-Host "Next step:" -ForegroundColor Yellow
    Write-Host "  Create shortcut: .\scripts\setup_shortcut.ps1"
} else {
    Write-Error "Build failed. Check the output above."
}
