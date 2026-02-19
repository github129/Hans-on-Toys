"""hotkey daemon (system tray)"""
import queue
import threading
import tkinter as tk

import keyboard
import pystray
from PIL import Image, ImageDraw

from hans_on_toys.clipboard import copy_to_clipboard
from hans_on_toys.screenshot import capture_fullscreen, capture_region
from hans_on_toys.selector import RegionSelector

# Hotkey definitions: {key combo: action name}
# Ctrl+Alt+* avoids conflicts with browser shortcuts (Ctrl+Shift+*)
HOTKEYS = {
    "ctrl+alt+s": "interactive",  # drag-select region
    "ctrl+alt+f": "fullscreen",   # full screen
    "ctrl+alt+r": "repeat",       # repeat last region
}


def _make_icon() -> Image.Image:
    """Generate a camera icon for the system tray."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([0, 0, size - 1, size - 1], fill="#1565C0")
    draw.rectangle([8, 22, 56, 50], fill="white")
    draw.ellipse([20, 26, 44, 46], fill="#BBDEFB", outline="#1565C0", width=2)
    draw.ellipse([27, 32, 37, 40], fill="#1565C0")
    draw.rectangle([24, 14, 40, 24], fill="white")

    return img


class Watcher:
    """
    System-tray daemon with global hotkeys for screen capture.

    - Ctrl+Alt+S : drag to select region, then capture
    - Ctrl+Alt+F : capture full screen
    - Ctrl+Alt+R : re-capture previous region
    """

    def __init__(self) -> None:
        self._last_region = None
        self._icon: pystray.Icon | None = None
        self._running = True
        self._action_queue: queue.Queue[str] = queue.Queue()
        self._tk_root: tk.Tk | None = None   # persistent hidden root

    # ──────────────────────────────────────────────
    # Capture handlers (run on main thread)
    # ──────────────────────────────────────────────

    def _do_capture_interactive(self) -> None:
        try:
            background = capture_fullscreen()
            # Pass the persistent root so selector uses Toplevel (not a new Tk)
            region = RegionSelector(background).select(self._tk_root)
            if region is None:
                return
            x1, y1, x2, y2 = region
            image = background.crop((x1, y1, x2, y2))
            copy_to_clipboard(image)
            self._last_region = region
            self._notify(f"Copied  {x2 - x1} x {y2 - y1} px")
        except Exception as exc:
            print(f"[error] {exc}")

    def _do_capture_fullscreen(self) -> None:
        try:
            image = capture_fullscreen()
            copy_to_clipboard(image)
            self._notify(f"Full screen copied  {image.width} x {image.height} px")
        except Exception as exc:
            print(f"[error] {exc}")

    def _do_capture_repeat(self) -> None:
        if self._last_region is None:
            self._notify("No previous region. Use Ctrl+Alt+S first.")
            return
        try:
            x1, y1, x2, y2 = self._last_region
            image = capture_region(x1, y1, x2, y2)
            copy_to_clipboard(image)
            self._notify(f"Re-captured  {x2 - x1} x {y2 - y1} px")
        except Exception as exc:
            print(f"[error] {exc}")

    # ──────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────

    def _notify(self, message: str) -> None:
        print(message)
        if self._icon:
            try:
                self._icon.notify(message, "Hans-on-Toys")
            except Exception:
                pass

    def _enqueue(self, action: str) -> None:
        """Thread-safe: enqueue an action for the main thread."""
        self._action_queue.put(action)

    def _quit(self, icon=None, item=None) -> None:
        """Called from the tray thread; schedule quit on the main (tk) thread."""
        self._running = False
        if self._icon:
            self._icon.stop()
        if self._tk_root:
            # after(0, ...) is thread-safe and exits mainloop cleanly
            self._tk_root.after(0, self._tk_root.quit)

    # ──────────────────────────────────────────────
    # Action polling (runs inside tkinter event loop)
    # ──────────────────────────────────────────────

    def _poll(self) -> None:
        """
        Non-blocking queue poll scheduled via tkinter's after().
        Keeps the main loop alive without a busy-wait thread.
        """
        dispatch = {
            "interactive": self._do_capture_interactive,
            "fullscreen":  self._do_capture_fullscreen,
            "repeat":      self._do_capture_repeat,
        }
        try:
            action = self._action_queue.get_nowait()
            handler = dispatch.get(action)
            if handler:
                handler()
        except queue.Empty:
            pass

        if self._running:
            self._tk_root.after(100, self._poll)

    # ──────────────────────────────────────────────
    # System tray
    # ──────────────────────────────────────────────

    def _run_tray(self) -> None:
        """Start the tray icon (runs in a daemon thread)."""
        menu = pystray.Menu(
            pystray.MenuItem(
                "Region capture  (Ctrl+Alt+S)",
                lambda: self._enqueue("interactive"),
            ),
            pystray.MenuItem(
                "Full screen  (Ctrl+Alt+F)",
                lambda: self._enqueue("fullscreen"),
            ),
            pystray.MenuItem(
                "Repeat last region  (Ctrl+Alt+R)",
                lambda: self._enqueue("repeat"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
        self._icon = pystray.Icon("hans-on-toys", _make_icon(), "Hans-on-Toys", menu)
        self._icon.run()

    # ──────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────

    def run(self) -> None:
        # Register global hotkeys
        for hotkey, action in HOTKEYS.items():
            keyboard.add_hotkey(hotkey, lambda a=action: self._enqueue(a), suppress=True)

        # Start tray in a daemon thread
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

        print("Hans-on-Toys started")
        print("  Ctrl+Alt+S  Region capture")
        print("  Ctrl+Alt+F  Full-screen capture")
        print("  Ctrl+Alt+R  Repeat last region")
        print("To quit: right-click the tray icon -> Quit")

        # Persistent hidden Tk root — keeps the Tcl interpreter (and Windows
        # message pump) alive for the entire session.  Without this, PyInstaller
        # windowed mode may treat "last window closed" as "app exited" after the
        # first selector overlay is destroyed.
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()   # keep it invisible

        # Kick off the queue poller inside tkinter's event loop
        self._poll()

        # tkinter's mainloop is the app's main loop
        self._tk_root.mainloop()

        keyboard.unhook_all()
        print("Exited.")
