"""クリップボードへの画像コピー（プラットフォーム別実装）"""
import os
import platform
import subprocess
import tempfile

from PIL import Image


def copy_to_clipboard(image: Image.Image) -> None:
    """PIL Image をクリップボードにコピーする。"""
    system = platform.system()
    if system == "Windows":
        _copy_windows(image)
    elif system == "Darwin":
        _copy_macos(image)
    elif system == "Linux":
        _copy_linux(image)
    else:
        raise RuntimeError(f"未対応のプラットフォーム: {system}")


def _copy_windows(image: Image.Image) -> None:
    """
    PowerShell の System.Windows.Forms 経由でクリップボードにコピー。
    pywin32 などの追加パッケージ不要。
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        image.save(tmp)
        # 一時ファイルパスのバックスラッシュをエスケープ
        escaped = tmp.replace("\\", "\\\\")
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            f"$img = [System.Drawing.Image]::FromFile('{escaped}'); "
            "[System.Windows.Forms.Clipboard]::SetImage($img); "
            "$img.Dispose()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            capture_output=True,
        )
    finally:
        os.unlink(tmp)


def _copy_macos(image: Image.Image) -> None:
    """osascript 経由で macOS クリップボードにコピー。"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        image.save(tmp)
        script = f'set the clipboard to (read (POSIX file "{tmp}") as «class PNGf»)'
        subprocess.run(["osascript", "-e", script], check=True)
    finally:
        os.unlink(tmp)


def _copy_linux(image: Image.Image) -> None:
    """xclip / xsel / wl-copy 経由で Linux クリップボードにコピー。"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        image.save(tmp)
        # 利用可能なツールを順番に試す
        for cmd in [
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", tmp],
            ["xsel", "--clipboard", "--input", tmp],
        ]:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        # Wayland 環境向け (wl-copy)
        try:
            with open(tmp, "rb") as fp:
                subprocess.run(
                    ["wl-copy", "--type", "image/png"],
                    stdin=fp,
                    check=True,
                    capture_output=True,
                )
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        raise RuntimeError(
            "Linux でのクリップボードコピーには xclip, xsel, または wl-copy が必要です。\n"
            "  X11 環境: sudo apt-get install xclip\n"
            "  Wayland 環境: sudo apt-get install wl-clipboard"
        )
    finally:
        os.unlink(tmp)
