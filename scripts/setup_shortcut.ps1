#Requires -Version 5.1
<#
.SYNOPSIS
    Set up a desktop shortcut for Hans-on-Toys.

.DESCRIPTION
    Creates a desktop shortcut that launches "shot watch" without a console window.
    Use -AddToStartup to also register it to run at Windows login.

.EXAMPLE
    .\scripts\setup_shortcut.ps1

.EXAMPLE
    .\scripts\setup_shortcut.ps1 -AddToStartup
#>
param(
    [switch]$AddToStartup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# This script lives in <project>/scripts/
$projectDir = Split-Path -Parent $PSScriptRoot
Write-Host "Project: $projectDir" -ForegroundColor Gray

# Decide how to launch: built exe > pythonw > python
$builtExe = Join-Path $projectDir "dist\shot.exe"

if (Test-Path $builtExe) {
    $launchTarget = $builtExe
    $launchArgs   = "watch"
    Write-Host "Launch method: built exe ($builtExe)" -ForegroundColor Green
} else {
    Write-Host "Locating Python..." -ForegroundColor Cyan
    try {
        $pyExe = (py -c "import sys; print(sys.executable)").Trim()
    } catch {
        Write-Error "dist\shot.exe not found and Python (py) is not available.`nRun .\scripts\build.ps1 first, or install Python."
        exit 1
    }
    $pythonw = $pyExe -replace "python\.exe$", "pythonw.exe"
    if (-not (Test-Path $pythonw)) {
        Write-Warning "pythonw.exe not found; using python.exe (a console window may flash briefly)."
        $pythonw = $pyExe
    }
    $launchTarget = $pythonw
    $launchArgs   = "-m hans_on_toys watch"
    Write-Host "Launch method: Python ($pythonw)" -ForegroundColor Yellow
    Write-Host "  Tip: run .\scripts\build.ps1 to create a standalone exe." -ForegroundColor Gray
}

# Generate icon (skip when using the built exe)
Write-Host "Generating icon..." -ForegroundColor Cyan

$iconDir  = Join-Path $env:APPDATA "hans-on-toys"
$iconPath = Join-Path $iconDir "icon.ico"
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null

if (Test-Path $builtExe) {
    $iconPath = $null   # icon is embedded in the exe
} else {
    $iconScript = @"
import sys
sys.path.insert(0, r'$projectDir')
from hans_on_toys.watcher import _make_icon
img = _make_icon().resize((256, 256))
img.save(r'$iconPath')
"@
    try {
        & $launchTarget -c $iconScript
        Write-Host "  Icon saved: $iconPath" -ForegroundColor Gray
    } catch {
        Write-Warning "Icon generation failed; using default icon."
        $iconPath = $null
    }
}

# Create VBScript launcher
# Using wscript.exe as the shortcut target prevents editors (e.g. VS Code)
# from hijacking the .exe file association.
Write-Host "Creating launcher script..." -ForegroundColor Cyan

$vbsPath = Join-Path $iconDir "launch.vbs"
$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """$launchTarget"" $launchArgs", 0, False
"@
Set-Content -Path $vbsPath -Value $vbsContent -Encoding UTF8
Write-Host "  Launcher: $vbsPath" -ForegroundColor Gray

# Create desktop shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Cyan

$desktop  = [Environment]::GetFolderPath("Desktop")
$lnkPath  = Join-Path $desktop "Hans-on-Toys.lnk"

$wsh      = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($lnkPath)
$shortcut.TargetPath       = "$env:SystemRoot\System32\wscript.exe"
$shortcut.Arguments        = """$vbsPath"""
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description      = "Hans-on-Toys screenshot tool (hotkey daemon)"
if ($iconPath -and (Test-Path $iconPath)) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Host "  Created: $lnkPath" -ForegroundColor Green

# Register to startup (optional)
if ($AddToStartup) {
    Write-Host "Adding to startup..." -ForegroundColor Cyan
    $startupDir = [Environment]::GetFolderPath("Startup")
    $startupLnk = Join-Path $startupDir "Hans-on-Toys.lnk"
    Copy-Item $lnkPath $startupLnk -Force
    Write-Host "  Registered: $startupLnk" -ForegroundColor Green
    Write-Host "  Will auto-start at next Windows login." -ForegroundColor Gray
}

# Done
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Double-click 'Hans-on-Toys' on your desktop to launch." -ForegroundColor White
Write-Host ""
Write-Host "Hotkeys:" -ForegroundColor Yellow
Write-Host "  Ctrl+Alt+S  Region capture"
Write-Host "  Ctrl+Alt+F  Full-screen capture"
Write-Host "  Ctrl+Alt+R  Re-capture last region"
Write-Host ""
Write-Host "To quit: right-click the tray icon -> Exit"
