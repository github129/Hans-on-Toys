"""ホットキー常駐モード（タスクトレイ）"""
import queue
import threading

import keyboard
import pystray
from PIL import Image, ImageDraw

from hans_on_toys.clipboard import copy_to_clipboard
from hans_on_toys.screenshot import capture_fullscreen, capture_region
from hans_on_toys.selector import RegionSelector

# ホットキー定義: {キーの組み合わせ: アクション名}
HOTKEYS = {
    "ctrl+shift+s": "interactive",  # 範囲を選択してキャプチャ
    "ctrl+shift+f": "fullscreen",   # 全画面キャプチャ
    "ctrl+shift+r": "repeat",       # 前回の範囲を再キャプチャ
}


def _make_icon() -> Image.Image:
    """タスクトレイ用のカメラアイコンを生成する。"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 背景（青い円）
    draw.ellipse([0, 0, size - 1, size - 1], fill="#1565C0")
    # カメラ本体
    draw.rectangle([8, 22, 56, 50], fill="white")
    # レンズ外枠
    draw.ellipse([20, 26, 44, 46], fill="#BBDEFB", outline="#1565C0", width=2)
    # レンズ中心
    draw.ellipse([27, 32, 37, 40], fill="#1565C0")
    # ファインダー（上の出っ張り）
    draw.rectangle([24, 14, 40, 24], fill="white")

    return img


class Watcher:
    """
    タスクトレイに常駐し、グローバルホットキーでスクリーンショットを撮影するウォッチャー。

    - Ctrl+Shift+S : ドラッグで範囲を選択してキャプチャ
    - Ctrl+Shift+F : 全画面をキャプチャ
    - Ctrl+Shift+R : 前回と同じ範囲を再キャプチャ
    """

    def __init__(self) -> None:
        self._last_region = None
        self._icon: pystray.Icon | None = None
        self._running = True
        self._action_queue: queue.Queue[str] = queue.Queue()

    # ──────────────────────────────────────────────
    # キャプチャ処理（tkinter を使うためメインスレッドで実行）
    # ──────────────────────────────────────────────

    def _do_capture_interactive(self) -> None:
        try:
            background = capture_fullscreen()
            region = RegionSelector(background).select()
            if region is None:
                return
            x1, y1, x2, y2 = region
            image = background.crop((x1, y1, x2, y2))
            copy_to_clipboard(image)
            self._last_region = region
            self._notify(f"コピーしました  {x2 - x1} × {y2 - y1} px")
        except Exception as exc:
            print(f"[エラー] {exc}")

    def _do_capture_fullscreen(self) -> None:
        try:
            image = capture_fullscreen()
            copy_to_clipboard(image)
            self._notify(f"全画面をコピーしました  {image.width} × {image.height} px")
        except Exception as exc:
            print(f"[エラー] {exc}")

    def _do_capture_repeat(self) -> None:
        if self._last_region is None:
            self._notify(
                "前回の範囲がありません。先に Ctrl+Shift+S で範囲を選択してください。"
            )
            return
        try:
            x1, y1, x2, y2 = self._last_region
            image = capture_region(x1, y1, x2, y2)
            copy_to_clipboard(image)
            self._notify(f"前回の範囲をコピーしました  {x2 - x1} × {y2 - y1} px")
        except Exception as exc:
            print(f"[エラー] {exc}")

    # ──────────────────────────────────────────────
    # ユーティリティ
    # ──────────────────────────────────────────────

    def _notify(self, message: str) -> None:
        """コンソールとトレイ通知に結果を表示する。"""
        print(message)
        if self._icon:
            try:
                self._icon.notify(message, "Hans-on-Toys")
            except Exception:
                pass  # 通知非対応環境では無視

    def _enqueue(self, action: str) -> None:
        """メインスレッドの処理キューにアクションを追加する（スレッドセーフ）。"""
        self._action_queue.put(action)

    def _quit(self, icon=None, item=None) -> None:
        self._running = False
        self._action_queue.put("quit")
        if self._icon:
            self._icon.stop()

    # ──────────────────────────────────────────────
    # タスクトレイ
    # ──────────────────────────────────────────────

    def _run_tray(self) -> None:
        """タスクトレイアイコンとメニューを起動する（別スレッドで実行）。"""
        menu = pystray.Menu(
            pystray.MenuItem(
                "範囲を選択してキャプチャ  (Ctrl+Shift+S)",
                lambda: self._enqueue("interactive"),
            ),
            pystray.MenuItem(
                "全画面キャプチャ  (Ctrl+Shift+F)",
                lambda: self._enqueue("fullscreen"),
            ),
            pystray.MenuItem(
                "前回の範囲を再キャプチャ  (Ctrl+Shift+R)",
                lambda: self._enqueue("repeat"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self._quit),
        )
        self._icon = pystray.Icon("hans-on-toys", _make_icon(), "Hans-on-Toys", menu)
        self._icon.run()

    # ──────────────────────────────────────────────
    # メインエントリ
    # ──────────────────────────────────────────────

    def run(self) -> None:
        # グローバルホットキーを登録
        for hotkey, action in HOTKEYS.items():
            keyboard.add_hotkey(hotkey, lambda a=action: self._enqueue(a))

        # タスクトレイをバックグラウンドスレッドで起動
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

        print("Hans-on-Toys が起動しました")
        print("  Ctrl+Shift+S  範囲を選択してキャプチャ")
        print("  Ctrl+Shift+F  全画面キャプチャ")
        print("  Ctrl+Shift+R  前回の範囲を再キャプチャ")
        print("終了: タスクトレイのアイコンを右クリック → 終了")

        # メインループ
        # tkinter を使う処理はすべてここ（メインスレッド）で実行する
        _dispatch = {
            "interactive": self._do_capture_interactive,
            "fullscreen": self._do_capture_fullscreen,
            "repeat": self._do_capture_repeat,
        }
        while self._running:
            try:
                action = self._action_queue.get(timeout=0.1)
                if action == "quit":
                    break
                handler = _dispatch.get(action)
                if handler:
                    handler()
            except queue.Empty:
                continue

        keyboard.unhook_all()
        print("終了しました。")
