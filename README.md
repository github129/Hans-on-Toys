# Hans-on-Toys

ハンズオン資料作成用スクリーンショットツール。
画面の指定範囲をスクリーンショットして、クリップボードにコピーします。

## セットアップ（ゼロから始める場合）

### 1. Python のインストール

[python.org](https://www.python.org/downloads/) から **Python 3.9 以上**をダウンロードしてインストールしてください。

> インストール時に **「Add Python to PATH」** にチェックを入れてください。

インストール確認:

```powershell
py --version
# 例: Python 3.12.x
```

### 2. パッケージのインストール

```powershell
py -m pip install -r requirements.txt
```

これにより以下がインストールされます:

| パッケージ | 用途 |
|---|---|
| Pillow | 画像処理 |
| mss | 高速スクリーンショット |
| keyboard | グローバルホットキー |
| pystray | タスクトレイアイコン |
| pytesseract | OCR（個人情報マスク機能用） |

> **Windows** はクリップボードコピーに追加パッケージ不要（PowerShell を使用）。
> **Linux** は `xclip` または `wl-clipboard` が必要:
> `sudo apt-get install xclip` / `sudo apt-get install wl-clipboard`

### 3. Tesseract OCR のインストール（個人情報マスク機能を使う場合のみ）

[Tesseract インストーラー（Windows）](https://github.com/UB-Mannheim/tesseract/wiki) からダウンロードしてインストールしてください。

> **日本語データは不要**です。英語のみのインストールで動作します。
> インストール後、`tesseract --version` でパスが通っていることを確認してください。
> パスが通っていない場合はタスクトレイ右クリック → **設定...** から実行ファイルのパスを指定できます。

---

## 単体 exe にパッケージ化（配布用・Python 不要になる）

> **前提**: 上記セットアップ（Python + `pip install -r requirements.txt`）が完了していること。
> PyInstaller は `build.ps1` が自動でインストールします。

```powershell
# 1. exe をビルド（初回のみ・数分かかります）
.\scripts\build.ps1

# 2. デスクトップショートカットを作成
.\scripts\setup_shortcut.ps1

# Windows ログイン時に自動起動させる場合
.\scripts\setup_shortcut.ps1 -AddToStartup
```

`dist\shot.exe` が生成され、**Python がインストールされていない PC でも動作**します。
デスクトップに **「Hans-on-Toys」** アイコンが作成され、ダブルクリックするだけで起動します。

> **Python 環境のままショートカットだけ作る場合**（ビルドしない場合）:
> `.\scripts\setup_shortcut.ps1` だけ実行してください。`dist\shot.exe` がなければ自動的に Python 経由で起動します。

---

## 使い方

### ホットキー常駐モード（推奨）

```powershell
shot watch
```

タスクトレイにアイコンが表示され、以下のホットキーがいつでも使えます:

| ホットキー | 動作 |
|---|---|
| `Ctrl+Alt+S` | 画面上でドラッグして範囲を選択してキャプチャ |
| `Ctrl+Alt+F` | 全画面をキャプチャ |
| `Ctrl+Alt+R` | 前回と同じ範囲を再キャプチャ |
| `Ctrl+Alt+P` | 範囲を選択してキャプチャ（個人情報を自動マスク） |

タスクトレイのアイコンを右クリック → **終了** で停止。

---

### 単発コマンドモード

#### インタラクティブ（ドラッグで範囲を選択）

```powershell
shot
```

1. 画面が暗くなり選択モードに入る
2. マウスをドラッグして範囲を選ぶ（右下にサイズをリアルタイム表示）
3. マウスを離すとクリップボードにコピー完了
4. `ESC` でキャンセル

#### 座標指定

```powershell
shot --region X1 Y1 X2 Y2
# 例: 左上 (100, 200) から右下 (900, 700)
shot --region 100 200 900 700
```

#### ファイルへの保存（クリップボードコピーと同時）

```powershell
shot --output capture.png
shot --region 0 0 1920 1080 --output fullscreen.png
```

#### ヘルプ

```powershell
shot --help
```

---

## 個人情報マスク機能（プライバシーキャプチャ）

`Ctrl+Alt+P` を押すと、キャプチャ後に画像内の個人情報を自動検出して黒塗りしてからクリップボードにコピーします。

> この機能を使うには、セットアップの **手順 2・3**（`requirements.txt` のインストールと Tesseract OCR）が必要です。

### 検出できる個人情報

| 種類 | 例 | デフォルト |
|---|---|:---:|
| メールアドレス | `user@example.com` | 有効 |
| 電話番号（日本） | `090-xxxx-xxxx` | 有効 |
| 電話番号（国際） | `+1-xxx-xxx-xxxx` | 無効 |
| 郵便番号 | `〒123-4567` | 無効 |
| クレジットカード番号 | `xxxx-xxxx-xxxx-xxxx` | 有効 |
| カスタム正規表現 | 任意のパターン | — |

### 設定の変更

タスクトレイのアイコンを右クリック → **設定...** で設定ダイアログを開けます。

- マスクする個人情報の種類をオン/オフ
- マスクの色を変更（デフォルト: 黒）
- カスタム正規表現パターンを追加・削除
- Tesseract の実行ファイルパスを指定（PATH に通っている場合は不要）

設定は `~/.hans_on_toys/config.json` に保存されます。

> **pytesseract がインストールされていない場合**、`Ctrl+Alt+P` を使うとトレイ通知でエラーが表示されます。通常のキャプチャ（`Ctrl+Alt+S` / `F` / `R`）は影響を受けず正常に動作します。

---

## 動作環境

| OS | クリップボードの仕組み |
|---|---|
| Windows 10/11 | PowerShell (System.Windows.Forms) |
| macOS | osascript |
| Linux (X11) | xclip / xsel |
| Linux (Wayland) | wl-copy |
