#Requires -Version 5.1
<#
.SYNOPSIS
    Hans-on-Toys のデスクトップショートカットをセットアップします。

.DESCRIPTION
    shot watch をコンソール画面なしで起動するデスクトップショートカットを作成します。
    -AddToStartup を付けると Windows ログイン時に自動起動します。

.EXAMPLE
    # デスクトップショートカットだけ作成
    .\setup_shortcut.ps1

.EXAMPLE
    # デスクトップショートカット + Windows 起動時に自動起動
    .\setup_shortcut.ps1 -AddToStartup
#>
param(
    [switch]$AddToStartup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── Python の場所を確認 ──────────────────────────────────────────────────────
Write-Host "Python を検索中..." -ForegroundColor Cyan

try {
    $pyExe = (py -c "import sys; print(sys.executable)").Trim()
} catch {
    Write-Error "Python (py コマンド) が見つかりません。Python をインストールして再実行してください。"
    exit 1
}

# コンソール非表示で実行できる pythonw.exe を優先する
$pythonw = $pyExe -replace "python\.exe$", "pythonw.exe"
if (-not (Test-Path $pythonw)) {
    Write-Warning "pythonw.exe が見つかりません。python.exe を使用します（起動時にコンソール画面が一瞬表示されます）。"
    $pythonw = $pyExe
}
Write-Host "  使用する Python: $pythonw" -ForegroundColor Gray

# ─── プロジェクトディレクトリ ──────────────────────────────────────────────────
# このスクリプトは <project>/scripts/ に置かれている前提
$projectDir = Split-Path -Parent $PSScriptRoot
Write-Host "  プロジェクト: $projectDir" -ForegroundColor Gray

# ─── アイコン生成（hans_on_toys.watcher の _make_icon を流用） ─────────────────
Write-Host "アイコンを生成中..." -ForegroundColor Cyan

$iconDir  = Join-Path $env:APPDATA "hans-on-toys"
$iconPath = Join-Path $iconDir "icon.ico"
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null

$iconScript = "
import sys
sys.path.insert(0, r'$projectDir')
from hans_on_toys.watcher import _make_icon
img = _make_icon().resize((256, 256))
img.save(r'$iconPath')
"

try {
    & $pythonw -c $iconScript
    Write-Host "  アイコン保存先: $iconPath" -ForegroundColor Gray
} catch {
    Write-Warning "アイコン生成に失敗しました。デフォルトアイコンを使用します。"
    $iconPath = $null
}

# ─── デスクトップショートカット作成 ───────────────────────────────────────────
Write-Host "デスクトップショートカットを作成中..." -ForegroundColor Cyan

$desktop  = [Environment]::GetFolderPath("Desktop")
$lnkPath  = Join-Path $desktop "Hans-on-Toys.lnk"

$wsh      = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($lnkPath)
$shortcut.TargetPath       = $pythonw
$shortcut.Arguments        = "-m hans_on_toys watch"
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description      = "Hans-on-Toys スクリーンショットツール（ホットキー常駐）"
if ($iconPath -and (Test-Path $iconPath)) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Host "  作成しました: $lnkPath" -ForegroundColor Green

# ─── スタートアップ登録（オプション） ─────────────────────────────────────────
if ($AddToStartup) {
    Write-Host "スタートアップに登録中..." -ForegroundColor Cyan
    $startupDir = [Environment]::GetFolderPath("Startup")
    $startupLnk = Join-Path $startupDir "Hans-on-Toys.lnk"
    Copy-Item $lnkPath $startupLnk -Force
    Write-Host "  登録しました: $startupLnk" -ForegroundColor Green
    Write-Host "  次回 Windows ログイン時から自動起動します。" -ForegroundColor Gray
}

# ─── 完了メッセージ ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "セットアップ完了！" -ForegroundColor Green
Write-Host "デスクトップの「Hans-on-Toys」をダブルクリックして起動してください。" -ForegroundColor White
Write-Host ""
Write-Host "ホットキー:" -ForegroundColor Yellow
Write-Host "  Ctrl+Alt+S  範囲を選択してキャプチャ"
Write-Host "  Ctrl+Alt+F  全画面キャプチャ"
Write-Host "  Ctrl+Alt+R  前回の範囲を再キャプチャ"
Write-Host ""
Write-Host "終了: タスクトレイのアイコンを右クリック → 終了"
