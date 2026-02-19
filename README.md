# Hans-on-Toys

ハンズオン資料作成用スクリーンショットツール。
画面の指定範囲をスクリーンショットして、クリップボードにコピーします。

## インストール

```bash
pip install -e .
```

依存パッケージ（自動インストール）:
- [Pillow](https://pillow.readthedocs.io/) — 画像処理
- [mss](https://python-mss.readthedocs.io/) — 高速スクリーンショット
- [keyboard](https://github.com/boppreh/keyboard) — グローバルホットキー
- [pystray](https://github.com/moses-palmer/pystray) — タスクトレイアイコン

> **Windows** はクリップボードコピーに追加パッケージ不要（PowerShell を使用）。
> **Linux** は `xclip` または `wl-clipboard` が必要:
> `sudo apt-get install xclip` / `sudo apt-get install wl-clipboard`

## 使い方

### ホットキー常駐モード（推奨）

```bash
shot watch
```

タスクトレイにアイコンが表示され、以下のホットキーがいつでも使えます:

| ホットキー | 動作 |
|---|---|
| `Ctrl+Shift+S` | 画面上でドラッグして範囲を選択してキャプチャ |
| `Ctrl+Shift+F` | 全画面をキャプチャ |
| `Ctrl+Shift+R` | 前回と同じ範囲を再キャプチャ |

タスクトレイのアイコンを右クリック → **終了** で停止。

---

### 単発コマンドモード

#### インタラクティブ（ドラッグで範囲を選択）

```bash
shot
```

1. 画面が暗くなり選択モードに入る
2. マウスをドラッグして範囲を選ぶ（右下にサイズをリアルタイム表示）
3. マウスを離すとクリップボードにコピー完了
4. `ESC` でキャンセル

#### 座標指定

```bash
shot --region X1 Y1 X2 Y2
# 例: 左上 (100, 200) から右下 (900, 700)
shot --region 100 200 900 700
```

#### ファイルへの保存（クリップボードコピーと同時）

```bash
shot --output capture.png
shot --region 0 0 1920 1080 --output fullscreen.png
```

### ヘルプ

```bash
shot --help
```

## 動作環境

| OS | クリップボードの仕組み |
|---|---|
| Windows 10/11 | PowerShell (System.Windows.Forms) |
| macOS | osascript |
| Linux (X11) | xclip / xsel |
| Linux (Wayland) | wl-copy |
