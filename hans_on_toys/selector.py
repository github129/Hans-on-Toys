"""Interactive screen-region selector UI"""
import tkinter as tk
from typing import Optional, Tuple

from PIL import Image, ImageEnhance, ImageTk


class RegionSelector:
    """
    Full-screen overlay that lets the user drag to select a region.

    Usage:
      - In watch mode (persistent daemon): pass the existing hidden Tk root.
        A Toplevel window is used and wait_window() blocks until closed.
      - In single-shot mode: omit root; a temporary Tk root is created and
        mainloop() is used (identical to the previous behaviour).
    """

    def __init__(self, background: Image.Image) -> None:
        self._bg = background
        self._region: Optional[Tuple[int, int, int, int]] = None

    def select(
        self,
        root: Optional[tk.Tk] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Show the selection overlay and return (x1, y1, x2, y2), or None if
        cancelled.

        Parameters
        ----------
        root:
            Existing Tk root to use as parent.  When provided a Toplevel
            window is created; the root itself is never destroyed, so the
            Tcl interpreter stays alive between calls.  Pass None (default)
            to create a self-contained Tk root (single-shot mode).
        """
        own_root = root is None
        if own_root:
            # Single-shot mode: create and own the Tk root
            win: tk.BaseWidget = tk.Tk()
        else:
            # Daemon mode: attach to the existing root via Toplevel
            win = tk.Toplevel(root)

        win.overrideredirect(True)
        w, h = self._bg.width, self._bg.height
        win.geometry(f"{w}x{h}+0+0")
        win.attributes("-topmost", True)

        # Dim the background to signal "selection mode"
        dimmed = ImageEnhance.Brightness(self._bg).enhance(0.5)
        photo = ImageTk.PhotoImage(dimmed)

        canvas = tk.Canvas(win, cursor="cross", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=photo, anchor="nw")

        canvas.create_text(
            w // 2,
            40,
            text="Drag to select  |  ESC to cancel",
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
                start["x"], start["y"], e.x, e.y,
                outline="#FF4444", width=2,
            )

            sw = abs(e.x - start["x"])
            sh = abs(e.y - start["y"])
            lx = max(e.x, start["x"]) + 5
            ly = max(e.y, start["y"]) + 5
            size_label_id[0] = canvas.create_text(
                lx, ly,
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
            win.destroy()

        def on_escape(_: tk.Event) -> None:
            win.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        win.bind("<Escape>", on_escape)

        if own_root:
            # Single-shot: run our own event loop until the window closes
            win.mainloop()
        else:
            # Daemon: block here (processing tk events) until win is destroyed.
            # The persistent root stays alive; only the Toplevel is destroyed.
            root.wait_window(win)

        return self._region
