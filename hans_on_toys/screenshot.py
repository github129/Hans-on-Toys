"""スクリーンショット撮影モジュール"""
from typing import Tuple

import mss
from PIL import Image


def capture_fullscreen() -> Image.Image:
    """プライマリモニターの全画面スクリーンショットを撮影する。"""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # プライマリモニター
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def capture_region(x1: int, y1: int, x2: int, y2: int) -> Image.Image:
    """指定範囲のスクリーンショットを撮影する。"""
    with mss.mss() as sct:
        monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
