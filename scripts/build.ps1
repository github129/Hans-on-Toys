#Requires -Version 5.1
<#
.SYNOPSIS
    Hans-on-Toys を単体の shot.exe にビルドします。

.DESCRIPTION
    PyInstaller を使って dist\shot.exe を生成します。
    生成した .exe は Python がインストールされていない PC でも動作します。

.EXAMPLE
    .\scripts\build.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $PSScriptRoot

# ─── PyInstaller をインストール ───────────────────────────────────────────────
Write-Host "PyInstaller を確認中..." -ForegroundColor Cyan
py -m pip install pyinstaller --quiet
Write-Host "  OK" -ForegroundColor Gray

# ─── ビルド ──────────────────────────────────────────────────────────────────
Write-Host "ビルド中..." -ForegroundColor Cyan
Push-Location $projectDir
try {
    py -m PyInstaller shot.spec --noconfirm
} finally {
    Pop-Location
}

# ─── 結果確認 ─────────────────────────────────────────────────────────────────
$exePath = Join-Path $projectDir "dist\shot.exe"
if (Test-Path $exePath) {
    $sizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "ビルド完了！" -ForegroundColor Green
    Write-Host "  出力: $exePath  ($sizeMB MB)" -ForegroundColor White
    Write-Host ""
    Write-Host "次のステップ:" -ForegroundColor Yellow
    Write-Host "  ショートカットを作成: .\scripts\setup_shortcut.ps1"
    Write-Host "  （dist\shot.exe が自動で使われます）"
} else {
    Write-Error "ビルドに失敗しました。上記のエラーを確認してください。"
}
