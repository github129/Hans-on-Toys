"""インタラクティブな画面範囲選択UI"""
import tkinter as tk
from typing import Optional, Tuple

from PIL import Image, ImageEnhance, ImageTk


class RegionSelector:
    """
    現在の画面を背景に表示し、ドラッグで範囲を選択するオーバーレイUI。

    手順:
    1. 画面全体のスクリーンショットを背景として表示（50% 暗くして選択モードを表現）
    2. マウスでドラッグして矩形を描く
    3. リリース時に選択範囲の座標を返す
    4. ESC でキャンセル
    """

    def __init__(self, background: Image.Image) -> None:
        self._bg = background
        self._region: Optional[Tuple[int, int, int, int]] = None

    def select(self) -> Optional[Tuple[int, int, int, int]]:
        """
        選択UIを表示し、ユーザーが選択した (x1, y1, x2, y2) を返す。
        キャンセルされた場合は None を返す。
        """
        root = tk.Tk()
        root.overrideredirect(True)
        w, h = self._bg.width, self._bg.height
        root.geometry(f"{w}x{h}+0+0")
        root.attributes("-topmost", True)

        # 暗くして「選択モード」であることを示す
        dimmed = ImageEnhance.Brightness(self._bg).enhance(0.5)
        photo = ImageTk.PhotoImage(dimmed)

        canvas = tk.Canvas(root, cursor="cross", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=photo, anchor="nw")

        # ガイドテキスト
        canvas.create_text(
            w // 2,
            40,
            text="ドラッグして範囲を選択  |  ESC でキャンセル",
            fill="white",
            font=("Arial", 16, "bold"),
        )

        start = {"x": 0, "y": 0}
        rect_id: list = [None]
        size_label_id: list = [None]

        def on_press(e: tk.Event) -> None:
            start["x"], start["y"] = e.x, e.y
            if rect_id[0]:
                canvas.delete(rect_id[0])
            if size_label_id[0]:
                canvas.delete(size_label_id[0])

        def on_drag(e: tk.Event) -> None:
            if rect_id[0]:
                canvas.delete(rect_id[0])
            if size_label_id[0]:
                canvas.delete(size_label_id[0])

            rect_id[0] = canvas.create_rectangle(
                start["x"],
                start["y"],
                e.x,
                e.y,
                outline="#FF4444",
                width=2,
            )

            # 選択サイズをリアルタイム表示
            sw = abs(e.x - start["x"])
            sh = abs(e.y - start["y"])
            lx = max(e.x, start["x"]) + 5
            ly = max(e.y, start["y"]) + 5
            size_label_id[0] = canvas.create_text(
                lx,
                ly,
                text=f"{sw} x {sh}",
                fill="yellow",
                font=("Arial", 11, "bold"),
                anchor="nw",
            )

        def on_release(e: tk.Event) -> None:
            x1 = min(start["x"], e.x)
            y1 = min(start["y"], e.y)
            x2 = max(start["x"], e.x)
            y2 = max(start["y"], e.y)
            if x2 > x1 and y2 > y1:
                self._region = (x1, y1, x2, y2)
            root.destroy()

        def on_escape(_: tk.Event) -> None:
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Escape>", on_escape)

        root.mainloop()
        return self._region
